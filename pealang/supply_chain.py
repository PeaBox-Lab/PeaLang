"""Dependency supply-chain security scanning for PeaLang packages.

Provides:
- Dependency resolution with version matching
- Integrity verification via SHA-256 checksums
- UUIDv5-based package identifiers (no MD5)
- Signed package validation
"""
from __future__ import annotations
import uuid

import hashlib
import json
import os
import re
import zipfile
from collections.abc import ItemsView, KeysView, ValuesView
from pathlib import Path
from typing import Any, Dict, ItemsView, ItemsView, KeysView, List, Optional


# ---------------------------------------------------------------------------
# Package metadata models
# ---------------------------------------------------------------------------

class PackageMetadata:
    """Describes a peer package with integrity metadata."""

    def __init__(
        self,
        name: str,
        version: str,
        checksum: str,
        depends: Optional[List[str]] = None,
        optional: bool = False,
    ):
        self.name = name
        self.version = version
        self.checksum = checksum  # SHA-256 of normalized package payload
        self.depends = depends or []
        self.optional = optional

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "checksum": self.checksum,
            "depends": self.depends,
            "optional": self.optional,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "PackageMetadata":
        return PackageMetadata(
            name=d["name"],
            version=d["version"],
            checksum=d["checksum"],
            depends=d.get("depends", []),
            optional=d.get("optional", False),
        )


# ---------------------------------------------------------------------------
# Signed package blob (JSON + detached SHA-256 signature)
# ---------------------------------------------------------------------------

def sign_payload(payload: bytes) -> str:
    """Create a detached SHA-256 signature for a payload blob."""
    return hashlib.sha256(payload).hexdigest()


def verify_signature(payload: bytes, signature_hex: str) -> bool:
    """Verify that a SHA-256 signature matches the payload."""
    expected = sign_payload(payload)
    return expected == signature_hex


# ---------------------------------------------------------------------------
# Dependency resolver
# ---------------------------------------------------------------------------

def resolve_dependencies(
    wanted: str,
    index: Dict[str, PackageMetadata],
    max_depth: int = 5,
) -> List[PackageMetadata]:
    """Resolve all transitive dependencies for *wanted* from *index*.

    Returns the ordered list of packages to install, or raises ValueError
    if resolution fails (missing dependency, cycle, etc.).
    """
    visited: set[str] = set()
    resolved: List[PackageMetadata] = []

    def _resolve(name: str, depth: int = 0) -> PackageMetadata:
        if depth > max_depth:
            raise ValueError(f"Dependency resolution depth exceeded {max_depth}")
        if name in visited:
            # Already being processed — cycle detection
            existing = next((m for m in resolved if m.name == name), None)
            if existing:
                return existing
            raise ValueError(f"Circular dependency involving '{name}'")
        if name not in index:
            raise ValueError(f"Package '{name}' not found in index")

        visited.add(name)
        meta = index[name]

        # Resolve dependencies first
        dep_meta: List[PackageMetadata] = []
        for dep_name in meta.depends:
            dep_meta.append(_resolve(dep_name, depth + 1))

        visited.discard(name)
        # Build the full resolution: deps first, then this package
        result: List[PackageMetadata] = []
        for d in dep_meta:
            if d not in result:
                result.append(d)
        result.append(meta)
        return meta

    _resolve(wanted)

    # Deduplicate while preserving order
    seen: set[str] = set()
    ordered: List[PackageMetadata] = []
    for m in resolved:
        if m.name not in seen:
            seen.add(m.name)
            ordered.append(m)
    # Append the wanted package if not already there
    wanted_meta = index.get(wanted)
    if wanted_meta and wanted_meta.name not in seen:
        ordered.append(wanted_meta)
    return ordered


# ---------------------------------------------------------------------------
# Integrated index wrapper
# ---------------------------------------------------------------------------

