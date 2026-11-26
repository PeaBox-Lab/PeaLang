"""Phase 103: deterministic chaos engineering and resilience sector-pack evidence.

This module opens Wave 6 with a focused sector pack for chaos engineering and resilience.
It inventories Chaos manifests, validates their dependency graph and
Chaos contract, and reports a deterministic application order and
incomplete set. All evidence is free of wall-clock values and absolute host
paths. It reports a plan; it does not create or modify project files.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

CHAOS_PACK_VERSION = '5.3.0'
CHAOS_PACK_FORMAT = 'pea-chaos-pack'
CHAOS_PACK_SKIP_DIRS = frozenset({
    '.git', '.venv', '__pycache__', '.pea_modules', '.pea_test_index', 'build',
    'node_modules', 'dist',
})
CHAOS_PACK_PREVIEW_DIRS = frozenset({'preview', 'canary', 'experimental'})
CHAOS_KINDS = frozenset({
    'steady-state', 'hypothesis', 'blast-radius', 'abort-condition',
    'rollback-plan', 'game-day', 'resilience-report', 'resource',
    'resilience-demo',
})
CHAOS_NAME_RE = re.compile(r'^[a-z][a-z0-9_-]*$')


class ChaosPackError(Exception):
    """Raised when a Chaos profile, manifest, or state is invalid."""
    pass


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class ChaosProfileV2:
    """A validated, serializable chaos engineering and resilience profile."""

    max_entries: int = 500
    include_preview: bool = False
    check_steady: bool = True
    check_hypothesis: bool = True
    check_blast: bool = True
    check_abort: bool = True
    check_rollback: bool = True
    check_game_day: bool = True
    check_report: bool = True
    fail_on_incomplete: bool = False
    current_version: str = ''

    def __post_init__(self) -> None:
        if int(self.max_entries) < 1:
            raise ChaosPackError('max_entries must be at least 1')
        if not isinstance(self.current_version, str):
            raise ChaosPackError('current_version must be a string')

    def effective_version(self) -> str:
        return self.current_version or CHAOS_PACK_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return _digest(self.to_dict())


DEFAULT_CHAOS_PROFILE = ChaosProfileV2()


def chaos_pack_capabilities() -> dict[str, Any]:
    """Return the versioned Chaos capability set."""

    return {
        'version': CHAOS_PACK_VERSION,
        'format': CHAOS_PACK_FORMAT,
        'profile': DEFAULT_CHAOS_PROFILE.to_dict(),
        'options': ['max_entries', 'include_preview', 'check_steady',
                    'check_hypothesis', 'check_blast', 'check_abort',
                    'check_rollback', 'check_game_day', 'check_report',
                    'fail_on_incomplete', 'current_version'],
        'source_filter': '*.chaos.json',
        'kinds': sorted(CHAOS_KINDS),
        'stable_order': True,
        'wall_clock_excluded': True,
        'host_paths_excluded': True,
        'recomputed_gate': True,
    }


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _discover(root: Path, profile: ChaosProfileV2) -> list[str]:
    paths: list[str] = []
    for path in root.rglob('*.chaos.json'):
        parts = path.relative_to(root).parts
        if any(part in CHAOS_PACK_SKIP_DIRS for part in parts[:-1]):
            continue
        if (not profile.include_preview
                and any(part in CHAOS_PACK_PREVIEW_DIRS
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
    if not isinstance(name, str) or not CHAOS_NAME_RE.match(name):
        return None
    if not isinstance(version, str) or not isinstance(kind, str):
        return None
    if kind not in CHAOS_KINDS:
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
class ChaosIssueV2:
    """One stable chaos engineering and resilience issue."""

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
class ChaosAppV2:
    """One reviewed Chaos node in a sector-pack plan."""

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
              profile: ChaosProfileV2) -> dict[str, Any]:
    issues: list[str] = []
    if error_count:
        issues.append('errors')
    if profile.fail_on_incomplete and incomplete_count:
        issues.append('incomplete')
    return {'gate': 'FAIL' if issues else 'PASS', 'issues': issues}


@dataclass(frozen=True)
class ChaosPackPlanV2:
    """Reviewable outcome of one chaos engineering and resilience inventory."""

    version: str
    format: str
    profile: dict[str, Any]
    root_name: str
    apps: tuple[ChaosAppV2, ...]
    build_order: tuple[str, ...]
    incomplete: tuple[str, ...]
    issues: tuple[ChaosIssueV2, ...]
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


def plan_chaos_pack(root: str | Path,
                            profile: ChaosProfileV2 | None = None,
                            state: dict[str, str] | None = None
                            ) -> ChaosPackPlanV2:
    """Inventory Chaos entries with stable, reviewable output."""

    base = Path(root)
    if not base.is_dir():
        raise ChaosPackError('root must be a directory')
    active = profile or DEFAULT_CHAOS_PROFILE
    previous = state or {}
    if not isinstance(previous, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in previous.items()):
        raise ChaosPackError('state must map paths to digests')
    paths = _discover(base, active)
    issues: list[ChaosIssueV2] = []
    if len(paths) > active.max_entries:
        issues.append(ChaosIssueV2(
            'C203', 'error',
            f'Chaos pack has {len(paths)} entries, exceeding limit '
            f'{active.max_entries}',
            '.',
        ))

    digests: dict[str, str] = {}
    manifests: dict[str, dict[str, Any]] = {}
    for path in paths:
        data = (base / path).read_bytes()
        digests[path] = hashlib.sha256(data).hexdigest()
        manifest = _manifest(base, path)
        if manifest is None:
            issues.append(ChaosIssueV2(
                'C204', 'error',
                f'Chaos entry "{path}" is invalid',
                path,
            ))
            manifest = {
                'name': '', 'version': '', 'kind': '', 'evidence': (),
                'requires': (), 'bindings': (),
            }
        manifests[path] = manifest
        for evidence in manifest['evidence']:
            if not (base / evidence).is_file():
                issues.append(ChaosIssueV2(
                    'C205', 'error',
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
                issues.append(ChaosIssueV2(
                    'C201', 'error',
                    f'Chaos entry "{name}" required by "{path}" is '
                    'not present',
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
        issues.append(ChaosIssueV2(
            'C202', 'error',
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
            if (manifest['kind'] == 'resilience-demo'
                    and not provider_paths.intersection(dependencies[path])):
                issues.append(ChaosIssueV2(
                    code, 'error',
                    f'Resilience demo "{path}" has no {message} dependency',
                    path,
                ))

    require_kind(active.check_steady, 'C206', {'steady-state'},
                 'steady state')
    require_kind(active.check_hypothesis, 'C207', {'hypothesis'},
                 'hypothesis')
    require_kind(active.check_blast, 'C208', {'blast-radius'},
                 'blast radius')
    require_kind(active.check_abort, 'C209', {'abort-condition'},
                 'abort condition')
    require_kind(active.check_rollback, 'C210', {'rollback-plan'},
                 'rollback plan')
    require_kind(active.check_game_day, 'C211', {'game-day'}, 'game day')
    require_kind(active.check_report, 'C212', {'resilience-report'},
                 'resilience report')

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
        ChaosAppV2(
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
        'version': CHAOS_PACK_VERSION,
        'format': CHAOS_PACK_FORMAT,
        'profile': active.digest(),
        'apps': [item.fingerprint() for item in apps],
        'build_order': order,
        'incomplete': list(incomplete),
        'issues': [item.fingerprint() for item in ordered_issues],
        'gate': gate,
    }
    return ChaosPackPlanV2(
        version=CHAOS_PACK_VERSION,
        format=CHAOS_PACK_FORMAT,
        profile=active.to_dict(),
        root_name=base.resolve().name,
        apps=apps,
        build_order=tuple(order),
        incomplete=incomplete,
        issues=ordered_issues,
        gate=gate,
        digest=_digest(payload),
    )


def load_chaos_state_v2(path: str | Path) -> dict[str, str]:
    """Load versioned Chaos state, returning empty state if absent."""

    target = Path(path)
    if not target.is_file():
        return {}
    try:
        data = json.loads(target.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ChaosPackError('Chaos state is not valid JSON') from exc
    if data.get('version') != CHAOS_PACK_VERSION:
        raise ChaosPackError('Chaos state version does not match')
    state = data.get('state', {})
    if not isinstance(state, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in state.items()):
        raise ChaosPackError('Chaos state must map paths to digests')
    return dict(state)


def write_chaos_state_v2(root: str | Path,
                                 plan: ChaosPackPlanV2,
                                 path: str | Path | None = None) -> Path:
    """Persist a deterministic chaos engineering and resilience digest state."""

    target = (Path(path) if path is not None
              else Path(root) / '.pea_chaos_pack.json')
    payload = {
        'version': CHAOS_PACK_VERSION,
        'format': CHAOS_PACK_FORMAT,
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


def chaos_pack_report(plans: Iterable[ChaosPackPlanV2],
                              profile: ChaosProfileV2 | None = None
                              ) -> dict[str, Any]:
    """Summarize Chaos plans with a recomputable digest."""

    active = profile or DEFAULT_CHAOS_PROFILE
    items = list(plans)
    app_count = sum(len(item.apps) for item in items)
    incomplete_count = sum(len(item.incomplete) for item in items)
    error_count = sum(len(item.issues) for item in items)
    payload: dict[str, Any] = {
        'version': CHAOS_PACK_VERSION,
        'format': CHAOS_PACK_FORMAT,
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


def chaos_pack_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute a deterministic PASS/FAIL decision from an Chaos report."""

    issues: list[str] = []
    if report.get('version') != CHAOS_PACK_VERSION:
        issues.append('version')
    if report.get('format') != CHAOS_PACK_FORMAT:
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
    profile_data = (report.get('profile')
                    or DEFAULT_CHAOS_PROFILE.to_dict())
    try:
        profile = ChaosProfileV2(**profile_data)
    except Exception:
        issues.append('profile')
        profile = DEFAULT_CHAOS_PROFILE
    expected = _decision(error_count, incomplete_count, profile)
    if report.get('gate') != expected['gate']:
        issues.append('gate')
    issues.extend(expected['issues'])
    return {'gate': 'PASS' if not issues else 'FAIL',
            'issues': sorted(set(issues))}


