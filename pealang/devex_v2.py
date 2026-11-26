"""Phase 90: deterministic developer-experience evidence for PeaLang projects.

This module is a Wave 3 capstone. It inventories developer-tool evidence
manifests, validates their dependency graph and evidence contracts, and reports
a deterministic tool order and incomplete set. All evidence is free of
wall-clock values and absolute host paths. It reports a plan; it does not
create or modify project files.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

DEVEX_V2_VERSION = '3.1.53'
DEVEX_V2_FORMAT = 'pea-devx-v2'
DEVEX_V2_SKIP_DIRS = frozenset({
    '.git', '.venv', '__pycache__', '.pea_modules', '.pea_test_index', 'build',
    'node_modules', 'dist',
})
DEVEX_V2_EXPERIMENTAL_DIRS = frozenset({
    'experimental', 'preview', 'incubator',
})
DEVEX_NAME_RE = re.compile(r'^[a-z][a-z0-9_-]*$')


class DevExV2Error(Exception):
    """Raised when a DevEx profile, manifest, or state input is invalid."""


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class DevExProfileV2:
    """A validated, serializable developer-experience profile."""

    max_tools: int = 500
    include_experimental: bool = False
    check_evidence: bool = True
    fail_on_incomplete: bool = False
    current_version: str = ''

    def __post_init__(self) -> None:
        if int(self.max_tools) < 1:
            raise DevExV2Error('max_tools must be at least 1')
        if not isinstance(self.current_version, str):
            raise DevExV2Error('current_version must be a string')

    def effective_version(self) -> str:
        return self.current_version or DEVEX_V2_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return _digest(self.to_dict())


DEFAULT_DEVEX_PROFILE = DevExProfileV2()


def devex_v2_capabilities() -> dict[str, Any]:
    """Return the versioned developer-experience capability set."""

    return {
        'version': DEVEX_V2_VERSION,
        'format': DEVEX_V2_FORMAT,
        'profile': DEFAULT_DEVEX_PROFILE.to_dict(),
        'options': ['max_tools', 'include_experimental', 'check_evidence',
                    'fail_on_incomplete', 'current_version'],
        'source_filter': '*.devx.json',
        'stable_order': True,
        'wall_clock_excluded': True,
        'host_paths_excluded': True,
        'recomputed_gate': True,
    }


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _discover(root: Path, profile: DevExProfileV2) -> list[str]:
    paths: list[str] = []
    for path in root.rglob('*.devx.json'):
        parts = path.relative_to(root).parts
        if any(part in DEVEX_V2_SKIP_DIRS for part in parts[:-1]):
            continue
        if (not profile.include_experimental
                and any(part in DEVEX_V2_EXPERIMENTAL_DIRS
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
    tool_format = data.get('format', '')
    evidence = data.get('evidence')
    requires = data.get('requires', [])
    checks = data.get('checks', [])
    if not isinstance(name, str) or not DEVEX_NAME_RE.match(name):
        return None
    if not isinstance(version, str) or not isinstance(tool_format, str):
        return None
    if (not isinstance(evidence, list) or not evidence
            or not all(isinstance(item, str) and item for item in evidence)):
        return None
    if not isinstance(requires, list) or not all(
            isinstance(item, str) for item in requires):
        return None
    if not isinstance(checks, list) or not all(
            isinstance(item, str) for item in checks):
        return None
    return {
        'name': name,
        'version': version,
        'format': tool_format,
        'evidence': tuple(sorted(set(evidence))),
        'requires': tuple(sorted(set(requires))),
        'checks': tuple(sorted(set(checks))),
    }


def _canonical_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    items = list(cycle[:-1] if cycle and cycle[-1] == cycle[0] else cycle)
    rotations = [tuple(items[index:] + items[:index])
                 for index in range(len(items))]
    return min(rotations)


@dataclass(frozen=True)
class DevExIssueV2:
    """One stable developer-experience issue."""

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
class DevExToolV2:
    """One reviewed developer-tool node in a DevEx plan."""

    path: str
    digest: str
    name: str
    version: str
    format: str
    evidence: tuple[str, ...]
    requires: tuple[str, ...]
    checks: tuple[str, ...]
    dependencies: tuple[str, ...]
    state: str
    reasons: tuple[str, ...]

    def fingerprint(self) -> str:
        return _digest([
            self.path, self.digest, self.name, self.version, self.format,
            list(self.evidence), list(self.requires), list(self.checks),
            list(self.dependencies), self.state, list(self.reasons),
        ])

    def to_dict(self) -> dict[str, Any]:
        return {
            'path': self.path,
            'digest': self.digest,
            'name': self.name,
            'version': self.version,
            'format': self.format,
            'evidence': list(self.evidence),
            'requires': list(self.requires),
            'checks': list(self.checks),
            'dependencies': list(self.dependencies),
            'state': self.state,
            'reasons': list(self.reasons),
            'fingerprint': self.fingerprint(),
        }


def _decision(error_count: int, incomplete_count: int,
              profile: DevExProfileV2) -> dict[str, Any]:
    issues: list[str] = []
    if error_count:
        issues.append('errors')
    if profile.fail_on_incomplete and incomplete_count:
        issues.append('incomplete')
    return {'gate': 'FAIL' if issues else 'PASS', 'issues': issues}


@dataclass(frozen=True)
class DevExPlanV2:
    """Reviewable outcome of one developer-experience inventory."""

    version: str
    format: str
    profile: dict[str, Any]
    root_name: str
    tools: tuple[DevExToolV2, ...]
    build_order: tuple[str, ...]
    incomplete: tuple[str, ...]
    issues: tuple[DevExIssueV2, ...]
    gate: str
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
            'format': self.format,
            'profile': self.profile,
            'root_name': self.root_name,
            'tool_count': len(self.tools),
            'clean_count': len(self.tools) - len(self.incomplete),
            'incomplete_count': len(self.incomplete),
            'error_count': len(self.issues),
            'tools': [item.to_dict() for item in self.tools],
            'build_order': list(self.build_order),
            'incomplete': list(self.incomplete),
            'issues': [item.to_dict() for item in self.issues],
            'gate': self.gate,
            'digest': self.digest,
        }


def plan_devex_v2(root: str | Path, profile: DevExProfileV2 | None = None,
                  state: dict[str, str] | None = None) -> DevExPlanV2:
    """Inventory developer-tool evidence with stable, reviewable output."""

    base = Path(root)
    if not base.is_dir():
        raise DevExV2Error('root must be a directory')
    active = profile or DEFAULT_DEVEX_PROFILE
    previous = state or {}
    if not isinstance(previous, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in previous.items()):
        raise DevExV2Error('state must map paths to digests')
    paths = _discover(base, active)
    issues: list[DevExIssueV2] = []
    if len(paths) > active.max_tools:
        issues.append(DevExIssueV2(
            'D203', 'error',
            f'DevEx catalog has {len(paths)} tools, exceeding limit '
            f'{active.max_tools}',
            '.',
        ))

    digests: dict[str, str] = {}
    manifests: dict[str, dict[str, Any]] = {}
    for path in paths:
        data = (base / path).read_bytes()
        digests[path] = hashlib.sha256(data).hexdigest()
        manifest = _manifest(base, path)
        if manifest is None:
            issues.append(DevExIssueV2(
                'D204', 'error',
                f"DevEx manifest '{path}' is invalid",
                path,
            ))
            manifest = {
                'name': '', 'version': '', 'format': '', 'evidence': (),
                'requires': (), 'checks': (),
            }
        manifests[path] = manifest
        if active.check_evidence:
            for evidence in manifest['evidence']:
                if not (base / evidence).is_file():
                    issues.append(DevExIssueV2(
                        'D205', 'error',
                        f"Evidence '{evidence}' declared by '{path}' is missing",
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
            elif active.check_evidence:
                issues.append(DevExIssueV2(
                    'D201', 'error',
                    f"DevEx tool '{name}' required by '{path}' is not present",
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
        issues.append(DevExIssueV2(
            'D202', 'error',
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
    tools = tuple(
        DevExToolV2(
            path=path,
            digest=digests[path],
            name=manifests[path]['name'],
            version=manifests[path]['version'],
            format=manifests[path]['format'],
            evidence=manifests[path]['evidence'],
            requires=manifests[path]['requires'],
            checks=manifests[path]['checks'],
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
        'version': DEVEX_V2_VERSION,
        'format': DEVEX_V2_FORMAT,
        'profile': active.digest(),
        'tools': [item.fingerprint() for item in tools],
        'build_order': order,
        'incomplete': list(incomplete),
        'issues': [item.fingerprint() for item in ordered_issues],
        'gate': gate,
    }
    return DevExPlanV2(
        version=DEVEX_V2_VERSION,
        format=DEVEX_V2_FORMAT,
        profile=active.to_dict(),
        root_name=base.resolve().name,
        tools=tools,
        build_order=tuple(order),
        incomplete=incomplete,
        issues=ordered_issues,
        gate=gate,
        digest=_digest(payload),
    )


def load_devex_state_v2(path: str | Path) -> dict[str, str]:
    """Load versioned DevEx state, returning empty state when absent."""

    target = Path(path)
    if not target.is_file():
        return {}
    try:
        data = json.loads(target.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise DevExV2Error('DevEx state is not valid JSON') from exc
    if data.get('version') != DEVEX_V2_VERSION:
        raise DevExV2Error('DevEx state version does not match')
    state = data.get('state', {})
    if not isinstance(state, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in state.items()):
        raise DevExV2Error('DevEx state must map paths to digests')
    return dict(state)


def write_devex_state_v2(root: str | Path, plan: DevExPlanV2,
                         path: str | Path | None = None) -> Path:
    """Persist a deterministic developer-experience digest state."""

    target = Path(path) if path is not None else Path(root) / '.pea_devex_v2.json'
    payload = {
        'version': DEVEX_V2_VERSION,
        'format': DEVEX_V2_FORMAT,
        'state': {tool.path: tool.digest for tool in plan.tools},
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


def _tool_fingerprint(item: dict[str, Any]) -> str:
    return _digest([
        item.get('path'), item.get('digest'), item.get('name'),
        item.get('version'), item.get('format'),
        list(item.get('evidence', [])), list(item.get('requires', [])),
        list(item.get('checks', [])), list(item.get('dependencies', [])),
        item.get('state'), list(item.get('reasons', [])),
    ])


def _plan_digest(item: dict[str, Any]) -> str:
    return _digest({
        'version': item.get('version'),
        'format': item.get('format'),
        'profile': _digest(item.get('profile', {})),
        'tools': [tool.get('fingerprint') for tool in item.get('tools', [])],
        'build_order': item.get('build_order', []),
        'incomplete': item.get('incomplete', []),
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
        'tool_count': report.get('tool_count'),
        'clean_count': report.get('clean_count'),
        'incomplete_count': report.get('incomplete_count'),
        'error_count': report.get('error_count'),
        'plans': [
            {
                'tool_count': item.get('tool_count'),
                'incomplete_count': item.get('incomplete_count'),
                'error_count': item.get('error_count'),
                'gate': item.get('gate'),
                'digest': item.get('digest'),
            }
            for item in report.get('plans', [])
        ],
        'gate': report.get('gate'),
    })


def devex_v2_report(plans: Iterable[DevExPlanV2],
                    profile: DevExProfileV2 | None = None) -> dict[str, Any]:
    """Summarize DevEx plans with a recomputable digest."""

    active = profile or DEFAULT_DEVEX_PROFILE
    items = list(plans)
    tool_count = sum(len(item.tools) for item in items)
    incomplete_count = sum(len(item.incomplete) for item in items)
    error_count = sum(len(item.issues) for item in items)
    payload: dict[str, Any] = {
        'version': DEVEX_V2_VERSION,
        'format': DEVEX_V2_FORMAT,
        'profile': active.to_dict(),
        'profile_digest': active.digest(),
        'plan_count': len(items),
        'tool_count': tool_count,
        'clean_count': tool_count - incomplete_count,
        'incomplete_count': incomplete_count,
        'error_count': error_count,
        'plans': [item.to_dict() for item in items],
        'gate': _decision(error_count, incomplete_count, active)['gate'],
    }
    payload['digest'] = _report_digest(payload)
    return payload


def devex_v2_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute a deterministic PASS/FAIL decision from a DevEx report."""

    issues: list[str] = []
    if report.get('version') != DEVEX_V2_VERSION:
        issues.append('version')
    if report.get('format') != DEVEX_V2_FORMAT:
        issues.append('format')
    if report.get('gate') not in ('PASS', 'FAIL'):
        issues.append('report')
    digest = str(report.get('digest', ''))
    if len(digest) != 64 or digest != _report_digest(report):
        issues.append('digest')
    tool_count = int(report.get('tool_count', 0))
    incomplete_count = int(report.get('incomplete_count', 0))
    error_count = int(report.get('error_count', 0))
    clean_count = int(report.get('clean_count', 0))
    if tool_count != clean_count + incomplete_count:
        issues.append('counts')
    for item in report.get('plans', []):
        item_digest = str(item.get('digest', ''))
        if len(item_digest) != 64 or item_digest != _plan_digest(item):
            issues.append('plan_digest')
        if int(item.get('tool_count', 0)) != (
                int(item.get('clean_count', 0))
                + int(item.get('incomplete_count', 0))):
            issues.append('plan_counts')
        for tool in item.get('tools', []):
            fingerprint = str(tool.get('fingerprint', ''))
            if (len(fingerprint) != 64
                    or fingerprint != _tool_fingerprint(tool)):
                issues.append('tool_fingerprint')
        for issue_item in item.get('issues', []):
            fingerprint = str(issue_item.get('fingerprint', ''))
            if (len(fingerprint) != 64
                    or fingerprint != _issue_fingerprint(issue_item)):
                issues.append('issue_fingerprint')
    profile_data = report.get('profile') or DEFAULT_DEVEX_PROFILE.to_dict()
    try:
        profile = DevExProfileV2(**profile_data)
    except Exception:
        issues.append('profile')
        profile = DEFAULT_DEVEX_PROFILE
    expected = _decision(error_count, incomplete_count, profile)
    if report.get('gate') != expected['gate']:
        issues.append('gate')
    issues.extend(expected['issues'])
    return {'gate': 'PASS' if not issues else 'FAIL',
            'issues': sorted(set(issues))}