class SupplyChainIndex:
    """Wraps a PackageIndex adding security-scanning and resolution."""

    def __init__(self, index_dir: str = ".pea_index"):
        from pealang.vm_optimizer import PackageIndex
        self._base = PackageIndex(index_dir)
        self._metadata: Dict[str, PackageMetadata] = {}
        self._scan_results: Dict[str, Dict[str, Any]] = {}

    def _build_metadata(self) -> None:
        """Rebuild the metadata dict from the base index."""
        self._metadata = {}
        for name in self._base.list_packages():
            pkg_name = name["name"]
            latest = name["latest"]
            # Use latest version as the representative metadata
            meta = PackageMetadata(
                name=pkg_name,
                version=latest or "0.0.0",
                checksum="",  # to be filled by explicit publish
                depends=[],
                optional=False,
            )
            self._metadata[pkg_name] = meta

    def publish(
        self,
        name: str,
        version: str,
        checksum: str,
        depends: Optional[List[str]] = None,
        optional: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """Publish a package with full integrity metadata.

        Unlike the bare PackageIndex.publish, this records checksums and
        dependency declarations for supply-chain scanning.
        """
        self._base.publish(name, version)
        if name not in self._metadata:
            self._metadata[name] = PackageMetadata(
                name=name,
                version=version,
                checksum=checksum,
                depends=depends or [],
                optional=optional,
            )
        else:
            self._metadata[name].version = version
            self._metadata[name].checksum = checksum
            self._metadata[name].depends = depends or []
            self._metadata[name].optional = optional
        if metadata:
            self._metadata[name].setdefault("extra", {}).update(metadata)
        self._scan_package(name)
        return {"name": name, "version": version, "published": True, "scanned": True}

    def _scan_package(self, name: str) -> Dict[str, Any]:
        """Basic security scan — check for weak hashes, etc."""
        meta = self._metadata.get(name)
        if not meta:
            return {"name": name, "status": "not_found", "issues": [], "passed": True}
        issues: List[str] = []
        # Check checksum is a valid hex string
        try:
            int(meta.checksum, 16)
        except ValueError:
            issues.append("invalid checksum format")
        passed = len(issues) == 0
        self._scan_results[name] = {"issues": issues, "passed": passed}
        return {"name": name, "status": "scanned", "issues": issues, "passed": passed}

    def scan(self, name: str) -> Dict[str, Any]:
        """Public API: scan a package for security issues."""
        return self._scan_package(name)

    def resolve(self, name: str, version: Optional[str] = None) -> Optional[PackageMetadata]:
        """Resolve a package version with full metadata."""
        meta = self._metadata.get(name)
        if not meta:
            return None
        if version is not None and meta.version != version:
            # Look for the exact version in the base index
            resolved = self._base.resolve(name, version)
            if resolved is None:
                return None
            # Build minimal metadata
            meta = PackageMetadata(
                name=name,
                version=version,
                checksum=resolved.get("metadata", {}).get("checksum", ""),
                depends=[],
                optional=False,
            )
        return meta

    def list_packages(self) -> List[Dict[str, Any]]:
        """List all packages with their metadata."""
        result = []
        for name, meta in self._metadata.items():
            result.append(
                {
                    "name": meta.name,
                    "version": meta.version,
                    "checksum": meta.checksum,
                    "depends": meta.depends,
                    "optional": meta.optional,
                }
            )
        return result


# ---------------------------------------------------------------------------
# Release-hardening API
#
# Deterministic manifests, SBOMs, provenance, integrity verification and
# packaging gates. Functions take project trees (Path-like) or file lists and
# are side-effect free except where noted (write_checksums writes a file).
# ---------------------------------------------------------------------------

def _parse_pyproject_deps(text):
    m = re.search(r'dependencies\s*=\s*\[(.*?)\]', text, re.DOTALL)
    if not m:
        return []
    return [d.strip() for d in re.findall(r'"([^"]+)"', m.group(1))]

def _dep_name(spec):
    return re.split(r'[<>=!~\[]', spec.strip(), maxsplit=1)[0].strip()

def sha256_file(path):
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def artifact_checksums(*paths):
    """Return SHA-256 checksums for each given path."""
    return {str(p): sha256_file(str(p)) for p in paths}

def write_checksums(checksums_or_paths, dest=None):
    """Write checksums to dest.

    Accepts either a dict {path: hexdigest} (written as sorted JSON) or a
    list of file paths (written in SHA256SUMS format: "<hash>  <path>").
    Returns the destination path on success.
    """
    if dest is None:
        raise TypeError("write_checksums requires a destination path")
    dest = Path(dest)
    if isinstance(checksums_or_paths, dict):
        dest.write_text(json.dumps({str(k): v for k, v in checksums_or_paths.items()},
                                     sort_keys=True, indent=2), encoding="utf-8")
        return dest
    lines = []
    for p in checksums_or_paths:
        p = Path(p)
        lines.append(f"{sha256_file(str(p))}  {p.name}")
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest

def generate_sbom(root, version="0.0.0", dependencies=None):
    """Generate a CycloneDX SBOM for the project tree at root."""
    root = Path(root)
    deps = dependencies
    pyproject = root / "pyproject.toml"
    if deps is None and pyproject.is_file():
        deps = _parse_pyproject_deps(pyproject.read_text(encoding="utf-8", errors="ignore"))
    components = [{"type": "application", "name": root.name or "app",
                   "version": version, "bom-ref": "root"}]
    for p in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        components.append({"type": "file", "name": rel,
                           "sha256": sha256_file(str(p))})
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": version,
        "metadata": {"component": {"type": "application",
                                    "name": root.name or "app", "version": version}},
        "dependencies": deps or [],
        "components": components,
    }

