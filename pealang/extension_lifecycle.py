"""PeaLang Extension Lifecycle & Deprecation Management (v2.40.0).

Provides deprecation warnings, migration paths, and version compatibility
checking for PeaLang extensions. Extensions can be marked as deprecated with
migration guidance, and the type system will warn when deprecated extensions
are used.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import time


@dataclass
class ExtensionDeprecation:
    """Records a deprecation notice for an extension."""

    extension_name: str
    deprecated_version: str
    deprecated_at: int
    removal_version: Optional[str] = None
    removal_date: Optional[int] = None
    message: str = ""
    migration_guide: Optional[str] = None
    replacement: Optional[str] = None


@dataclass
class ExtensionVersion:
    """Tracks version information for an extension."""

    name: str
    version: str
    released_at: int
    deprecated: bool = False
    deprecation: Optional[ExtensionDeprecation] = None


class ExtensionLifecycleManager:
    """Manages extension lifecycle: deprecation, migration, compatibility."""

    def __init__(self, storage_dir: str = "./extension-lifecycle") -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.deprecations: Dict[str, ExtensionDeprecation] = {}
        self.versions: Dict[str, List[ExtensionVersion]] = {}
        self._load()

    def _load(self) -> None:
        """Load lifecycle data from disk."""
        deprecations_file = self.storage_dir / "deprecations.json"
        versions_file = self.storage_dir / "versions.json"

        if deprecations_file.exists():
            try:
                data = json.loads(deprecations_file.read_text())
                for key, val in data.items():
                    self.deprecations[key] = ExtensionDeprecation(**val)
            except Exception:
                pass

        if versions_file.exists():
            try:
                data = json.loads(versions_file.read_text())
                for key, val_list in data.items():
                    self.versions[key] = [ExtensionVersion(**v) for v in val_list]
            except Exception:
                pass

    def _save(self) -> None:
        """Save lifecycle data to disk."""
        deprecations_file = self.storage_dir / "deprecations.json"
        versions_file = self.storage_dir / "versions.json"

        deprecations_file.write_text(
            json.dumps(
                {k: asdict(v) for k, v in self.deprecations.items()},
                indent=2,
            )
        )

        versions_file.write_text(
            json.dumps(
                {k: [asdict(v) for v in versions] for k, versions in self.versions.items()},
                indent=2,
            )
        )

    def register_version(
        self,
        name: str,
        version: str,
        released_at: Optional[int] = None,
    ) -> ExtensionVersion:
        """Register a new version of an extension."""
        if released_at is None:
            released_at = int(time.time())

        ev = ExtensionVersion(
            name=name,
            version=version,
            released_at=released_at,
        )

        if name not in self.versions:
            self.versions[name] = []
        self.versions[name].append(ev)
        self._save()
        return ev

    def deprecate(
        self,
        name: str,
        version: str,
        message: str = "",
        replacement: Optional[str] = None,
        migration_guide: Optional[str] = None,
        removal_version: Optional[str] = None,
        removal_date: Optional[int] = None,
    ) -> ExtensionDeprecation:
        """Deprecate an extension version."""

        if name not in self.versions:
            # Register the version if it doesn't exist
            self.register_version(name, version)

        deprecated = ExtensionDeprecation(
            extension_name=name,
            deprecated_version=version,
            deprecated_at=int(time.time()),
            removal_version=removal_version,
            removal_date=removal_date,
            message=message,
            migration_guide=migration_guide,
            replacement=replacement,
        )
        self.deprecations[f"{name}@{version}"] = deprecated

        # Mark the version as deprecated
        for ev in self.versions.get(name, []):
            if ev.version == version:
                ev.deprecated = True
                ev.deprecation = deprecated

        self._save()
        return deprecated

    def is_deprecated(self, name: str, version: str) -> bool:
        """Check if an extension version is deprecated."""
        key = f"{name}@{version}"
        return key in self.deprecations

    def get_deprecation(self, name: str, version: str) -> Optional[ExtensionDeprecation]:
        """Get deprecation info for an extension version."""
        key = f"{name}@{version}"
        return self.deprecations.get(key)

    def check_compatibility(
        self,
        name: str,
        from_version: str,
        to_version: str,
    ) -> Dict[str, Any]:
        """Check compatibility between two versions of an extension."""
        from_ev = None
        to_ev = None

        for ev in self.versions.get(name, []):
            if ev.version == from_version:
                from_ev = ev
            if ev.version == to_version:
                to_ev = ev

        if from_ev is None or to_ev is None:
            return {
                "compatible": False,
                "reason": "One or both versions not found",
            }

        # Check if either version is deprecated
        from_deprecated = self.is_deprecated(name, from_version)
        to_deprecated = self.is_deprecated(name, to_version)

        # Check if major version changed (breaking change)
        from_parts = from_version.split(".")
        to_parts = to_version.split(".")
        major_changed = from_parts[0] != to_parts[0]

        compatible = (
            not from_deprecated
            and not to_deprecated
            and not major_changed
        )

        return {
            "compatible": compatible,
            "from_version": from_version,
            "to_version": to_version,
            "from_deprecated": from_deprecated,
            "to_deprecated": to_deprecated,
            "major_changed": major_changed,
            "migration_guide": (
                self.deprecations[f"{name}@{from_version}"].migration_guide
                if from_deprecated and f"{name}@{from_version}" in self.deprecations
                else None
            ),
            "replacement": (
                self.deprecations[f"{name}@{from_version}"].replacement
                if from_deprecated and f"{name}@{from_version}" in self.deprecations
                else None
            ),
        }

    def list_deprecated(self) -> List[ExtensionDeprecation]:
        """List all deprecated extensions."""
        return list(self.deprecations.values())

    def get_migration_path(
        self,
        name: str,
        from_version: str,
    ) -> Optional[Dict[str, Any]]:
        """Get migration path for a deprecated extension version."""
        dep = self.get_deprecation(name, from_version)
        if dep is None:
            return None

        # Find the latest non-deprecated version
        latest = None
        for ev in self.versions.get(name, []):
            if not ev.deprecated:
                if latest is None or ev.released_at > latest.released_at:
                    latest = ev

        return {
            "from_version": from_version,
            "to_version": latest.version if latest else None,
            "replacement": dep.replacement,
            "migration_guide": dep.migration_guide,
            "message": dep.message,
            "removal_version": dep.removal_version,
            "removal_date": dep.removal_date,
        }


def create_lifecycle_manager(
    storage_dir: str = "./extension-lifecycle",
) -> ExtensionLifecycleManager:
    """Factory function to create an ExtensionLifecycleManager."""
    return ExtensionLifecycleManager(storage_dir)
