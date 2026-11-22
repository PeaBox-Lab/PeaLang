"""PeaLang Public Package Registry server (v2.33.0).

A self-hostable package registry for PeaLang libraries (.pelib packages).
Provides package upload, download, listing, and info endpoints with
Ed25519-signed registry indexes and bearer-token publisher authentication.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import tarfile
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .errors import PeaError
from .package_manager import load_pea_toml
from .registry_index import PackageRecord, RegistryIndex, build_index, validate_index
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

    def list_packages(self) -> dict[str, Any]:
        """Return all packages with their versions."""
        result: dict[str, list[dict]] = {}
        for p in self.packages:
            result.setdefault(p["name"], []).append({
                "version": p["version"],
                "sha256": p["sha256"],
                "url": p["url"],
                "published": p["published"],
                "publisher": p.get("publisher_key_id", ""),
            })
        return result

    def get_package_info(self, name: str) -> dict[str, Any] | None:
        versions = [p for p in self.packages if p["name"] == name]
        if not versions:
            return None
        return {
            "name": name,
            "versions": sorted(versions, key=lambda p: p["published"], reverse=True),
        }

    def upload_package(self, name: str, version: str, package_bytes: bytes,
                       publisher_id: str, token: str) -> dict[str, Any]:
        """Upload a .pelib package to the registry."""
        self._require_auth(token)

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

        # Create signature
        sig_path = self._signature_file(name, version)
        sig_path, env = sign_ed25519(str(pkg_path), str(self.private_key_path),
                                     output=str(sig_path), publisher=publisher_id)

        # Build package record
        record = {
            "name": name,
            "version": version,
            "sha256": sha,
            "url": f"/api/v1/packages/{name}/{version}/download",
            "signature_url": f"/api/v1/packages/{name}/{version}/signature",
            "publisher_key_id": self.signing_key_id,
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
        }

    def download_package(self, name: str, version: str) -> bytes | None:
        """Download a .pelib package."""
        pkg_path = self._package_file(name, version)
        if not pkg_path.exists():
            return None
        return pkg_path.read_bytes()

    def download_signature(self, name: str, version: str) -> bytes | None:
        """Download package signature."""
        sig_path = self._signature_file(name, version)
        if not sig_path.exists():
            return None
        return sig_path.read_bytes()

    def get_index(self) -> dict[str, Any]:
        """Return the signed registry index."""
        index = RegistryIndex(self.registry_name, self.sequence, int(time.time()), self.packages)
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

    def do_GET(self) -> None:
        path = self.path

        if path == "/api/v1/packages":
            self.send_json(200, {"packages": self.server.list_packages()})
            return

        if path == "/api/v1/index":
            self.send_json(200, self.server.get_index())
            return

        # /api/v1/packages/<name>
        if path.startswith("/api/v1/packages/") and path.count("/") == 4:
            name = path.split("/")[3]
            info = self.server.get_package_info(name)
            if info is None:
                self.send_json(404, {"error": f"Package {name} not found"})
                return
            self.send_json(200, info)
            return

        # /api/v1/packages/<name>/<version>/download
        if path.startswith("/api/v1/packages/") and path.count("/") == 6:
            parts = path.split("/")
            name, version = parts[3], parts[4]
            if parts[5] == "download":
                data = self.server.download_package(name, version)
                if data is None:
                    self.send_json(404, {"error": f"Package {name} {version} not found"})
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/gzip")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if parts[5] == "signature":
                data = self.server.download_signature(name, version)
                if data is None:
                    self.send_json(404, {"error": f"Signature for {name} {version} not found"})
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data)
                return

        self.send_json(404, {"error": "not found"})

    def do_PUT(self) -> None:
        # /api/v1/packages/<name>/<version>
        if self.path.startswith("/api/v1/packages/") and self.path.count("/") == 5:
            parts = self.path.split("/")
            name, version = parts[3], parts[4]

            token = self._auth_token()
            publisher_id = self.server._auth_token(token)
            if publisher_id is None:
                self.send_json(401, {"error": "Authentication required"})
                return

            try:
                body = self._get_body()
                result = self.server.upload_package(name, version, body, publisher_id, token)
                self.send_json(201, {
                    "ok": True,
                    "name": result["name"],
                    "version": result["version"],
                    "sha256": result["sha256"],
                    "published": result["published"],
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