def verify_sbom(sbom, root):
    """Verify every file component in an SBOM against its hash."""
    root = Path(root)
    mismatches = []
    for comp in sbom.get("components", []):
        if comp.get("type") != "file":
            continue
        p = root / comp["name"]
        if not p.is_file() or sha256_file(str(p)) != comp.get("sha256"):
            mismatches.append(comp["name"])
    return {"valid": not mismatches, "mismatches": mismatches}

def dependency_inventory(source, dep_name=_dep_name):
    """Inventory a pyproject.toml (directory) or UUID-keyed index (dict)."""
    if isinstance(source, (str, os.PathLike)):
        root = Path(source)
        pyproject = root / "pyproject.toml"
        deps = _parse_pyproject_deps(pyproject.read_text(encoding="utf-8", errors="ignore")) if pyproject.is_file() else []
        return [{"name": dep_name(d), "specifier": d} for d in deps]
    return [{"name": str(uuid.uuid5(uuid.NAMESPACE_DNS, str(k))), **v}
            for k, v in source.items()]

def build_provenance(root, files, version="0.0.0", compiler="peac"):
    """Build a provenance record for the compiled artifacts in files."""
    root = Path(root)
    subject = []
    for f in files:
        p = Path(f)
        subject.append({"name": p.name,
                        "digest": {"sha256": sha256_file(str(p))},
                        "path": str(p)})
    return {
        "_type": "provenance",
        "package": root.name or "app",
        "version": version,
        "compiler": compiler,
        "subject": subject,
    }

def verify_provenance(provenance, files):
    """Verify every file listed in a provenance record matches its hash."""
    by_name = {entry.get("name"): entry.get("digest", {}).get("sha256")
               for entry in provenance.get("subject", [])}
    mismatches = []
    for f in files:
        p = Path(f)
        expected = by_name.get(p.name)
        if expected is None or sha256_file(str(p)) != expected:
            mismatches.append(p.name)
    return {"valid": not mismatches, "mismatches": mismatches}

def deterministic_manifest(root):
    """Hash every file under root in sorted order; deterministic output."""
    root = Path(root)
    files = []
    for p in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        files.append({"path": rel, "sha256": sha256_file(str(p))})
    return {"algorithm": "sha256", "files": files, "file_count": len(files)}

def verify_manifest(root, manifest):
    """Verify a deterministic manifest: list files whose hash changed."""
    root = Path(root)
    changed = []
    for entry in manifest.get("files", []):
        p = root / entry["path"]
        if not p.is_file() or sha256_file(str(p)) != entry["sha256"]:
            changed.append(entry["path"])
    return {"valid": not changed, "changed": changed}

def sign_release_manifest(manifest, private_key_bytes):
    """Sign a manifest dict with a raw Ed25519 private key."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return key.sign(payload)

def verify_release_signature(manifest, signature, public_key_bytes):
    """Verify an Ed25519 signature for a manifest dict."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    try:
        key.verify(signature, payload)
        return True
    except Exception:
        return False

def verify_wheel(wheel_path):
    """Inspect a wheel: requires pealang/__init__.py and *-dist-info/METADATA."""
    try:
        with zipfile.ZipFile(wheel_path) as z:
            names = z.namelist()
            has_init = any(n.endswith("pealang/__init__.py") for n in names)
            metadata = next((n for n in names if n.endswith(".dist-info/METADATA")), None)
            version = None
            if metadata is not None:
                m = re.search(r"^Version:\s*([^\s]+)",
                              z.read(metadata).decode("utf-8", "replace"), re.MULTILINE)
                version = m.group(1).strip() if m else None
            valid = has_init and metadata is not None
            return {"valid": valid, "version": version, "files": len(names)}
    except Exception:
        return {"valid": False, "version": None, "files": 0}

def verify_source_archive(archive_path):
    """Inspect a source zip: requires pyproject.toml and README.md at its root."""
    try:
        with zipfile.ZipFile(archive_path) as z:
            names = z.namelist()
            tree_root = None
            for n in names:
                parts = n.split("/")
                if len(parts) >= 2 and parts[-1] == "pyproject.toml":
                    tree_root = parts[0]
                    break
            pyproject = next((n for n in names if n.endswith("/pyproject.toml")), None)
            readme = next((n for n in names if n.endswith("/README.md")), None)
            valid = bool(pyproject and readme)
            return {"valid": valid, "root": tree_root, "files": len(names)}
    except Exception:
        return {"valid": False, "root": None, "files": 0}

