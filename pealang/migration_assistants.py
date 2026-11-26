"""Phase 88: deterministic migration assistants for PeaLang projects.

This module is additive to the existing ``pea migrate`` command. It plans
migrations from source digests and migration scripts, emits a deterministic
migration order and migration set, and keeps all evidence free of wall-clock
values and absolute host paths. It reports a plan; it does not execute or modify
project source.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

MIGRATION_ASSISTANTS_VERSION = '3.1.51'
MIGRATION_ASSISTANTS_FORMAT = 'pea-migrate-v2'
MIGRATION_ASSISTANTS_SKIP_DIRS = frozenset({
    '.git', '.venv', '__pycache__', '.pea_modules', '.pea_test_index', 'build',
    'node_modules', 'dist',
})
MIGRATION_ASSISTANTS_HISTORY_DIRS = frozenset({
    'releases', 'history', 'archive', 'retention',
})
MIGRATION_IMPORT_RE = re.compile(r'^\s*import\s+"([^"]+)"')
MIGRATION_SCRIPT_RE = re.compile(r'\bdef\s+(\w+)\s*\(')


class MigrationAssistantError(Exception):
    """Raised when a migration assistant profile or state input is invalid."""


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class MigrationProfileV2:
    """A validated, serializable migration assistant profile."""

    max_migrations: int = 500
    include_test_migrations: bool = False
    check_imports: bool = True
    fail_on_dirty: bool = False
    current_version: str = ''

    def __post_init__(self) -> None:
        if int(self.max_migrations) < 1:
            raise MigrationAssistantError('max_migrations must be at least 1')
        if not isinstance(self.current_version, str):
            raise MigrationAssistantError('current_version must be a string')

    def effective_version(self) -> str:
        return self.current_version or MIGRATION_ASSISTANTS_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return _digest(self.to_dict())


DEFAULT_MIGRATION_PROFILE = MigrationProfileV2()


def migration_assistants_capabilities() -> dict[str, Any]:
    """Return the versioned migration assistant capability set."""

    return {
        'version': MIGRATION_ASSISTANTS_VERSION,
        'format': MIGRATION_ASSISTANTS_FORMAT,
        'profile': DEFAULT_MIGRATION_PROFILE.to_dict(),
        'options': ['max_migrations', 'include_test_migrations', 'check_imports',
                    'fail_on_dirty', 'current_version'],
        'source_filter': '*.migration',
        'stable_order': True,
        'wall_clock_excluded': True,
        'host_paths_excluded': True,
        'recomputed_gate': True,
    }


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _discover(root: Path, profile: MigrationProfileV2) -> list[str]:
    paths: list[str] = []
    for path in root.rglob('*.migration'):
        parts = path.relative_to(root).parts
        if any(part in MIGRATION_ASSISTANTS_SKIP_DIRS for part in parts[:-1]):
            continue
        if (not profile.include_test_migrations
                and any(part in MIGRATION_ASSISTANTS_HISTORY_DIRS
                        for part in parts[:-1])):
            continue
        paths.append(_relative(path, root))
    return sorted(paths)


def _imports(text: str) -> tuple[str, ...]:
    found: set[str] = set()
    for line in text.splitlines():
        stripped = line.split('#', 1)[0].split('//', 1)[0].strip()
        match = MIGRATION_IMPORT_RE.match(stripped)
        if match:
            found.add(match.group(1))
    return tuple(sorted(found))


def _scripts(text: str) -> tuple[str, ...]:
    found: set[str] = set()
    for line in text.splitlines():
        stripped = line.split('#', 1)[0].split('//', 1)[0].strip()
        match = MIGRATION_SCRIPT_RE.match(stripped)
        if match:
            found.add(match.group(1))
    return tuple(sorted(found))


def _candidates(name: str) -> tuple[str, ...]:
    stem = name.replace('.', '/')
    return (f'migrations/{stem}.migration', f'{stem}.migration')


def _canonical_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    items = list(cycle[:-1] if cycle and cycle[-1] == cycle[0] else cycle)
    rotations = [tuple(items[index:] + items[:index])
                 for index in range(len(items))]
    return min(rotations)


@dataclass(frozen=True)
class MigrationIssueV2:
    """One stable migration-assistant issue."""

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
class MigrationNodeV2:
    """One reviewed migration node in a migration assistant plan."""

    path: str
    digest: str
    imports: tuple[str, ...]
    scripts: tuple[str, ...]
    dependencies: tuple[str, ...]
    state: str
    reasons: tuple[str, ...]

    def fingerprint(self) -> str:
        return _digest([
            self.path, self.digest, list(self.imports), list(self.scripts),
            list(self.dependencies), self.state, list(self.reasons),
        ])

    def to_dict(self) -> dict[str, Any]:
        return {
            'path': self.path,
            'digest': self.digest,
            'imports': list(self.imports),
            'scripts': list(self.scripts),
            'dependencies': list(self.dependencies),
            'state': self.state,
            'reasons': list(self.reasons),
            'fingerprint': self.fingerprint(),
        }


def _decision(error_count: int, dirty_count: int,
              profile: MigrationProfileV2) -> dict[str, Any]:
    issues: list[str] = []
    if error_count:
        issues.append('errors')
    if profile.fail_on_dirty and dirty_count:
        issues.append('dirty')
    return {'gate': 'FAIL' if issues else 'PASS', 'issues': issues}


@dataclass(frozen=True)
class MigrationPlanV2:
    """Reviewable outcome of one migration assistant plan."""

    version: str
    format: str
    profile: dict[str, Any]
    root_name: str
    nodes: tuple[MigrationNodeV2, ...]
    build_order: tuple[str, ...]
    dirty: tuple[str, ...]
    issues: tuple[MigrationIssueV2, ...]
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


def plan_migration_v2(root: str | Path, profile: MigrationProfileV2 | None = None,
                      state: dict[str, str] | None = None) -> MigrationPlanV2:
    """Plan an incremental migration from source digests and script edges."""

    base = Path(root)
    if not base.is_dir():
        raise MigrationAssistantError('root must be a directory')
    active = profile or DEFAULT_MIGRATION_PROFILE
    previous = state or {}
    if not isinstance(previous, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in previous.items()):
        raise MigrationAssistantError('state must map paths to digests')
    paths = _discover(base, active)
    issues: list[MigrationIssueV2] = []
    if len(paths) > active.max_migrations:
        issues.append(MigrationIssueV2(
            'M203', 'error',
            f'Migration has {len(paths)} migration files, exceeding limit '
            f'{active.max_migrations}',
            '.',
        ))

    digests: dict[str, str] = {}
    imports: dict[str, tuple[str, ...]] = {}
    scripts: dict[str, tuple[str, ...]] = {}
    dependencies: dict[str, tuple[str, ...]] = {}
    providers: dict[str, set[str]] = {}
    source_set = set(paths)
    for path in paths:
        data = (base / path).read_bytes()
        digests[path] = hashlib.sha256(data).hexdigest()
        text = data.decode('utf-8', errors='replace')
        imports[path] = _imports(text)
        scripts[path] = _scripts(text)
        for name in scripts[path]:
            providers.setdefault(name, set()).add(path)
    for path in paths:
        resolved: set[str] = set()
        for name in imports[path]:
            candidates = {
                candidate for candidate in _candidates(name)
                if candidate in source_set
            }
            candidates.update(providers.get(name, set()))
            if candidates:
                resolved.update(candidates)
            elif active.check_imports:
                issues.append(MigrationIssueV2(
                    'M201', 'error',
                    f"Migration script '{name}' imported by '{path}' is not present",
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
        issues.append(MigrationIssueV2(
            'M202', 'error',
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
    nodes = tuple(
        MigrationNodeV2(
            path=path,
            digest=digests[path],
            imports=imports[path],
            scripts=scripts[path],
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
        'version': MIGRATION_ASSISTANTS_VERSION,
        'format': MIGRATION_ASSISTANTS_FORMAT,
        'profile': active.digest(),
        'nodes': [item.fingerprint() for item in nodes],
        'build_order': order,
        'dirty': list(dirty),
        'issues': [item.fingerprint() for item in ordered_issues],
        'gate': gate,
    }
    return MigrationPlanV2(
        version=MIGRATION_ASSISTANTS_VERSION,
        format=MIGRATION_ASSISTANTS_FORMAT,
        profile=active.to_dict(),
        root_name=base.resolve().name,
        nodes=nodes,
        build_order=tuple(order),
        dirty=dirty,
        issues=ordered_issues,
        gate=gate,
        digest=_digest(payload),
    )


def load_migration_state_v2(path: str | Path) -> dict[str, str]:
    """Load versioned migration state, returning empty state when absent."""

    target = Path(path)
    if not target.is_file():
        return {}
    try:
        data = json.loads(target.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise MigrationAssistantError('migration state is not valid JSON') from exc
    if data.get('version') != MIGRATION_ASSISTANTS_VERSION:
        raise MigrationAssistantError('migration state version does not match')
    state = data.get('state', {})
    if not isinstance(state, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in state.items()):
        raise MigrationAssistantError('migration state must map paths to digests')
    return dict(state)


def write_migration_state_v2(root: str | Path, plan: MigrationPlanV2,
                             path: str | Path | None = None) -> Path:
    """Persist a deterministic migration digest state."""

    target = Path(path) if path is not None else Path(root) / '.pea_migrate_v2.json'
    payload = {
        'version': MIGRATION_ASSISTANTS_VERSION,
        'format': MIGRATION_ASSISTANTS_FORMAT,
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
        list(item.get('scripts', [])), list(item.get('dependencies', [])),
        item.get('state'), list(item.get('reasons', [])),
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


def migration_v2_report(plans: Iterable[MigrationPlanV2],
                        profile: MigrationProfileV2 | None = None) -> dict[str, Any]:
    """Summarize migration assistant plans with a recomputable digest."""

    active = profile or DEFAULT_MIGRATION_PROFILE
    items = list(plans)
    node_count = sum(len(item.nodes) for item in items)
    dirty_count = sum(len(item.dirty) for item in items)
    error_count = sum(len(item.issues) for item in items)
    payload: dict[str, Any] = {
        'version': MIGRATION_ASSISTANTS_VERSION,
        'format': MIGRATION_ASSISTANTS_FORMAT,
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


def migration_v2_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute a deterministic PASS/FAIL decision from a migration report."""

    issues: list[str] = []
    if report.get('version') != MIGRATION_ASSISTANTS_VERSION:
        issues.append('version')
    if report.get('format') != MIGRATION_ASSISTANTS_FORMAT:
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
            if (len(fingerprint) != 64
                    or fingerprint != _node_fingerprint(node)):
                issues.append('node_fingerprint')
        for issue_item in item.get('issues', []):
            fingerprint = str(issue_item.get('fingerprint', ''))
            if (len(fingerprint) != 64
                    or fingerprint != _issue_fingerprint(issue_item)):
                issues.append('issue_fingerprint')
    profile_data = report.get('profile') or DEFAULT_MIGRATION_PROFILE.to_dict()
    try:
        profile = MigrationProfileV2(**profile_data)
    except Exception:
        issues.append('profile')
        profile = DEFAULT_MIGRATION_PROFILE
    expected = _decision(error_count, dirty_count, profile)
    if report.get('gate') != expected['gate']:
        issues.append('gate')
    issues.extend(expected['issues'])
    return {'gate': 'PASS' if not issues else 'FAIL',
            'issues': sorted(set(issues))}


