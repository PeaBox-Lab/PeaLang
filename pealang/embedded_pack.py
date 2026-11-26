"""Phase 97: deterministic Embedded / IoT / OS sector-pack evidence.

This module continues Wave 4 with a focused sector pack for firmware and OS
delivery. It inventories embedded manifests, validates their dependency graph and
platform contracts, and reports a deterministic application order and incomplete
set. All evidence is free of wall-clock values and absolute host paths. It
reports a plan; it does not create or modify project files.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

EMBEDDED_PACK_VERSION = '3.1.60'
EMBEDDED_PACK_FORMAT = 'pea-embedded-pack'
EMBEDDED_PACK_SKIP_DIRS = frozenset({
    '.git', '.venv', '__pycache__', '.pea_modules', '.pea_test_index', 'build',
    'node_modules', 'dist',
})
EMBEDDED_PACK_PREVIEW_DIRS = frozenset({'preview', 'canary', 'experimental'})
EMBEDDED_KINDS = frozenset({
    'native-profile', 'c-abi', 'rtos-binding', 'static-binary', 'gpio-api',
    'i2c-api', 'spi-api', 'can-api', 'safety-audit', 'resource',
    'firmware-demo',
})
EMBEDDED_NAME_RE = re.compile(r'^[a-z][a-z0-9_-]*$')


class EmbeddedPackError(Exception):
    """Raised when an embedded profile, manifest, or state input is invalid."""
    pass


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class EmbeddedProfileV2:
    """A validated, serializable Embedded / IoT / OS sector-pack profile."""

    max_firmware: int = 500
    include_preview: bool = False
    check_native: bool = True
    check_c_abi: bool = True
    check_rtos: bool = True
    check_static: bool = True
    check_bus: bool = True
    check_safety: bool = True
    check_memory: bool = True
    check_signed: bool = True
    fail_on_incomplete: bool = False
    current_version: str = ''

    def __post_init__(self) -> None:
        if int(self.max_firmware) < 1:
            raise EmbeddedPackError('max_firmware must be at least 1')
        if not isinstance(self.current_version, str):
            raise EmbeddedPackError('current_version must be a string')

    def effective_version(self) -> str:
        return self.current_version or EMBEDDED_PACK_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return _digest(self.to_dict())


DEFAULT_EMBEDDED_PROFILE = EmbeddedProfileV2()


def embedded_pack_capabilities() -> dict[str, Any]:
    """Return the versioned Embedded / IoT / OS sector-pack capability set."""

    return {
        'version': EMBEDDED_PACK_VERSION,
        'format': EMBEDDED_PACK_FORMAT,
        'profile': DEFAULT_EMBEDDED_PROFILE.to_dict(),
        'options': ['max_firmware', 'include_preview', 'check_native',
                    'check_c_abi', 'check_rtos', 'check_static', 'check_bus',
                    'check_safety', 'check_memory', 'check_signed',
                    'fail_on_incomplete', 'current_version'],
        'source_filter': '*.embedded.json',
        'kinds': sorted(EMBEDDED_KINDS),
        'stable_order': True,
        'wall_clock_excluded': True,
        'host_paths_excluded': True,
        'recomputed_gate': True,
    }


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _discover(root: Path, profile: EmbeddedProfileV2) -> list[str]:
    paths: list[str] = []
    for path in root.rglob('*.embedded.json'):
        parts = path.relative_to(root).parts
        if any(part in EMBEDDED_PACK_SKIP_DIRS for part in parts[:-1]):
            continue
        if (not profile.include_preview
                and any(part in EMBEDDED_PACK_PREVIEW_DIRS
                        for part in parts[:-1])):
            continue
        paths.append(_relative(path, root))
    return sorted(paths)


def _manifest(base: Path, path: str) -> dict[str, Any] | None:
    try:
        data = json.loads((base / path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    name = data.get('name')
    version = data.get('version', '')
    kind = data.get('kind', '')
    evidence = data.get('evidence')
    requires = data.get('requires', [])
    bindings = data.get('bindings', [])
    if not isinstance(name, str) or not EMBEDDED_NAME_RE.match(name):
        return None
    if not isinstance(version, str) or not isinstance(kind, str):
        return None
    if kind not in EMBEDDED_KINDS:
        return None
    if (not isinstance(evidence, list) or not evidence
            or not all(isinstance(item, str) and item for item in evidence)):
        return None
    if not isinstance(requires, list) or not all(
            isinstance(item, str) for item in requires):
        return None
    if not isinstance(bindings, list) or not all(
            isinstance(item, str) for item in bindings):
        return None
    return {
        'name': name,
        'version': version,
        'kind': kind,
        'evidence': tuple(sorted(set(evidence))),
        'requires': tuple(sorted(set(requires))),
        'bindings': tuple(sorted(set(bindings))),
    }


def _canonical_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    items = list(cycle[:-1] if cycle and cycle[-1] == cycle[0] else cycle)
    rotations = [tuple(items[index:] + items[:index])
                 for index in range(len(items))]
    return min(rotations)


@dataclass(frozen=True)
class EmbeddedIssueV2:
    """One stable Embedded / IoT / OS sector-pack issue."""

    code: str
    severity: str
    message: str
    path: str

    def fingerprint(self) -> str:
        return _digest([self.code, self.severity, self.message, self.path])

    def to_dict(self) -> dict[str, Any]:
        return {
            'code': self.code,
            'severity': self.severity,
            'message': self.message,
            'path': self.path,
            'fingerprint': self.fingerprint(),
        }


@dataclass(frozen=True)
class EmbeddedAppV2:
    """One reviewed embedded node in a sector-pack plan."""

    path: str
    digest: str
    name: str
    version: str
    kind: str
    evidence: tuple[str, ...]
    requires: tuple[str, ...]
    bindings: tuple[str, ...]
    dependencies: tuple[str, ...]
    state: str
    reasons: tuple[str, ...]

    def fingerprint(self) -> str:
        return _digest([
            self.path, self.digest, self.name, self.version, self.kind,
            list(self.evidence), list(self.requires), list(self.bindings),
            list(self.dependencies), self.state, list(self.reasons),
        ])

    def to_dict(self) -> dict[str, Any]:
        return {
            'path': self.path,
            'digest': self.digest,
            'name': self.name,
            'version': self.version,
            'kind': self.kind,
            'evidence': list(self.evidence),
            'requires': list(self.requires),
            'bindings': list(self.bindings),
            'dependencies': list(self.dependencies),
            'state': self.state,
            'reasons': list(self.reasons),
            'fingerprint': self.fingerprint(),
        }


def _decision(error_count: int, incomplete_count: int,
              profile: EmbeddedProfileV2) -> dict[str, Any]:
    issues: list[str] = []
    if error_count:
        issues.append('errors')
    if profile.fail_on_incomplete and incomplete_count:
        issues.append('incomplete')
    return {'gate': 'FAIL' if issues else 'PASS', 'issues': issues}


@dataclass(frozen=True)
class EmbeddedPackPlanV2:
    """Reviewable outcome of one Embedded / IoT / OS sector-pack inventory."""

    version: str
    format: str
    profile: dict[str, Any]
    root_name: str
    apps: tuple[EmbeddedAppV2, ...]
    build_order: tuple[str, ...]
    incomplete: tuple[str, ...]
    issues: tuple[EmbeddedIssueV2, ...]
    gate: str
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
            'format': self.format,
            'profile': self.profile,
            'root_name': self.root_name,
            'app_count': len(self.apps),
            'clean_count': len(self.apps) - len(self.incomplete),
            'incomplete_count': len(self.incomplete),
            'error_count': len(self.issues),
            'apps': [item.to_dict() for item in self.apps],
            'build_order': list(self.build_order),
            'incomplete': list(self.incomplete),
            'issues': [item.to_dict() for item in self.issues],
            'gate': self.gate,
            'digest': self.digest,
        }


def plan_embedded_pack(root: str | Path,
                       profile: EmbeddedProfileV2 | None = None,
                       state: dict[str, str] | None = None
                       ) -> EmbeddedPackPlanV2:
    """Inventory embedded apps with stable, reviewable output."""

    base = Path(root)
    if not base.is_dir():
        raise EmbeddedPackError('root must be a directory')
    active = profile or DEFAULT_EMBEDDED_PROFILE
    previous = state or {}
    if not isinstance(previous, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in previous.items()):
        raise EmbeddedPackError('state must map paths to digests')
    paths = _discover(base, active)
    issues: list[EmbeddedIssueV2] = []
    if len(paths) > active.max_firmware:
        issues.append(EmbeddedIssueV2(
            'E203', 'error',
            f'Embedded pack has {len(paths)} apps, exceeding limit '
            f'{active.max_firmware}',
            '.',
        ))

    digests: dict[str, str] = {}
    manifests: dict[str, dict[str, Any]] = {}
    for path in paths:
        data = (base / path).read_bytes()
        digests[path] = hashlib.sha256(data).hexdigest()
        manifest = _manifest(base, path)
        if manifest is None:
            issues.append(EmbeddedIssueV2(
                'E204', 'error',
                f'Embedded app "{path}" is invalid',
                path,
            ))
            manifest = {
                'name': '', 'version': '', 'kind': '', 'evidence': (),
                'requires': (), 'bindings': (),
            }
        manifests[path] = manifest
        for evidence in manifest['evidence']:
            if not (base / evidence).is_file():
                issues.append(EmbeddedIssueV2(
                    'E205', 'error',
                    f'Evidence "{evidence}" declared by "{path}" is missing',
                    path,
                ))

    providers: dict[str, set[str]] = {}
    for path, manifest in manifests.items():
        if manifest['name']:
            providers.setdefault(manifest['name'], set()).add(path)

    dependencies: dict[str, tuple[str, ...]] = {}
    for path, manifest in manifests.items():
        resolved: set[str] = set()
        for name in manifest['requires']:
            candidates = providers.get(name, set())
            if candidates:
                resolved.update(candidates)
            else:
                issues.append(EmbeddedIssueV2(
                    'E201', 'error',
                    f'Embedded app "{name}" required by "{path}" is not '
                    'present',
                    path,
                ))
        dependencies[path] = tuple(sorted(resolved))

    reverse: dict[str, list[str]] = {path: [] for path in paths}
    for path, deps in dependencies.items():
        for dep in deps:
            reverse[dep].append(path)

    colors: dict[str, int] = {}
    stack: list[str] = []
    cycles: list[tuple[str, ...]] = []

    def visit(path: str) -> None:
        colors[path] = 1
        stack.append(path)
        for dep in dependencies[path]:
            if colors.get(dep) == 1:
                cycles.append(_canonical_cycle(tuple(stack[stack.index(dep):])))
            elif colors.get(dep, 0) == 0:
                visit(dep)
        stack.pop()
        colors[path] = 2

    for path in paths:
        if colors.get(path, 0) == 0:
            visit(path)
    for cycle in sorted(set(cycles)):
        issues.append(EmbeddedIssueV2(
            'E202', 'error',
            'Dependency cycle: ' + ' -> '.join(cycle + (cycle[0],)),
            cycle[0],
        ))

    def require_kind(check: bool, code: str, kinds: set[str],
                     message: str) -> None:
        if not check:
            return
        provider_paths = {
            path for path, manifest in manifests.items()
            if manifest['kind'] in kinds
        }
        for path, manifest in manifests.items():
            if (manifest['kind'] == 'firmware-demo'
                    and not provider_paths.intersection(dependencies[path])):
                issues.append(EmbeddedIssueV2(
                    code, 'error',
                    f'Firmware demo "{path}" has no {message} dependency',
                    path,
                ))

    require_kind(active.check_native, 'E206', {'native-profile'},
                 'no-GC native profile')
    require_kind(active.check_c_abi, 'E207', {'c-abi'}, 'C ABI')
    require_kind(active.check_rtos, 'E208', {'rtos-binding'}, 'RTOS binding')
    require_kind(active.check_static, 'E209', {'static-binary'},
                 'static binary')
    require_kind(active.check_bus, 'E210',
                 {'gpio-api', 'i2c-api', 'spi-api', 'can-api'},
                 'GPIO/I2C/SPI/CAN API')
    require_kind(active.check_safety, 'E211', {'safety-audit'},
                 'safety audit')

    if active.check_memory:
        for path, manifest in manifests.items():
            if (manifest['kind'] == 'firmware-demo'
                    and 'bounded-memory' not in manifest['bindings']):
                issues.append(EmbeddedIssueV2(
                    'E212', 'error',
                    f'Firmware demo "{path}" has no bounded-memory binding',
                    path,
                ))
    if active.check_signed:
        for path, manifest in manifests.items():
            if (manifest['kind'] == 'firmware-demo'
                    and 'signed-update' not in manifest['bindings']):
                issues.append(EmbeddedIssueV2(
                    'E213', 'error',
                    f'Firmware demo "{path}" has no signed-update binding',
                    path,
                ))

    indegree = {path: len(dependencies[path]) for path in paths}
    ready = [path for path, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        path = heapq.heappop(ready)
        order.append(path)
        for dependent in sorted(reverse[path]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, dependent)
    order.extend(path for path in paths if path not in set(order))

    reasons: dict[str, list[str]] = {path: [] for path in paths}
    stale = {path for path in paths if previous.get(path) != digests[path]}
    for path in sorted(stale):
        reasons[path].append('new' if path not in previous else 'changed')
    queue = sorted(stale)
    while queue:
        source = queue.pop(0)
        for dependent in sorted(reverse[source]):
            if dependent not in stale:
                stale.add(dependent)
                reasons[dependent].append('dependency')
                queue.append(dependent)
    apps = tuple(
        EmbeddedAppV2(
            path=path,
            digest=digests[path],
            name=manifests[path]['name'],
            version=manifests[path]['version'],
            kind=manifests[path]['kind'],
            evidence=manifests[path]['evidence'],
            requires=manifests[path]['requires'],
            bindings=manifests[path]['bindings'],
            dependencies=dependencies[path],
            state='stale' if path in stale else 'current',
            reasons=tuple(sorted(set(reasons[path]))),
        )
        for path in paths
    )
    incomplete = tuple(path for path in paths if path in stale)
    ordered_issues = tuple(sorted(
        issues, key=lambda item: (item.code, item.path, item.message),
    ))
    gate = _decision(len(ordered_issues), len(incomplete), active)['gate']
    payload = {
        'version': EMBEDDED_PACK_VERSION,
        'format': EMBEDDED_PACK_FORMAT,
        'profile': active.digest(),
        'apps': [item.fingerprint() for item in apps],
        'build_order': order,
        'incomplete': list(incomplete),
        'issues': [item.fingerprint() for item in ordered_issues],
        'gate': gate,
    }
    return EmbeddedPackPlanV2(
        version=EMBEDDED_PACK_VERSION,
        format=EMBEDDED_PACK_FORMAT,
        profile=active.to_dict(),
        root_name=base.resolve().name,
        apps=apps,
        build_order=tuple(order),
        incomplete=incomplete,
        issues=ordered_issues,
        gate=gate,
        digest=_digest(payload),
    )


def load_embedded_state_v2(path: str | Path) -> dict[str, str]:
    """Load versioned embedded state, returning empty state when absent."""

    target = Path(path)
    if not target.is_file():
        return {}
    try:
        data = json.loads(target.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise EmbeddedPackError('embedded state is not valid JSON') from exc
    if data.get('version') != EMBEDDED_PACK_VERSION:
        raise EmbeddedPackError('embedded state version does not match')
    state = data.get('state', {})
    if not isinstance(state, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in state.items()):
        raise EmbeddedPackError('embedded state must map paths to digests')
    return dict(state)


def write_embedded_state_v2(root: str | Path, plan: EmbeddedPackPlanV2,
                            path: str | Path | None = None) -> Path:
    """Persist a deterministic Embedded / IoT / OS sector-pack digest state."""

    target = (Path(path) if path is not None
              else Path(root) / '.pea_embedded_pack.json')
    payload = {
        'version': EMBEDDED_PACK_VERSION,
        'format': EMBEDDED_PACK_FORMAT,
        'state': {item.path: item.digest for item in plan.apps},
    }
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8',
    )
    return target


def _issue_fingerprint(item: dict[str, Any]) -> str:
    return _digest([
        item.get('code'), item.get('severity'), item.get('message'),
        item.get('path'),
    ])


def _app_fingerprint(item: dict[str, Any]) -> str:
    return _digest([
        item.get('path'), item.get('digest'), item.get('name'),
        item.get('version'), item.get('kind'),
        list(item.get('evidence', [])), list(item.get('requires', [])),
        list(item.get('bindings', [])), list(item.get('dependencies', [])),
        item.get('state'), list(item.get('reasons', [])),
    ])


def _plan_digest(item: dict[str, Any]) -> str:
    return _digest({
        'version': item.get('version'),
        'format': item.get('format'),
        'profile': _digest(item.get('profile', {})),
        'apps': [x.get('fingerprint') for x in item.get('apps', [])],
        'build_order': item.get('build_order', []),
        'incomplete': list(item.get('incomplete', [])),
        'issues': [x.get('fingerprint') for x in item.get('issues', [])],
        'gate': item.get('gate'),
    })


def _report_digest(report: dict[str, Any]) -> str:
    return _digest({
        'version': report.get('version'),
        'format': report.get('format'),
        'profile_digest': report.get('profile_digest'),
        'plan_count': report.get('plan_count'),
        'app_count': report.get('app_count'),
        'clean_count': report.get('clean_count'),
        'incomplete_count': report.get('incomplete_count'),
        'error_count': report.get('error_count'),
        'plans': [
            {
                'app_count': item.get('app_count'),
                'incomplete_count': item.get('incomplete_count'),
                'error_count': item.get('error_count'),
                'gate': item.get('gate'),
                'digest': item.get('digest'),
            }
            for item in report.get('plans', [])
        ],
        'gate': report.get('gate'),
    })


def embedded_pack_report(plans: Iterable[EmbeddedPackPlanV2],
                         profile: EmbeddedProfileV2 | None = None
                         ) -> dict[str, Any]:
    """Summarize embedded plans with a recomputable digest."""

    active = profile or DEFAULT_EMBEDDED_PROFILE
    items = list(plans)
    app_count = sum(len(item.apps) for item in items)
    incomplete_count = sum(len(item.incomplete) for item in items)
    error_count = sum(len(item.issues) for item in items)
    payload: dict[str, Any] = {
        'version': EMBEDDED_PACK_VERSION,
        'format': EMBEDDED_PACK_FORMAT,
        'profile': active.to_dict(),
        'profile_digest': active.digest(),
        'plan_count': len(items),
        'app_count': app_count,
        'clean_count': app_count - incomplete_count,
        'incomplete_count': incomplete_count,
        'error_count': error_count,
        'plans': [item.to_dict() for item in items],
        'gate': _decision(error_count, incomplete_count, active)['gate'],
    }
    payload['digest'] = _report_digest(payload)
    return payload


def embedded_pack_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute a deterministic PASS/FAIL decision from an embedded report."""

    issues: list[str] = []
    if report.get('version') != EMBEDDED_PACK_VERSION:
        issues.append('version')
    if report.get('format') != EMBEDDED_PACK_FORMAT:
        issues.append('format')
    if report.get('gate') not in ('PASS', 'FAIL'):
        issues.append('report')
    digest = str(report.get('digest', ''))
    if len(digest) != 64 or digest != _report_digest(report):
        issues.append('digest')
    app_count = int(report.get('app_count', 0))
    incomplete_count = int(report.get('incomplete_count', 0))
    error_count = int(report.get('error_count', 0))
    clean_count = int(report.get('clean_count', 0))
    if app_count != clean_count + incomplete_count:
        issues.append('counts')
    for item in report.get('plans', []):
        item_digest = str(item.get('digest', ''))
        if len(item_digest) != 64 or item_digest != _plan_digest(item):
            issues.append('plan_digest')
        if int(item.get('app_count', 0)) != (
                int(item.get('clean_count', 0))
                + int(item.get('incomplete_count', 0))):
            issues.append('plan_counts')
        for app in item.get('apps', []):
            fingerprint = str(app.get('fingerprint', ''))
            if (len(fingerprint) != 64
                    or fingerprint != _app_fingerprint(app)):
                issues.append('app_fingerprint')
        for issue_item in item.get('issues', []):
            fingerprint = str(issue_item.get('fingerprint', ''))
            if (len(fingerprint) != 64
                    or fingerprint != _issue_fingerprint(issue_item)):
                issues.append('issue_fingerprint')
    profile_data = report.get('profile') or DEFAULT_EMBEDDED_PROFILE.to_dict()
    try:
        profile = EmbeddedProfileV2(**profile_data)
    except Exception:
        issues.append('profile')
        profile = DEFAULT_EMBEDDED_PROFILE
    expected = _decision(error_count, incomplete_count, profile)
    if report.get('gate') != expected['gate']:
        issues.append('gate')
    issues.extend(expected['issues'])
    return {'gate': 'PASS' if not issues else 'FAIL',
            'issues': sorted(set(issues))}