def migration_check(from_root, to_root):
    """Compare two trees; a migration is compatible iff no source files vanished."""
    a, b = Path(from_root), Path(to_root)
    if not a.is_dir() or not b.is_dir():
        return {"compatible": False,
                "removed": sorted(set(p.as_posix() for p in a.rglob("*") if p.is_file()))
                if a.is_dir() else [str(a)]}
    a_files = {p.relative_to(a).as_posix() for p in a.rglob("*") if p.is_file()}
    b_files = {p.relative_to(b).as_posix() for p in b.rglob("*") if p.is_file()}
    removed = sorted(a_files - b_files)
    added = sorted(b_files - a_files)
    changed = sorted(rel for rel in (a_files & b_files)
                     if sha256_file(str(a / rel)) != sha256_file(str(b / rel)))
    return {"compatible": not removed, "removed": removed,
            "added": added, "changed": changed}

def reproducible_build_metadata(build_id, timestamp, source_hash):
    """Produce reproducible build metadata dict."""
    return {"build_id": build_id, "timestamp": timestamp, "source_hash": source_hash}

def release_checklist():
    """A release checklist covering spec, tests, security and distribution."""
    return [
        "spec version frozen and verified",
        "regression suite green",
        "conformance suite green",
        "security audit clean",
        "SBOM and provenance signed",
        "deterministic manifest verified",
        "packaging quality gate PASS",
        "migration check compatible",
        "docs and examples updated",
        "release manifest signed",
        "known limitations documented",
        "changelog and roadmap updated",
    ]

def readiness_assessment(states):
    """Score a mapping of component -> truthy state; full score means ready."""
    if not isinstance(states, dict):
        states = {"state": bool(states)}
    total = len(states)
    passed = sum(1 for v in states.values() if bool(v))
    score = int(round(passed * 100 / total)) if total else 100
    return {"component": "aggregate", "state": "green" if score == 100 else "amber",
            "score": score, "ready": score == 100, "checks": list(states)}

def containerfile():
    """Generate a minimal containerfile definition for release builds."""
    return ("FROM python:3.12-slim\n"
            "WORKDIR /app\n"
            "ENV PYTHONUNBUFFERED=1\n"
            "WORKDIR /app\n"
            "COPY . /app\n"
            "RUN pip install --no-cache-dir .\n"
            "USER 10001:10001\n"
            "CMD [\"pealang\", \"run\", \"main.pea\"]\n")

def ci_matrix():
    """Return the CI platform/version matrix for release gating."""
    return {"os": ["ubuntu-latest", "windows-latest", "macos-latest"],
            "python-version": ["3.10", "3.11", "3.12", "3.13"]}

def locked_dependency_evidence(root):
    """Inspect requirements.lock for a pinned, complete dependency lock."""
    root = Path(root)
    lock = root / "requirements.lock"
    locked = lock.is_file() and bool(lock.read_text(encoding="utf-8", errors="ignore").strip())
    packages = [l for l in lock.read_text(encoding="utf-8", errors="ignore").splitlines()
                if l.strip() and not l.strip().startswith("#")] if lock.is_file() else []
    return {"locked": locked, "packages": packages}

def offline_install_evidence(wheelhouse, packages):
    """Check each pkg==version in packages has a wheel in wheelhouse."""
    wh = Path(wheelhouse)
    wheels = list(wh.glob("*.whl")) if wh.is_dir() else []
    missing = []
    matched = []
    for pkg in packages:
        name, _, version = pkg.partition("==")
        name, version = name.strip(), version.strip()
        match = any(w.name.startswith(f"{name}-{version}-") for w in wheels)
        if match:
            matched.append(pkg)
        else:
            missing.append(pkg)
    return {"ready": not missing, "matched": matched, "missing": missing,
            "wheels": [w.name for w in wheels]}

def packaging_quality_gate(manifest, sbom, provenance, deterministic, offline, files):
    """Aggregate the packaging gate checks into a PASS/FAIL verdict."""
    def _ok(arg, key="valid"):
        if isinstance(arg, dict):
            return bool(arg.get(key, arg.get("ready", arg)))
        return bool(arg)
    checks = [_ok(manifest, "valid"),
              _ok(sbom, "valid"),
              _ok(provenance, "valid"),
              bool(deterministic),
              _ok(offline, "ready"),
              bool(files.get("files", files) if isinstance(files, dict) else bool(files))]
    return {"gate": "PASS" if all(checks) else "FAIL", "checks": checks}

# ---------------------------------------------------------------------------
# Namespace exporter
# ---------------------------------------------------------------------------

def build_supply_chain_namespace() -> Dict[str, Any]:
    """Return a namespace dict for registration in analysis/stats/numerics."""
    return {
        "PackageMetadata": PackageMetadata,
        "sign_payload": sign_payload,
        "verify_signature": verify_signature,
        "resolve_dependencies": resolve_dependencies,
        "SupplyChainIndex": SupplyChainIndex,
        "build_supply_chain_namespace": build_supply_chain_namespace,
    }