def build_migration_assistants_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'MIGRATION_ASSISTANTS_VERSION': MIGRATION_ASSISTANTS_VERSION,
        'MIGRATION_ASSISTANTS_FORMAT': MIGRATION_ASSISTANTS_FORMAT,
        'MIGRATION_ASSISTANTS_SKIP_DIRS': MIGRATION_ASSISTANTS_SKIP_DIRS,
        'MIGRATION_ASSISTANTS_HISTORY_DIRS': MIGRATION_ASSISTANTS_HISTORY_DIRS,
        'MigrationProfileV2': MigrationProfileV2,
        'DEFAULT_MIGRATION_PROFILE': DEFAULT_MIGRATION_PROFILE,
        'MigrationIssueV2': MigrationIssueV2,
        'MigrationNodeV2': MigrationNodeV2,
        'MigrationPlanV2': MigrationPlanV2,
        'MigrationAssistantError': MigrationAssistantError,
        'plan_migration_v2': plan_migration_v2,
        'load_migration_state_v2': load_migration_state_v2,
        'write_migration_state_v2': write_migration_state_v2,
        'migration_assistants_capabilities': migration_assistants_capabilities,
        'migration_v2_report': migration_v2_report,
        'migration_v2_gate': migration_v2_gate,
        'build_migration_assistants_namespace': build_migration_assistants_namespace,
    }


__all__ = [
    'MIGRATION_ASSISTANTS_VERSION', 'MIGRATION_ASSISTANTS_FORMAT',
    'MIGRATION_ASSISTANTS_SKIP_DIRS', 'MIGRATION_ASSISTANTS_HISTORY_DIRS',
    'MigrationProfileV2', 'DEFAULT_MIGRATION_PROFILE',
    'MigrationAssistantError', 'MigrationIssueV2', 'MigrationNodeV2',
    'MigrationPlanV2', 'plan_migration_v2', 'load_migration_state_v2',
    'write_migration_state_v2', 'migration_assistants_capabilities',
    'migration_v2_report', 'migration_v2_gate',
    'build_migration_assistants_namespace',
]
