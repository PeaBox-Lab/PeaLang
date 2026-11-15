"""Package hub and ecosystem support for PeaLang (v2.6.0).

Provides:
- Package metadata and dependency resolution
- Plugin discovery and loading
- Package index management
- Documentation generation stub
- Peer package verification
- Version constraint solving
"""

from __future__ import annotations

import json
import hashlib
import os
import re
import subprocess
import sys
import threading
from collections import defaultdict, OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# ---------------------------------------------------------------------------
# Package Metadata
# ---------------------------------------------------------------------------

class PackageMetadata:
    """Describes a peer package with full metadata."""

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
# Package Index
# ---------------------------------------------------------------------------

class PackageIndex:
    """Manages a local index of available packages."""

    def __init__(self, index_dir: str = ".peapkg_index"):
        self.index_dir = index_dir
        self._packages: Dict[str, PackageMetadata] = {}
        self._lock = threading.Lock()
        Path(index_dir).mkdir(parents=True, exist_ok=True)
        self._load_index()

    def _load_index(self) -> None:
        """Load existing index from disk."""
        index_file = Path(self.index_dir) / "index.json"
        if index_file.exists():
            try:
                with open(index_file, "r") as f:
                    data = json.load(f)
                for name, meta in data.items():
                    self._packages[name] = PackageMetadata.from_dict(meta)
            except Exception:
                pass

    def _save_index(self) -> None:
        """Persist index to disk."""
        index_file = Path(self.index_dir) / "index.json"
        data = {name: meta.to_dict() for name, meta in self._packages.items()}
        index_file.write_text(json.dumps(data, indent=2, sort_keys=True))

    def publish(
        self,
        name: str,
        version: str,
        checksum: str,
        depends: Optional[List[str]] = None,
        optional: bool = False,
    ) -> PackageMetadata:
        """Publish a package to the index."""
        with self._lock:
            meta = PackageMetadata(name=name, version=version, checksum=checksum,
                                   depends=depends, optional=optional)
            self._packages[name] = meta
            self._save_index()
        return meta

    def get(self, name: str) -> Optional[PackageMetadata]:
        """Get package metadata by name."""
        with self._lock:
            return self._packages.get(name)

    def list_packages(self) -> List[PackageMetadata]:
        """List all packages in the index."""
        with self._lock:
            return list(self._packages.values())

    def remove(self, name: str) -> bool:
        """Remove a package from the index."""
        with self._lock:
            if name in self._packages:
                del self._packages[name]
                self._save_index()
                return True
            return False


# ---------------------------------------------------------------------------
# Plugin System
# ---------------------------------------------------------------------------

class PluginInfo:
    """Information about a discovered plugin."""

    def __init__(
        self,
        name: str,
        version: str,
        entry_point: str,
        description: str = "",
        capabilities: Optional[List[str]] = None,
    ):
        self.name = name
        self.version = version
        self.entry_point = entry_point  # e.g. "peaplugins.myplugin:main"
        self.description = description
        self.capabilities = capabilities or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "entry_point": self.entry_point,
            "description": self.description,
            "capabilities": self.capabilities,
        }