def build_devex_v2_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'DEVEX_V2_VERSION': DEVEX_V2_VERSION,
        'DEVEX_V2_FORMAT': DEVEX_V2_FORMAT,
        'DEVEX_V2_SKIP_DIRS': DEVEX_V2_SKIP_DIRS,
        'DEVEX_V2_EXPERIMENTAL_DIRS': DEVEX_V2_EXPERIMENTAL_DIRS,
        'DevExProfileV2': DevExProfileV2,
        'DEFAULT_DEVEX_PROFILE': DEFAULT_DEVEX_PROFILE,
        'DevExIssueV2': DevExIssueV2,
        'DevExToolV2': DevExToolV2,
        'DevExPlanV2': DevExPlanV2,
        'DevExV2Error': DevExV2Error,
        'plan_devex_v2': plan_devex_v2,
        'load_devex_state_v2': load_devex_state_v2,
        'write_devex_state_v2': write_devex_state_v2,
        'devex_v2_capabilities': devex_v2_capabilities,
        'devex_v2_report': devex_v2_report,
        'devex_v2_gate': devex_v2_gate,
        'build_devex_v2_namespace': build_devex_v2_namespace,
    }


__all__ = [
    'DEVEX_V2_VERSION', 'DEVEX_V2_FORMAT', 'DEVEX_V2_SKIP_DIRS',
    'DEVEX_V2_EXPERIMENTAL_DIRS', 'DevExProfileV2', 'DEFAULT_DEVEX_PROFILE',
    'DevExV2Error', 'DevExIssueV2', 'DevExToolV2', 'DevExPlanV2',
    'plan_devex_v2', 'load_devex_state_v2', 'write_devex_state_v2',
    'devex_v2_capabilities', 'devex_v2_report', 'devex_v2_gate',
    'build_devex_v2_namespace',
]
