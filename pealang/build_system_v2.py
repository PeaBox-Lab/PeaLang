"""Phase 86: deterministic incremental build system for PeaLang projects.

This module is additive to the existing ``pea build`` command. It plans builds
from source digests and module imports, emits a deterministic rebuild order and
dirty set, and keeps all evidence free of wall-clock values and absolute host
paths. It reports a plan; it does not package or modify project source.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

BUILD_SYSTEM_V2_VERSION = '3.1.49'
BUILD_SYSTEM_V2_FORMAT = 'pea-build-v2'
BUILD_V2_SKIP_DIRS = frozenset({
    '.git', '.venv', '__pycache__', '.pea_modules', '.pea_test_index', 'build',
})
IMPORT_RE = re.compile(r'^\s*import\s+"([^"]+)"')


class BuildSystemV2Error(Exception):
    """Raised when a build system v2 profile or state input is invalid."""


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class BuildProfileV2:
    """A validated, serializable incremental build profile."""

    max_files: int = 500
    include_tests: bool = False
    check_imports: bool = True
    fail_on_dirty: bool = False

    def __post_init__(self) -> None:
        if int(self.max_files) < 1:
            raise BuildSystemV2Error('max_files must be at least 1')

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return _digest(self.to_dict())


DEFAULT_BUILD_PROFILE = BuildProfileV2()


def build_system_v2_capabilities() -> dict[str, Any]:
    """Return the versioned incremental build capability set."""

    return {
        'version': BUILD_SYSTEM_V2_VERSION,
        'format': BUILD_SYSTEM_V2_FORMAT,
        'profile': DEFAULT_BUILD_PROFILE.to_dict(),
        'options': ['max_files', 'include_tests', 'check_imports',
                    'fail_on_dirty'],
        'source_filter': '*.pea',
        'dependency_source': 'import declarations',
        'stable_order': True,
        'wall_clock_excluded': True,
        'host_paths_excluded': True,
        'recomputed_gate': True,
    }


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _discover(root: Path, profile: BuildProfileV2) -> list[str]:
    paths: list[str] = []
    for path in root.rglob('*.pea'):
        parts = path.relative_to(root).parts
        if any(part in BUILD_V2_SKIP_DIRS for part in parts[:-1]):
            continue
        if not profile.include_tests and any(
                part in ('tests', 'test') for part in parts[:-1]):
            continue
        paths.append(_relative(path, root))
    return sorted(paths)


def _imports(text: str) -> tuple[str, ...]:
    found: set[str] = set()
    for line in text.splitlines():
        stripped = line.split('#', 1)[0].split('//', 1)[0].strip()
        match = IMPORT_RE.match(stripped)
        if match:
            found.add(match.group(1))
    return tuple(sorted(found))


def _candidates(name: str) -> tuple[str, ...]:
    parts = name.split('.')
    stem = '/'.join(parts)
    return (
        f'modules/{stem}.pea',
        f'modules/{stem}/__init__.pea',
        f'{stem}.pea',
        f'{stem}/__init__.pea',
    )


def _canonical_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    items = list(cycle[:-1] if cycle and cycle[-1] == cycle[0] else cycle)
    rotations = [tuple(items[index:] + items[:index])
                 for index in range(len(items))]
    return min(rotations)


@dataclass(frozen=True)
class BuildIssueV2:
    """One stable build-planning issue."""

    code: str
    severity: str
    message: str
    path: str

    def fingerprint(self) -> str:
        return _digest([
            self.code, self.severity, self.message, self.path,
        ])

    def to_dict(self) -> dict[str, Any]:
        return {
            'code': self.code,
            'severity': self.severity,
            'message': self.message,
            'path': self.path,
            'fingerprint': self.fingerprint(),
        }


@dataclass(frozen=True)
class BuildNodeV2:
    """One reviewed source node in an incremental build plan."""

    path: str
    digest: str
    imports: tuple[str, ...]
    dependencies: tuple[str, ...]
    state: str
    reasons: tuple[str, ...]

    def fingerprint(self) -> str:
        return _digest([
            self.path, self.digest, list(self.imports),
            list(self.dependencies), self.state, list(self.reasons),
        ])

    def to_dict(self) -> dict[str, Any]:
        return {
            'path': self.path,
            'digest': self.digest,
            'imports': list(self.imports),
            'dependencies': list(self.dependencies),
            'state': self.state,
            'reasons': list(self.reasons),
            'fingerprint': self.fingerprint(),
        }


def _decision(error_count: int, dirty_count: int,
              profile: BuildProfileV2) -> dict[str, Any]:
    issues: list[str] = []
    if error_count:
        issues.append('errors')
    if profile.fail_on_dirty and dirty_count:
        issues.append('dirty')
    return {'gate': 'FAIL' if issues else 'PASS', 'issues': issues}


@dataclass(frozen=True)
class BuildPlanV2:
    """Reviewable outcome of one incremental build plan."""

    version: str
    format: str
    profile: dict[str, Any]
    root_name: str
    nodes: tuple[BuildNodeV2, ...]
    build_order: tuple[str, ...]
    dirty: tuple[str, ...]
    issues: tuple[BuildIssueV2, ...]
    gate: str
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
            'format': self.format,
            'profile': self.profile,
            'root_name': self.root_name,
            'node_count': len(self.nodes),
            'clean_count': len(self.nodes) - len(self.dirty),
            'dirty_count': len(self.dirty),
            'error_count': len(self.issues),
            'nodes': [item.to_dict() for item in self.nodes],
            'build_order': list(self.build_order),
            'dirty': list(self.dirty),
            'issues': [item.to_dict() for item in self.issues],
            'gate': self.gate,
            'digest': self.digest,
        }


def plan_build_v2(root: str | Path, profile: BuildProfileV2 | None = None,
                  state: dict[str, str] | None = None) -> BuildPlanV2:
    """Plan an incremental build from source digests and import edges."""

    base = Path(root)
    if not base.is_dir():
        raise BuildSystemV2Error('root must be a directory')
    active = profile or DEFAULT_BUILD_PROFILE
    previous = state or {}
    if not isinstance(previous, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in previous.items()):
        raise BuildSystemV2Error('state must map paths to digests')
    paths = _discover(base, active)
    issues: list[BuildIssueV2] = []
    if len(paths) > active.max_files:
        issues.append(BuildIssueV2(
            'B203', 'error',
            f'Build has {len(paths)} files, exceeding limit {active.max_files}',
            '.',
        ))

    digests: dict[str, str] = {}
    imports: dict[str, tuple[str, ...]] = {}
    dependencies: dict[str, tuple[str, ...]] = {}
    source_set = set(paths)
    for path in paths:
        data = (base / path).read_bytes()
        digests[path] = hashlib.sha256(data).hexdigest()
        names = _imports(data.decode('utf-8', errors='replace'))
        imports[path] = names
        resolved: list[str] = []
        for name in names:
            candidates = [candidate for candidate in _candidates(name)
                          if candidate in source_set]
            if candidates:
                resolved.append(sorted(candidates)[0])
            elif active.check_imports:
                issues.append(BuildIssueV2(
                    'B201', 'error',
                    f"Module '{name}' imported by '{path}' is not present",
                    path,
                ))
        dependencies[path] = tuple(sorted(set(resolved)))

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
        issues.append(BuildIssueV2(
            'B202', 'error',
            'Dependency cycle: ' + ' -> '.join(cycle + (cycle[0],)),
            cycle[0],
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
    stale = {
        path for path in paths
        if previous.get(path) != digests[path]
    }
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
    nodes = tuple(
        BuildNodeV2(
            path=path,
            digest=digests[path],
            imports=imports[path],
            dependencies=dependencies[path],
            state='stale' if path in stale else 'current',
            reasons=tuple(sorted(set(reasons[path]))),
        )
        for path in paths
    )
    dirty = tuple(path for path in paths if path in stale)
    ordered_issues = tuple(sorted(
        issues, key=lambda item: (item.code, item.path, item.message),
    ))
    gate = _decision(len(ordered_issues), len(dirty), active)['gate']
    payload = {
        'version': BUILD_SYSTEM_V2_VERSION,
        'format': BUILD_SYSTEM_V2_FORMAT,
        'profile': active.digest(),
        'nodes': [item.fingerprint() for item in nodes],
        'build_order': order,
        'dirty': list(dirty),
        'issues': [item.fingerprint() for item in ordered_issues],
        'gate': gate,
    }
    return BuildPlanV2(
        version=BUILD_SYSTEM_V2_VERSION,
        format=BUILD_SYSTEM_V2_FORMAT,
        profile=active.to_dict(),
        root_name=base.resolve().name,
        nodes=nodes,
        build_order=tuple(order),
        dirty=dirty,
        issues=ordered_issues,
        gate=gate,
        digest=_digest(payload),
    )


def load_build_state_v2(path: str | Path) -> dict[str, str]:
    """Load a versioned build state file, returning an empty state if absent."""

    target = Path(path)
    if not target.is_file():
        return {}
    try:
        data = json.loads(target.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise BuildSystemV2Error('build state is not valid JSON') from exc
    if data.get('version') != BUILD_SYSTEM_V2_VERSION:
        raise BuildSystemV2Error('build state version does not match')
    state = data.get('state', {})
    if not isinstance(state, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in state.items()):
        raise BuildSystemV2Error('build state must map paths to digests')
    return dict(state)


def write_build_state_v2(root: str | Path, plan: BuildPlanV2,
                         path: str | Path | None = None) -> Path:
    """Persist a deterministic build state from an accepted plan."""

    target = Path(path) if path is not None else Path(root) / '.pea_build_v2.json'
    payload = {
        'version': BUILD_SYSTEM_V2_VERSION,
        'format': BUILD_SYSTEM_V2_FORMAT,
        'state': {node.path: node.digest for node in plan.nodes},
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


def _node_fingerprint(item: dict[str, Any]) -> str:
    return _digest([
        item.get('path'), item.get('digest'), list(item.get('imports', [])),
        list(item.get('dependencies', [])), item.get('state'),
        list(item.get('reasons', [])),
    ])


def _plan_digest(item: dict[str, Any]) -> str:
    return _digest({
        'version': item.get('version'),
        'format': item.get('format'),
        'profile': _digest(item.get('profile', {})),
        'nodes': [node.get('fingerprint') for node in item.get('nodes', [])],
        'build_order': item.get('build_order', []),
        'dirty': item.get('dirty', []),
        'issues': [issue.get('fingerprint')
                   for issue in item.get('issues', [])],
        'gate': item.get('gate'),
    })


def _report_digest(report: dict[str, Any]) -> str:
    return _digest({
        'version': report.get('version'),
        'format': report.get('format'),
        'profile_digest': report.get('profile_digest'),
        'plan_count': report.get('plan_count'),
        'node_count': report.get('node_count'),
        'clean_count': report.get('clean_count'),
        'dirty_count': report.get('dirty_count'),
        'error_count': report.get('error_count'),
        'plans': [
            {
                'node_count': item.get('node_count'),
                'dirty_count': item.get('dirty_count'),
                'error_count': item.get('error_count'),
                'gate': item.get('gate'),
                'digest': item.get('digest'),
            }
            for item in report.get('plans', [])
        ],
        'gate': report.get('gate'),
    })


def build_v2_report(plans: Iterable[BuildPlanV2],
                    profile: BuildProfileV2 | None = None) -> dict[str, Any]:
    """Summarize incremental build plans with a recomputable digest."""

    active = profile or DEFAULT_BUILD_PROFILE
    items = list(plans)
    node_count = sum(len(item.nodes) for item in items)
    dirty_count = sum(len(item.dirty) for item in items)
    error_count = sum(len(item.issues) for item in items)
    payload: dict[str, Any] = {
        'version': BUILD_SYSTEM_V2_VERSION,
        'format': BUILD_SYSTEM_V2_FORMAT,
        'profile': active.to_dict(),
        'profile_digest': active.digest(),
        'plan_count': len(items),
        'node_count': node_count,
        'clean_count': node_count - dirty_count,
        'dirty_count': dirty_count,
        'error_count': error_count,
        'plans': [item.to_dict() for item in items],
        'gate': _decision(error_count, dirty_count, active)['gate'],
    }
    payload['digest'] = _report_digest(payload)
    return payload


def build_v2_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute a deterministic PASS/FAIL decision from a build report."""

    issues: list[str] = []
    if report.get('version') != BUILD_SYSTEM_V2_VERSION:
        issues.append('version')
    if report.get('format') != BUILD_SYSTEM_V2_FORMAT:
        issues.append('format')
    if report.get('gate') not in ('PASS', 'FAIL'):
        issues.append('report')
    digest = str(report.get('digest', ''))
    if len(digest) != 64 or digest != _report_digest(report):
        issues.append('digest')
    node_count = int(report.get('node_count', 0))
    dirty_count = int(report.get('dirty_count', 0))
    error_count = int(report.get('error_count', 0))
    clean_count = int(report.get('clean_count', 0))
    if node_count != clean_count + dirty_count:
        issues.append('counts')
    for item in report.get('plans', []):
        item_digest = str(item.get('digest', ''))
        if len(item_digest) != 64 or item_digest != _plan_digest(item):
            issues.append('plan_digest')
        if int(item.get('node_count', 0)) != (
                int(item.get('clean_count', 0))
                + int(item.get('dirty_count', 0))):
            issues.append('plan_counts')
        for node in item.get('nodes', []):
            fingerprint = str(node.get('fingerprint', ''))
            if len(fingerprint) != 64 or fingerprint != _node_fingerprint(node):
                issues.append('node_fingerprint')
        for issue_item in item.get('issues', []):
            fingerprint = str(issue_item.get('fingerprint', ''))
            if (len(fingerprint) != 64
                    or fingerprint != _issue_fingerprint(issue_item)):
                issues.append('issue_fingerprint')
    profile_data = report.get('profile') or DEFAULT_BUILD_PROFILE.to_dict()
    try:
        profile = BuildProfileV2(**profile_data)
    except Exception:
        issues.append('profile')
        profile = DEFAULT_BUILD_PROFILE
    expected = _decision(error_count, dirty_count, profile)
    if report.get('gate') != expected['gate']:
        issues.append('gate')
    issues.extend(expected['issues'])
    return {'gate': 'PASS' if not issues else 'FAIL',
            'issues': sorted(set(issues))}


