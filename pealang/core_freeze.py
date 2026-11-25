"""Frozen 3.0 language-core contract gate for PeaLang 3.1.37.

Phase 70 closes Wave 1 by freezing the language core that was built in phases
61-69. The gate combines four existing stability surfaces:

* the curated v2 conformance suite,
* the public API snapshot,
* the normative specification check, and
* an explicit manifest of frozen core surfaces.

Nothing here changes runtime behavior. It provides a deterministic report that
a release candidate can use to prove the core is complete and compatible.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .conformance_suite import conformance_report_v2
from .hardening import PublicAPIGate
from .rc_stabilization import public_api_snapshot
from .specification import verify_spec

CORE_VERSION = '3.0'
FREEZE_RELEASE = '3.1.37'


@dataclass(frozen=True)
class CoreSurface:
    """One named surface included in the frozen 3.0 core."""

    name: str
    category: str
    since: str
    stability: str = 'frozen'


CORE_SURFACES = (
    CoreSurface('core.syntax', 'syntax', '0.1'),
    CoreSurface('errors.structured_v2', 'errors', '2.41'),
    CoreSurface('language.generics_v2', 'types', '2.41'),
    CoreSurface('language.protocols_v2', 'types', '2.41'),
    CoreSurface('language.iterators', 'runtime', '2.41'),
    CoreSurface('language.async_v2', 'runtime', '2.41'),
    CoreSurface('language.modules_v2', 'modules', '2.41'),
    CoreSurface('language.macros_v2', 'metaprogramming', '2.41'),
    CoreSurface('language.resource_scopes_v2', 'runtime', '2.41'),
    CoreSurface('language.conformance_v2', 'quality', '2.41'),
    CoreSurface('vm.peac', 'bytecode', '0.20'),
)


class CoreFreezeManifest:
    """A versioned manifest of the frozen core surfaces."""

    def __init__(self, surfaces=()):
        self.surfaces = {surface.name: surface for surface in surfaces}

    def add(self, surface: CoreSurface) -> 'CoreFreezeManifest':
        if surface.name in self.surfaces:
            raise ValueError(f'duplicate frozen surface: {surface.name}')
        self.surfaces[surface.name] = surface
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            'schema': 1,
            'policy': 'pealang-3.0-core-freeze',
            'core_version': CORE_VERSION,
            'release': FREEZE_RELEASE,
            'surfaces': [asdict(surface) for surface in sorted(
                self.surfaces.values(), key=lambda item: item.name)],
        }

    def digest(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def diff(self, baseline: 'CoreFreezeManifest') -> dict[str, list[str]]:
        current = self.surfaces
        old = baseline.surfaces
        return {
            'added': sorted(set(current) - set(old)),
            'removed': sorted(set(old) - set(current)),
            'changed': sorted(
                name for name in set(current) & set(old)
                if current[name] != old[name]
            ),
        }


def default_core_manifest() -> CoreFreezeManifest:
    """Return the canonical frozen 3.0 core manifest."""

    return CoreFreezeManifest(CORE_SURFACES)


def _symbol_names(snapshot: dict[str, Any]) -> list[str]:
    return [f"{item['module']}.{item['name']}" for item in snapshot.get('symbols', ())]


def _package_version() -> str | None:
    from . import __version__
    return __version__


def core_freeze_gate(*, api=None, conformance=None, spec=None,
                     manifest=None, release=None) -> dict[str, Any]:
    """Reduce freeze inputs to a stable PASS/FAIL report."""

    release = release or FREEZE_RELEASE
    manifest = manifest or default_core_manifest()
    checks = {
        'public_api': bool(api and api.get('gate') == 'PASS'),
        'conformance': bool(conformance and conformance.get('suite', {}).get('ok')),
        'specification': bool(
            spec and spec.get('ok') and spec.get('version') == release),
        'surfaces': (
            len(manifest.surfaces) == len(CORE_SURFACES)
            and all(surface.stability == 'frozen'
                    for surface in manifest.surfaces.values())
        ),
        'version': _package_version() == release,
    }
    issues = [name for name, passed in checks.items() if not passed]
    return {
        'gate': 'PASS' if not issues else 'FAIL',
        'release': release,
        'core_version': CORE_VERSION,
        'checks': checks,
        'issues': issues,
        'digest': manifest.digest(),
    }


def verify_core_freeze(root: str | Path | None = None) -> dict[str, Any]:
    """Run the full frozen-core verification against repository artifacts."""

    base = Path(root) if root else Path(__file__).resolve().parent.parent
    snapshot_path = base / 'PUBLIC_API_SNAPSHOT.json'
    if snapshot_path.is_file():
        baseline = json.loads(snapshot_path.read_text(encoding='utf-8'))
        current = public_api_snapshot(base / 'pealang')
        api = PublicAPIGate().compare(_symbol_names(baseline), _symbol_names(current))
    else:
        api = {
            'gate': 'FAIL',
            'baseline': 0,
            'current': 0,
            'added': [],
            'removed': [],
            'approved_removals': [],
            'unexpected_removals': ['PUBLIC_API_SNAPSHOT.json'],
        }
    return core_freeze_gate(
        api=api,
        conformance=conformance_report_v2(),
        spec=verify_spec(base / 'spec'),
        manifest=default_core_manifest(),
    )


def core_freeze_report(root: str | Path | None = None) -> dict[str, Any]:
    """Return the CLI-facing frozen-core report."""

    manifest = default_core_manifest()
    return {
        'release': FREEZE_RELEASE,
        'core_version': CORE_VERSION,
        'manifest': manifest.to_dict(),
        'freeze': verify_core_freeze(root),
    }