def build_embedded_pack_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'EMBEDDED_PACK_VERSION': EMBEDDED_PACK_VERSION,
        'EMBEDDED_PACK_FORMAT': EMBEDDED_PACK_FORMAT,
        'EMBEDDED_PACK_SKIP_DIRS': EMBEDDED_PACK_SKIP_DIRS,
        'EMBEDDED_PACK_PREVIEW_DIRS': EMBEDDED_PACK_PREVIEW_DIRS,
        'EMBEDDED_KINDS': EMBEDDED_KINDS,
        'EmbeddedProfileV2': EmbeddedProfileV2,
        'DEFAULT_EMBEDDED_PROFILE': DEFAULT_EMBEDDED_PROFILE,
        'EmbeddedIssueV2': EmbeddedIssueV2,
        'EmbeddedAppV2': EmbeddedAppV2,
        'EmbeddedPackPlanV2': EmbeddedPackPlanV2,
        'EmbeddedPackError': EmbeddedPackError,
        'plan_embedded_pack': plan_embedded_pack,
        'load_embedded_state_v2': load_embedded_state_v2,
        'write_embedded_state_v2': write_embedded_state_v2,
        'embedded_pack_capabilities': embedded_pack_capabilities,
        'embedded_pack_report': embedded_pack_report,
        'embedded_pack_gate': embedded_pack_gate,
        'build_embedded_pack_namespace': build_embedded_pack_namespace,
    }


__all__ = [
    'EMBEDDED_PACK_VERSION', 'EMBEDDED_PACK_FORMAT',
    'EMBEDDED_PACK_SKIP_DIRS', 'EMBEDDED_PACK_PREVIEW_DIRS',
    'EMBEDDED_KINDS', 'EmbeddedProfileV2', 'DEFAULT_EMBEDDED_PROFILE',
    'EmbeddedPackError', 'EmbeddedIssueV2', 'EmbeddedAppV2',
    'EmbeddedPackPlanV2', 'plan_embedded_pack', 'load_embedded_state_v2',
    'write_embedded_state_v2', 'embedded_pack_capabilities',
    'embedded_pack_report', 'embedded_pack_gate',
    'build_embedded_pack_namespace',
]