def build_build_system_v2_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'BUILD_SYSTEM_V2_VERSION': BUILD_SYSTEM_V2_VERSION,
        'BUILD_SYSTEM_V2_FORMAT': BUILD_SYSTEM_V2_FORMAT,
        'BuildProfileV2': BuildProfileV2,
        'DEFAULT_BUILD_PROFILE': DEFAULT_BUILD_PROFILE,
        'BuildIssueV2': BuildIssueV2,
        'BuildNodeV2': BuildNodeV2,
        'BuildPlanV2': BuildPlanV2,
        'BuildSystemV2Error': BuildSystemV2Error,
        'plan_build_v2': plan_build_v2,
        'load_build_state_v2': load_build_state_v2,
        'write_build_state_v2': write_build_state_v2,
        'build_system_v2_capabilities': build_system_v2_capabilities,
        'build_v2_report': build_v2_report,
        'build_v2_gate': build_v2_gate,
        'build_build_system_v2_namespace': build_build_system_v2_namespace,
    }


__all__ = [
    'BUILD_SYSTEM_V2_VERSION', 'BUILD_SYSTEM_V2_FORMAT',
    'BUILD_V2_SKIP_DIRS', 'BuildProfileV2', 'DEFAULT_BUILD_PROFILE',
    'BuildIssueV2', 'BuildNodeV2', 'BuildPlanV2', 'BuildSystemV2Error',
    'plan_build_v2', 'load_build_state_v2', 'write_build_state_v2',
    'build_system_v2_capabilities', 'build_v2_report', 'build_v2_gate',
    'build_build_system_v2_namespace',
]
