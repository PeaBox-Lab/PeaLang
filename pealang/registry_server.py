"""PeaLang Public Package Registry server (v2.33.0).

A self-hostable package registry for PeaLang libraries (.pelib packages).
Provides package upload, download, listing, and info endpoints with
Ed25519-signed registry indexes and bearer-token publisher authentication.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import tarfile
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .errors import PeaError
from .package_manager import load_pea_toml
from .registry_index import PackageRecord, RegistryIndex, NamespacePolicy, build_index, validate_index, namespace_from_package
from .ed25519_signing import (
    generate_ed25519_keypair,
    sign_ed25519,
    verify_ed25519,
    public_key_bytes,
    public_key_id,
    PublicTrustStore,
)
from .registry_auth import bearer_headers


class RegistryServer:
    """In-memory package registry with signed index persistence."""

    def __init__(self, storage_dir: str, registry_name: str = "pealang",
                 private_key_path: str | None = None,
                 public_key_path: str | None = None,
                 trust_store_path: str | None = None):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.packages_dir = self.storage_dir / "packages"
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.storage_dir / "index.json"
        self.registry_name = registry_name
        self.sequence = 0
        self.packages: list[dict] = []
        self.publisher_tokens: dict[str, str] = {}  # token -> publisher_id
        self.namespace_path = self.storage_dir / "namespaces.json"
        self.namespace_policy = NamespacePolicy()
        self._load_namespaces()

        # Setup signing keys
        if private_key_path and public_key_path:
            self.private_key_path = Path(private_key_path)
            self.public_key_path = Path(public_key_path)
        else:
            self.private_key_path = self.storage_dir / "registry_private.key"
            self.public_key_path = self.storage_dir / "registry_public.key"
            if not self.private_key_path.exists():
                generate_ed25519_keypair(str(self.private_key_path), str(self.public_key_path))

        # Setup trust store
        if trust_store_path:
            self.trust_store = PublicTrustStore(trust_store_path)
        else:
            self.trust_store = PublicTrustStore(self.storage_dir / "trust.json")

        # Trust our own signing key
        pub_raw = public_key_bytes(str(self.public_key_path))
        kid = public_key_id(pub_raw)
        self.trust_store.trust(str(self.public_key_path), label="registry-signing-key")
        self.signing_key_id = kid

        self._load_index()

    def _load_index(self) -> None:
        if self.index_path.exists():
            index = RegistryIndex.load(str(self.index_path))
            self.sequence = index.sequence
            self.packages = index.packages
        else:
            self.sequence = 0
            self.packages = []

    def _save_index(self) -> None:
        index = build_index(self.registry_name, self.sequence, self.packages)
        index.save(str(self.index_path))

    def _load_namespaces(self) -> None:
        if self.namespace_path.exists():
            data = json.loads(self.namespace_path.read_text(encoding="utf-8"))
            self.namespace_policy.bindings = {
                name: set(keys) for name, keys in data.get("namespaces", {}).items()
            }

    def _save_namespaces(self) -> None:
        data = {"namespaces": {name: sorted(keys) for name, keys in self.namespace_policy.bindings.items()}}
        self.namespace_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def authorize_namespace(self, namespace: str, principal: str) -> bool:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", namespace) or ".." in namespace:
            raise PeaError("Invalid namespace")
        self.namespace_policy.authorize(namespace, principal)
        self._save_namespaces()
        return True

    def namespace_list(self) -> dict[str, list[str]]:
        return {name: sorted(keys) for name, keys in self.namespace_policy.bindings.items()}

    def _namespace_for(self, name: str, namespace: str | None, principal: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or ".." in name:
            raise PeaError("Invalid package name")
        resolved = namespace or (namespace_from_package(name) if "." in name else principal)
        if resolved != principal:
            self.namespace_policy.check_namespace(resolved, principal)
        return resolved

    def _auth_token(self, token: str | None) -> str | None:
        """Validate bearer token, return publisher_id or None."""
        if token is None:
            return None
        return self.publisher_tokens.get(token)

    def _require_auth(self, token: str | None) -> None:
        if self._auth_token(token) is None:
            raise PeaError("Authentication required: provide a valid registry token")

    def _package_dir(self, name: str) -> Path:
        return self.packages_dir / name

    def _package_file(self, name: str, version: str) -> Path:
        return self._package_dir(name) / f"{name}-{version}.pelib"

    def _signature_file(self, name: str, version: str) -> Path:
        return self._package_dir(name) / f"{name}-{version}.sig"

    def register_publisher(self, token: str, publisher_id: str) -> None:
        """Register a publisher token for package uploads."""
        self.publisher_tokens[token] = publisher_id

    def _visible(self, package: dict, viewer: str | None) -> bool:
        if package.get("visibility", "public") == "public":
            return True
        if viewer is None:
            return False
        allowed = set(package.get("allowed_principals", []))
        allowed.add(package.get("publisher_id", ""))
        return viewer in allowed

    def list_packages(self, viewer: str | None = None) -> dict[str, Any]:
        """Return packages visible to the given publisher principal."""
        result: dict[str, list[dict]] = {}
        for p in self.packages:
            if not self._visible(p, viewer):
                continue
            result.setdefault(p["name"], []).append({
                "version": p["version"],
                "sha256": p["sha256"],
                "url": p["url"],
                "signature_url": p.get("signature_url", ""),
                "signature_key_id": p.get("signature_key_id", p.get("publisher_key_id", "")),
                "published": p["published"],
                "publisher": p.get("publisher_key_id", ""),
                "namespace": p.get("namespace", ""),
                "visibility": p.get("visibility", "public"),
            })
        return result

    def get_package_info(self, name: str, viewer: str | None = None) -> dict[str, Any] | None:
        versions = [p for p in self.packages if p["name"] == name and self._visible(p, viewer)]
        if not versions:
            return None
        return {
            "name": name,
            "versions": sorted(versions, key=lambda p: p["published"], reverse=True),
        }

    def upload_package(self, name: str, version: str, package_bytes: bytes,
                       publisher_id: str, token: str,
                       signature_envelope: str | None = None,
                       namespace: str | None = None,
                       visibility: str = "public",
                       allowed_principals: list[str] | None = None) -> dict[str, Any]:
        """Upload a .pelib package to the registry."""
        self._require_auth(token)
        if visibility not in ("public", "private"):
            raise PeaError("Visibility must be public or private")
        resolved_namespace = self._namespace_for(name, namespace, publisher_id)
        allowed = set(allowed_principals or [])
        allowed.add(publisher_id)

        pkg_dir = self._package_dir(name)
        pkg_dir.mkdir(parents=True, exist_ok=True)

        pkg_path = self._package_file(name, version)
        if pkg_path.exists():
            raise PeaError(f"Package {name} {version} already exists (immutable)")

        # Verify it's a valid pelib
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td) / "upload.pelib"
            tmp_path.write_bytes(package_bytes)
            from .secure_packages import safe_extract
            safe_extract(str(tmp_path), td)
            manifest_path = Path(td) / "manifest.json"
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text())
                if manifest.get("name") != name:
                    raise PeaError(f"Package name mismatch: manifest={manifest.get('name')}, expected={name}")
                if manifest.get("version") != version:
                    raise PeaError(f"Package version mismatch: manifest={manifest.get('version')}, expected={version}")

        # Save package
        pkg_path.write_bytes(package_bytes)
        sha = hashlib.sha256(package_bytes).hexdigest()

        # Create or accept a detached publisher signature
        sig_path = self._signature_file(name, version)
        if signature_envelope:
            env = json.loads(signature_envelope)
            if env.get("algorithm") != "Ed25519":
                raise PeaError("Unsupported publisher signature algorithm")
            if env.get("package_sha256") != sha:
                raise PeaError("Publisher signature checksum mismatch")
            key_id = env.get("key_id")
            revoked = set(self.trust_store.data.get("revoked", {}))
            trusted = self.trust_store.data.get("keys", {}).get(key_id)
            if not trusted or key_id in revoked:
                raise PeaError(f"Publisher key {key_id} is not trusted by this registry")
            with tempfile.TemporaryDirectory() as sd:
                tmp_sig = Path(sd) / "publisher.sig"
                tmp_pub = Path(sd) / "publisher.pub"
                tmp_sig.write_text(signature_envelope, encoding="utf-8")
                tmp_pub.write_text(trusted["public_key"] + "\n", encoding="utf-8")
                verify_ed25519(str(pkg_path), str(tmp_sig), str(tmp_pub), revoked=revoked)
            sig_path.write_text(signature_envelope, encoding="utf-8")
            signature_key_id = key_id
            publisher_signature = True
        else:
            sig_path, env = sign_ed25519(str(pkg_path), str(self.private_key_path),
                                         output=str(sig_path), publisher=publisher_id)
            signature_key_id = self.signing_key_id
            publisher_signature = False

        # Build package record
        record = {
            "name": name,
            "version": version,
            "sha256": sha,
            "url": f"/api/v1/packages/{name}/{version}/download",
            "signature_url": f"/api/v1/packages/{name}/{version}/signature",
            "publisher_key_id": signature_key_id,
            "signature_key_id": signature_key_id,
            "publisher_signature": publisher_signature,
            "publisher_id": publisher_id,
            "namespace": resolved_namespace,
            "visibility": visibility,
            "allowed_principals": sorted(allowed),
            "published": int(time.time()),
            "expires": None,
        }

        self.packages.append(record)
        self.sequence += 1
        self._save_index()

        return {
            "name": name,
            "version": version,
            "sha256": sha,
            "published": record["published"],
            "signature_key_id": signature_key_id,
            "publisher_signature": publisher_signature,
            "namespace": resolved_namespace,
            "visibility": visibility,
        }

    def _check_download_access(self, name: str, version: str, viewer: str | None) -> None:
        record = next((p for p in self.packages if p["name"] == name and p["version"] == version), None)
        if record and not self._visible(record, viewer):
            raise PeaError(f"Package {name} {version} is private")

    def download_package(self, name: str, version: str, viewer: str | None = None) -> bytes | None:
        """Download a .pelib package."""
        self._check_download_access(name, version, viewer)
        pkg_path = self._package_file(name, version)
        if not pkg_path.exists():
            return None
        return pkg_path.read_bytes()

    def download_signature(self, name: str, version: str, viewer: str | None = None) -> bytes | None:
        """Download package signature."""
        self._check_download_access(name, version, viewer)
        sig_path = self._signature_file(name, version)
        if not sig_path.exists():
            return None
        return sig_path.read_bytes()

    def get_index(self, viewer: str | None = None) -> dict[str, Any]:
        """Return the registry index filtered to packages visible to the viewer."""
        packages = [p for p in self.packages if self._visible(p, viewer)]
        index = RegistryIndex(self.registry_name, self.sequence, int(time.time()), packages)
        return {
            "registry": index.registry,
            "sequence": index.sequence,
            "generated": index.generated,
            "packages": index.packages,
        }

    def verify_index(self) -> bool:
        """Verify the current registry index integrity."""
        index = RegistryIndex(self.registry_name, self.sequence, int(time.time()), self.packages)
        validate_index(index, self.registry_name, None)
        return True


class RegistryHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the registry server."""

    server: RegistryServer

    def send_json(self, status: int, data: dict[str, Any]) -> None:
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _get_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(length)

    def _auth_token(self) -> str | None:
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return None

    def _viewer(self) -> str | None:
        token = self._auth_token()
        return self.server.server._auth_token(token) if token else None

    def do_GET(self) -> None:
        path = self.path

        viewer = self._viewer()

        if path == "/api/v1/packages":
            self.send_json(200, {"packages": self.server.server.list_packages(viewer)})
            return

        if path == "/api/v1/index":
            self.send_json(200, self.server.server.get_index(viewer))
            return

        # /api/v1/packages/<name>
        if path.startswith("/api/v1/packages/") and path.count("/") == 4:
            name = path.split("/")[4]
            info = self.server.server.get_package_info(name, viewer)
            if info is None:
                self.send_json(404, {"error": f"Package {name} not found"})
                return
            self.send_json(200, info)
            return

        # /api/v1/packages/<name>/<version>/download
        if path.startswith("/api/v1/packages/") and path.count("/") == 6:
            parts = path.split("/")
            name, version = parts[4], parts[5]
            try:
                if parts[6] == "download":
                    data = self.server.server.download_package(name, version, viewer)
                    if data is None:
                        self.send_json(404, {"error": f"Package {name} {version} not found"})
                        return
                    self.send_response(200)
                    self.send_header("Content-Type", "application/gzip")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                if parts[6] == "signature":
                    data = self.server.server.download_signature(name, version, viewer)
                    if data is None:
                        self.send_json(404, {"error": f"Signature for {name} {version} not found"})
                        return
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(data)
                    return
            except PeaError as e:
                self.send_json(403, {"error": str(e)})
                return

        self.send_json(404, {"error": "not found"})

    def do_PUT(self) -> None:
        # /api/v1/packages/<name>/<version>
        if self.path.startswith("/api/v1/packages/") and self.path.count("/") == 5:
            parts = self.path.split("/")
            name, version = parts[4], parts[5]

            token = self._auth_token()
            publisher_id = self.server.server._auth_token(token)
            if publisher_id is None:
                self.send_json(401, {"error": "Authentication required"})
                return

            try:
                body = self._get_body()
                signature_envelope = None
                header = self.headers.get("X-PeaLang-Signature")
                if header:
                    signature_envelope = base64.b64decode(header, validate=True).decode("utf-8")
                namespace = self.headers.get("X-PeaLang-Namespace")
                visibility = self.headers.get("X-PeaLang-Visibility", "public")
                allowed_header = self.headers.get("X-PeaLang-Allow", "")
                allowed = [item for item in (part.strip() for part in allowed_header.split(",")) if item]
                result = self.server.server.upload_package(
                    name, version, body, publisher_id, token,
                    signature_envelope=signature_envelope,
                    namespace=namespace,
                    visibility=visibility,
                    allowed_principals=allowed,
                )
                self.send_json(201, {
                    "ok": True,
                    "name": result["name"],
                    "version": result["version"],
                    "sha256": result["sha256"],
                    "published": result["published"],
                    "signature_key_id": result["signature_key_id"],
                    "publisher_signature": result["publisher_signature"],
                    "namespace": result["namespace"],
                    "visibility": result["visibility"],
                })
                return
            except PeaError as e:
                self.send_json(400, {"error": str(e)})
                return
            except Exception as e:
                self.send_json(500, {"error": str(e)})
                return

        self.send_json(404, {"error": "not found"})

    def log_message(self, *args) -> None:
        pass  # Suppress default logging


def serve(host: str = "127.0.0.1", port: int = 8788,
          storage_dir: str = "./registry-storage",
          registry_name: str = "pealang",
          private_key_path: str | None = None,
          public_key_path: str | None = None,
          trust_store_path: str | None = None) -> None:
    """Start the PeaLang package registry server."""
    server = RegistryServer(
        storage_dir=storage_dir,
        registry_name=registry_name,
        private_key_path=private_key_path,
        public_key_path=public_key_path,
        trust_store_path=trust_store_path,
    )
    httpd = ThreadingHTTPServer((host, port), RegistryHandler)
    httpd.server = server  # type: ignore[attr-defined]
    print(f"PeaLang registry server on http://{host}:{port}")
    print(f"Storage: {storage_dir}")
    print(f"Registry: {registry_name}")
    httpd.serve_forever()