def build_chaos_pack_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'CHAOS_PACK_VERSION': CHAOS_PACK_VERSION,
        'CHAOS_PACK_FORMAT': CHAOS_PACK_FORMAT,
        'CHAOS_PACK_SKIP_DIRS': CHAOS_PACK_SKIP_DIRS,
        'CHAOS_PACK_PREVIEW_DIRS': CHAOS_PACK_PREVIEW_DIRS,
        'CHAOS_KINDS': CHAOS_KINDS,
        'ChaosProfileV2': ChaosProfileV2,
        'DEFAULT_CHAOS_PROFILE': DEFAULT_CHAOS_PROFILE,
        'ChaosIssueV2': ChaosIssueV2,
        'ChaosAppV2': ChaosAppV2,
        'ChaosPackPlanV2': ChaosPackPlanV2,
        'ChaosPackError': ChaosPackError,
        'plan_chaos_pack': plan_chaos_pack,
        'load_chaos_state_v2': load_chaos_state_v2,
        'write_chaos_state_v2': write_chaos_state_v2,
        'chaos_pack_capabilities': chaos_pack_capabilities,
        'chaos_pack_report': chaos_pack_report,
        'chaos_pack_gate': chaos_pack_gate,
        'build_chaos_pack_namespace': build_chaos_pack_namespace,
    }


__all__ = [
    'CHAOS_PACK_VERSION', 'CHAOS_PACK_FORMAT',
    'CHAOS_PACK_SKIP_DIRS', 'CHAOS_PACK_PREVIEW_DIRS',
    'CHAOS_KINDS', 'ChaosProfileV2',
    'DEFAULT_CHAOS_PROFILE', 'ChaosPackError',
    'ChaosIssueV2', 'ChaosAppV2',
    'ChaosPackPlanV2', 'plan_chaos_pack',
    'load_chaos_state_v2', 'write_chaos_state_v2',
    'chaos_pack_capabilities', 'chaos_pack_report',
    'chaos_pack_gate', 'build_chaos_pack_namespace',
]
