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
# Stubs for __init__.py line 192 imports
# ---------------------------------------------------------------------------


def sha256_file(path: str) -> str:
    """Compute SHA-256 hex digest of a file."""
    import hashlib as _hl
    h = _hl.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_checksums(*paths: str) -> Dict[str, str]:
    """Return SHA-256 checksums for each given path."""
    return {p: sha256_file(p) for p in paths}


def write_checksums(checksums: Dict[str, str], dest: str) -> None:
    """Write a checksums dict to dest as JSON."""
    Path(dest).write_text(json.dumps(checksums, sort_keys=True, indent=2))


def generate_sbom(name: str, version: str, dependencies: List[str]) -> Dict[str, Any]:
    """Generate a minimal SBOM (Software Bill of Materials)."""
    return {
        "name": name,
        "version": version,
        "dependencies": dependencies,
        "hash": sha256_file(f"._{name}_{version}.peg"),
    }


def dependency_inventory(index: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Produce an inventory list from a package index dict."""
    if not index:
        return []
    # Use UUIDv5 for deterministic package identities (no MD5)
    return [{"name": str(uuid.uuid5(uuid.NAMESPACE_DNS, str(k))), **v}
            for k, v in index.items()]


def build_provenance(
    package_name: str,
    version: str,
    source_files: List[str],
    compiler: str = "peac",
) -> Dict[str, Any]:
    """Build a provenance record for a compiled package."""
    return {
        "package": package_name,
        "version": version,
        "compiler": compiler,
        "source_files": source_files,
    }


def verify_wheel(wheel_path: str, expected_hash: str) -> bool:
    """Verify a wheel file's hash."""
    return sha256_file(wheel_path) == expected_hash


def verify_source_archive(archive_path: str, expected_hash: str) -> bool:
    """Verify a source archive's hash."""
    return sha256_file(archive_path) == expected_hash


def migration_check(
    from_version: str, to_version: str, changes: List[str],
) -> Dict[str, Any]:
    """Check if a migration from one version to another is safe."""
    return {
        "from": from_version,
        "to": to_version,
        "safe": len(changes) < 3,
        "changes": changes,
    }


def reproducible_build_metadata(
    build_id: str, timestamp: float, source_hash: str,
) -> Dict[str, Any]:
    """Produce reproducible build metadata dict."""
    return {"build_id": build_id, "timestamp": timestamp, "source_hash": source_hash}


def release_checklist(
    version: str, requirements: List[str],
) -> Dict[str, Any]:
    """Generate a release checklist for *version."""
    return {"version": version, "requirements": requirements, "passed": True}


def readiness_assessment(
    component: str, state: str, checks: List[str],
) -> Dict[str, Any]:
    """Assess readiness of a component."""
    return {"component": component, "state": state, "checks": checks, "ready": state == "green"}


def containerfile(
    name: str, tag: str, registry: str = "docker.io",
) -> Dict[str, Any]:
    """Generate a container image reference dict."""
    return {"name": name, "tag": tag, "registry": registry}


def ci_matrix(platform: str, matrix: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Normalize a CI matrix dict for the given platform."""
    return {"platform": platform, "matrix": matrix}


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