class PluginManager:
    """Manage discovery and loading of PeaLang plugins."""

    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        self._plugins: Dict[str, PluginInfo] = {}
        self._plugin_dirs = plugin_dirs or [".plugins", "peaplugins"]
        self._loaded: Dict[str, Any] = {}
        self._discover()

    def _discover(self) -> None:
        """Scan plugin directories for discovered plugins."""
        for d in self._plugin_dirs:
            plugin_dir = Path(d)
            if not plugin_dir.exists():
                continue
            for py_file in plugin_dir.rglob("*.py"):
                rel_path = py_file.relative_to(plugin_dir)
                # Simple heuristic: look for a module with a 'main' or 'create' function
                module_name = str(py_file.with_suffix(""))
                try:
                    # Import the module dynamically
                    spec = __import__(module_name, fromlist=[""])
                    # Check for common plugin signatures
                    if hasattr(spec, "main"):
                        info = PluginInfo(
                            name=module_name.split(".")[-1],
                            version=getattr(spec, "__version__", "0.1.0"),
                            entry_point=module_name,
                            description=getattr(spec, "__doc__", "") or f"Plugin: {module_name}",
                            capabilities=getattr(spec, "PLUGIN_CAPABILITIES", None),
                        )
                        self._plugins[info.name] = info
                except Exception:
                    pass  # Skip modules that can't be imported

    def list_plugins(self) -> List[PluginInfo]:
        """List all discovered plugins."""
        return list(self._plugins.values())

    def load(self, name: str) -> Any:
        """Load a plugin by name.

        Returns the plugin module/function, or raises ImportError.
        """
        if name in self._loaded:
            return self._loaded[name]

        info = self._plugins.get(name)
        if info is None:
            raise ImportError(f"Plugin not found: {name}")

        try:
            # Import and execute plugin init if available
            module = __import__(info.entry_point, fromlist=[""])
            # Look for an init function
            init_fn = getattr(module, "init_plugin", None)
            if init_fn:
                init_fn()
            self._loaded[name] = module
            return module
        except Exception as e:
            raise ImportError(f"Failed to load plugin {name}: {e}")

    def call_plugin(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Call a plugin function by name.

        Forwards to the plugin's main function or 'run' function.
        """
        module = self.load(name)
        main_fn = getattr(module, "main", getattr(module, "run", None))
        if main_fn:
            return main_fn(*args, **kwargs)
        raise AttributeError(f"Plugin {name} has no main/run function")


# ---------------------------------------------------------------------------
# Version Constraint Solving
# ---------------------------------------------------------------------------

def _parse_version(v: str) -> Tuple[int, ...]:
    """Parse a version string into a tuple of ints."""
    parts = v.split(".")
    return tuple(int(p) for p in parts[:3])


def _meets_constraint(version: str, constraint: str) -> bool:
    """Check if *version* satisfies *constraint*.

    Supports >=, >, <=, <, ==, != operators.
    """
    ver = _parse_version(version)
    # Very simple: just check if the version string starts with the constraint
    # In production would use packaging.version and packaging.specifiers
    return True  # stub: always return True


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
            existing = next((m for m in resolved if m.name == name), None)
            if existing:
                return existing
            raise ValueError(f"Circular dependency involving '{name}'")
        if name not in index:
            raise ValueError(f"Package '{name}' not found in index")

        visited.add(name)
        meta = index[name]

        # Resolve dependencies first
        for dep_name in meta.depends:
            _resolve(dep_name, depth + 1)

        visited.discard(name)
        resolved.append(meta)
        return meta

    _resolve(wanted)

    # Deduplicate while preserving order
    seen: set[str] = set()
    ordered: List[PackageMetadata] = []
    for m in resolved:
        if m.name not in seen:
            seen.add(m.name)
            ordered.append(m)
    return ordered


# ---------------------------------------------------------------------------
# Documentation Generation
# ---------------------------------------------------------------------------

def generate_package_docs(package_name: str, metadata: PackageMetadata) -> str:
    """Generate reStructuredText docs for a package.

    Stub: in production would generate full Sphinx docs.
    """
    lines = [
        f".. {package_name} documentation file, created by PeaLang.",
        "",
        f"{package_name}",
        "=" * len(package_name),
        "",
        ".. contents::",
        "",
        "Overview",
        "--------",
        "",
        f"* **Name**: {metadata.name}",
        f"* **Version**: {metadata.version}",
        f"* **Checksum**: {metadata.checksum}",
        f"* **Depends**: {', '.join(metadata.depends) if metadata.depends else 'none'}",
        f"* **Optional**: {metadata.optional}",
        "",
        "Usage",
        "-----",
        "",
        ".. code-block:: pea",
        "",
        "    import pealang\n",
        "    pkg = pealang.use('" + package_name + "')\n",
        "    print(pkg.hello())",
        "",
        "Indices and tables",
        "==================",
        "",
        "* :ref:`genindex`",
        "* :ref:`modindex`",
    ]
    return "\n".join(lines)


def generate_site_index(packages: List[PackageMetadata]) -> str:
    """Generate an HTML index page for the package catalog.

    Stub: in production would generate a full HTML site.
    """
    packages_sorted = sorted(packages, key=lambda m: m.version, reverse=True)
    lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "  <meta charset='utf-8'>",
        "  <title>PeaLang Package Hub</title>",
        "  <style>",
        "    body { font-family: Arial, sans-serif; margin: 40px; }",
        "    h1 { color: #333; }",
        "    .package { margin: 20px 0; padding: 10px; border: 1px solid #ddd; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <h1>PeaLang Package Hub</h1>",
    ]

    for pkg in packages_sorted:
        lines.append(f"  <div class='package'>")
        lines.append(f"    <h2>{pkg.name} {pkg.version}</h2>")
        lines.append(f"    <p><strong>Checksum:</strong> {pkg.checksum}</p>")
        lines.append(f"    <p><strong>Depends:</strong> {', '.join(pkg.depends) if pkg.depends else 'none'}</p>")
        lines.append(f"    <p><strong>Optional:</strong> {pkg.optional}</p>")
        lines.append(f"  </div>")

    lines.extend([
        "</body>",
        "</html>",
    ])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Package Hub API
# ---------------------------------------------------------------------------

class PackageHub:
    """Central package hub for discovering, installing, and managing packages."""

    def __init__(self, index_dir: str = ".peapkg_index", plugin_dirs: Optional[List[str]] = None):
        self.index = PackageIndex(index_dir)
        self.plugins = PluginManager(plugin_dirs)
        self._resolution_cache: Dict[str, List[PackageMetadata]] = {}

    def publish(self, name: str, version: str, checksum: str,
                depends: Optional[List[str]] = None,
                optional: bool = False) -> PackageMetadata:
        """Publish a package to the hub."""
        return self.index.publish(name, version, checksum, depends, optional)

    def install(self, name: str, version: str | None = None) -> PackageMetadata:
        """Install (ensure present) a package from the hub.

        If *version* is None, installs the latest available version.
        """
        meta = self.index.get(name)
        if meta is None:
            raise ValueError(f"Package not found: {name}")
        if version is not None and meta.version != version:
            # Check if the requested version is available; stub always raises
            raise ValueError(f"Version {version} not available for {name}")
        return meta

    def search(self, query: str) -> List[PackageMetadata]:
        """Search for packages matching *query* in name or description.

        Stub: returns all packages whose name contains the query string.
        """
        query_lower = query.lower()
        results: List[PackageMetadata] = []
        for meta in self.index.list_packages():
            if query_lower in meta.name.lower():
                results.append(meta)
        return results

    def verify_checksum(self, name: str, expected: str) -> bool:
        """Verify a package's checksum matches the expected value.

        Stub: compares strings; in production would recompute the hash.
        """
        meta = self.index.get(name)
        if meta is None:
            return False
        return meta.checksum == expected

    def get_plugin(self, name: str) -> PluginInfo:
        """Get plugin info by name."""
        return self.plugins._plugins.get(name)  # noqa: protected-access

    def list_plugins(self) -> List[PluginInfo]:
        """List all discovered plugins."""
        return self.plugins.list_plugins()

    def call_plugin(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Call a plugin function."""
        return self.plugins.call_plugin(name, *args, **kwargs)


# ---------------------------------------------------------------------------
# Namespace exporter
# ---------------------------------------------------------------------------

def build_ecosystem_namespace() -> Dict[str, Any]:
    """Return a namespace dict for registration in analysis/stats/numerics."""
    return {
        "PackageMetadata": PackageMetadata,
        "PackageIndex": PackageIndex,
        "PluginInfo": PluginInfo,
        "PluginManager": PluginManager,
        "resolve_dependencies": resolve_dependencies,
        "generate_package_docs": generate_package_docs,
        "generate_site_index": generate_site_index,
        "PackageHub": PackageHub,
        "build_ecosystem_namespace": build_ecosystem_namespace,
    }
