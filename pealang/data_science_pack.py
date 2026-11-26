"""Phase 92: deterministic Data Science / AI / ML sector-pack evidence.

This module continues Wave 4 with a focused sector pack for governed data,
analytics, and ML workflows. It inventories workflow manifests, validates their
dependency graph and governance contracts, and reports a deterministic workflow
order and incomplete set. All evidence is free of wall-clock values and absolute
host paths. It reports a plan; it does not create or modify project files.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

DATA_PACK_VERSION = '3.1.55'
DATA_PACK_FORMAT = 'pea-ds-pack'
DATA_PACK_SKIP_DIRS = frozenset({
    '.git', '.venv', '__pycache__', '.pea_modules', '.pea_test_index', 'build',
    'node_modules', 'dist',
})
DATA_PACK_PREVIEW_DIRS = frozenset({'preview', 'experimental', 'incubator'})
DATA_KINDS = frozenset({
    'dataset', 'pipeline', 'benchmark', 'model', 'parity-suite',
    'serving-endpoint',
})
DATA_NAME_RE = re.compile(r'^[a-z][a-z0-9_-]*$')


class DataPackError(Exception):
    """Raised when a data profile, manifest, or state input is invalid."""
    pass


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class DataProfileV2:
    """A validated, serializable data science sector-pack profile."""

    max_workflows: int = 500
    include_preview: bool = False
    check_parity: bool = True
    check_benchmarks: bool = True
    fail_on_incomplete: bool = False
    current_version: str = ''

    def __post_init__(self) -> None:
        if int(self.max_workflows) < 1:
            raise DataPackError('max_workflows must be at least 1')
        if not isinstance(self.current_version, str):
            raise DataPackError('current_version must be a string')

    def effective_version(self) -> str:
        return self.current_version or DATA_PACK_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return _digest(self.to_dict())


DEFAULT_DATA_PROFILE = DataProfileV2()


def data_pack_capabilities() -> dict[str, Any]:
    """Return the versioned data science sector-pack capability set."""

    return {
        'version': DATA_PACK_VERSION,
        'format': DATA_PACK_FORMAT,
        'profile': DEFAULT_DATA_PROFILE.to_dict(),
        'options': ['max_workflows', 'include_preview', 'check_parity',
                    'check_benchmarks', 'fail_on_incomplete', 'current_version'],
        'source_filter': '*.ds.json',
        'kinds': sorted(DATA_KINDS),
        'stable_order': True,
        'wall_clock_excluded': True,
        'host_paths_excluded': True,
        'recomputed_gate': True,
    }


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _discover(root: Path, profile: DataProfileV2) -> list[str]:
    paths: list[str] = []
    for path in root.rglob('*.ds.json'):
        parts = path.relative_to(root).parts
        if any(part in DATA_PACK_SKIP_DIRS for part in parts[:-1]):
            continue
        if (not profile.include_preview
                and any(part in DATA_PACK_PREVIEW_DIRS
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
    metrics = data.get('metrics', [])
    if not isinstance(name, str) or not DATA_NAME_RE.match(name):
        return None
    if not isinstance(version, str) or not isinstance(kind, str):
        return None
    if kind not in DATA_KINDS:
        return None
    if (not isinstance(evidence, list) or not evidence
            or not all(isinstance(item, str) and item for item in evidence)):
        return None
    if not isinstance(requires, list) or not all(
            isinstance(item, str) for item in requires):
        return None
    if not isinstance(metrics, list) or not all(
            isinstance(item, str) for item in metrics):
        return None
    return {
        'name': name,
        'version': version,
        'kind': kind,
        'evidence': tuple(sorted(set(evidence))),
        'requires': tuple(sorted(set(requires))),
        'metrics': tuple(sorted(set(metrics))),
    }


def _canonical_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    items = list(cycle[:-1] if cycle and cycle[-1] == cycle[0] else cycle)
    rotations = [tuple(items[index:] + items[:index])
                 for index in range(len(items))]
    return min(rotations)


@dataclass(frozen=True)
class DataIssueV2:
    """One stable data science sector-pack issue."""

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
class DataWorkflowV2:
    """One reviewed workflow node in a data science pack plan."""

    path: str
    digest: str
    name: str
    version: str
    kind: str
    evidence: tuple[str, ...]
    requires: tuple[str, ...]
    metrics: tuple[str, ...]
    dependencies: tuple[str, ...]
    state: str
    reasons: tuple[str, ...]

    def fingerprint(self) -> str:
        return _digest([
            self.path, self.digest, self.name, self.version, self.kind,
            list(self.evidence), list(self.requires), list(self.metrics),
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
            'metrics': list(self.metrics),
            'dependencies': list(self.dependencies),
            'state': self.state,
            'reasons': list(self.reasons),
            'fingerprint': self.fingerprint(),
        }


def _decision(error_count: int, incomplete_count: int,
              profile: DataProfileV2) -> dict[str, Any]:
    issues: list[str] = []
    if error_count:
        issues.append('errors')
    if profile.fail_on_incomplete and incomplete_count:
        issues.append('incomplete')
    return {'gate': 'FAIL' if issues else 'PASS', 'issues': issues}


@dataclass(frozen=True)
class DataPackPlanV2:
    """Reviewable outcome of one data science sector-pack inventory."""

    version: str
    format: str
    profile: dict[str, Any]
    root_name: str
    workflows: tuple[DataWorkflowV2, ...]
    build_order: tuple[str, ...]
    incomplete: tuple[str, ...]
    issues: tuple[DataIssueV2, ...]
    gate: str
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
            'format': self.format,
            'profile': self.profile,
            'root_name': self.root_name,
            'workflow_count': len(self.workflows),
            'clean_count': len(self.workflows) - len(self.incomplete),
            'incomplete_count': len(self.incomplete),
            'error_count': len(self.issues),
            'workflows': [item.to_dict() for item in self.workflows],
            'build_order': list(self.build_order),
            'incomplete': list(self.incomplete),
            'issues': [item.to_dict() for item in self.issues],
            'gate': self.gate,
            'digest': self.digest,
        }


def plan_data_pack(root: str | Path, profile: DataProfileV2 | None = None,
                   state: dict[str, str] | None = None) -> DataPackPlanV2:
    """Inventory data workflows with stable, reviewable output."""

    base = Path(root)
    if not base.is_dir():
        raise DataPackError('root must be a directory')
    active = profile or DEFAULT_DATA_PROFILE
    previous = state or {}
    if not isinstance(previous, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in previous.items()):
        raise DataPackError('state must map paths to digests')
    paths = _discover(base, active)
    issues: list[DataIssueV2] = []
    if len(paths) > active.max_workflows:
        issues.append(DataIssueV2(
            'S203', 'error',
            f'Data pack has {len(paths)} workflows, exceeding limit '
            f'{active.max_workflows}',
            '.',
        ))

    digests: dict[str, str] = {}
    manifests: dict[str, dict[str, Any]] = {}
    for path in paths:
        data = (base / path).read_bytes()
        digests[path] = hashlib.sha256(data).hexdigest()
        manifest = _manifest(base, path)
        if manifest is None:
            issues.append(DataIssueV2(
                'S204', 'error',
                f'Data workflow "{path}" is invalid',
                path,
            ))
            manifest = {
                'name': '', 'version': '', 'kind': '', 'evidence': (),
                'requires': (), 'metrics': (),
            }
        manifests[path] = manifest
        for evidence in manifest['evidence']:
            if not (base / evidence).is_file():
                issues.append(DataIssueV2(
                    'S205', 'error',
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
                issues.append(DataIssueV2(
                    'S201', 'error',
                    f'Data workflow "{name}" required by "{path}" is not present',
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
        issues.append(DataIssueV2(
            'S202', 'error',
            'Dependency cycle: ' + ' -> '.join(cycle + (cycle[0],)),
            cycle[0],
        ))

    parity_providers = {
        path for path, manifest in manifests.items()
        if manifest['kind'] == 'parity-suite'
    }
    if active.check_parity:
        for path, manifest in manifests.items():
            if (manifest['kind'] == 'pipeline'
                    and not parity_providers.intersection(dependencies[path])):
                issues.append(DataIssueV2(
                    'S206', 'error',
                    f'Pipeline "{path}" has no parity-suite dependency',
                    path,
                ))

    benchmark_providers = {
        path for path, manifest in manifests.items()
        if manifest['kind'] == 'benchmark'
    }
    if active.check_benchmarks:
        for path, manifest in manifests.items():
            if (manifest['kind'] == 'model'
                    and not benchmark_providers.intersection(dependencies[path])):
                issues.append(DataIssueV2(
                    'S207', 'error',
                    f'Model "{path}" has no published benchmark dependency',
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
    workflows = tuple(
        DataWorkflowV2(
            path=path,
            digest=digests[path],
            name=manifests[path]['name'],
            version=manifests[path]['version'],
            kind=manifests[path]['kind'],
            evidence=manifests[path]['evidence'],
            requires=manifests[path]['requires'],
            metrics=manifests[path]['metrics'],
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
        'version': DATA_PACK_VERSION,
        'format': DATA_PACK_FORMAT,
        'profile': active.digest(),
        'workflows': [item.fingerprint() for item in workflows],
        'build_order': order,
        'incomplete': list(incomplete),
        'issues': [item.fingerprint() for item in ordered_issues],
        'gate': gate,
    }
    return DataPackPlanV2(
        version=DATA_PACK_VERSION,
        format=DATA_PACK_FORMAT,
        profile=active.to_dict(),
        root_name=base.resolve().name,
        workflows=workflows,
        build_order=tuple(order),
        incomplete=incomplete,
        issues=ordered_issues,
        gate=gate,
        digest=_digest(payload),
    )


def load_data_state_v2(path: str | Path) -> dict[str, str]:
    """Load versioned data state, returning empty state when absent."""

    target = Path(path)
    if not target.is_file():
        return {}
    try:
        data = json.loads(target.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise DataPackError('Data state is not valid JSON') from exc
    if data.get('version') != DATA_PACK_VERSION:
        raise DataPackError('Data state version does not match')
    state = data.get('state', {})
    if not isinstance(state, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in state.items()):
        raise DataPackError('Data state must map paths to digests')
    return dict(state)


def write_data_state_v2(root: str | Path, plan: DataPackPlanV2,
                        path: str | Path | None = None) -> Path:
    """Persist a deterministic data sector-pack digest state."""

    target = (Path(path) if path is not None
              else Path(root) / '.pea_data_pack.json')
    payload = {
        'version': DATA_PACK_VERSION,
        'format': DATA_PACK_FORMAT,
        'state': {item.path: item.digest for item in plan.workflows},
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


def _workflow_fingerprint(item: dict[str, Any]) -> str:
    return _digest([
        item.get('path'), item.get('digest'), item.get('name'),
        item.get('version'), item.get('kind'),
        list(item.get('evidence', [])), list(item.get('requires', [])),
        list(item.get('metrics', [])), list(item.get('dependencies', [])),
        item.get('state'), list(item.get('reasons', [])),
    ])


def _plan_digest(item: dict[str, Any]) -> str:
    return _digest({
        'version': item.get('version'),
        'format': item.get('format'),
        'profile': _digest(item.get('profile', {})),
        'workflows': [x.get('fingerprint') for x in item.get('workflows', [])],
        'build_order': item.get('build_order', []),
        'incomplete': item.get('incomplete', []),
        'issues': [x.get('fingerprint') for x in item.get('issues', [])],
        'gate': item.get('gate'),
    })


def _report_digest(report: dict[str, Any]) -> str:
    return _digest({
        'version': report.get('version'),
        'format': report.get('format'),
        'profile_digest': report.get('profile_digest'),
        'plan_count': report.get('plan_count'),
        'workflow_count': report.get('workflow_count'),
        'clean_count': report.get('clean_count'),
        'incomplete_count': report.get('incomplete_count'),
        'error_count': report.get('error_count'),
        'plans': [
            {
                'workflow_count': item.get('workflow_count'),
                'incomplete_count': item.get('incomplete_count'),
                'error_count': item.get('error_count'),
                'gate': item.get('gate'),
                'digest': item.get('digest'),
            }
            for item in report.get('plans', [])
        ],
        'gate': report.get('gate'),
    })


def data_pack_report(plans: Iterable[DataPackPlanV2],
                     profile: DataProfileV2 | None = None) -> dict[str, Any]:
    """Summarize data plans with a recomputable digest."""

    active = profile or DEFAULT_DATA_PROFILE
    items = list(plans)
    workflow_count = sum(len(item.workflows) for item in items)
    incomplete_count = sum(len(item.incomplete) for item in items)
    error_count = sum(len(item.issues) for item in items)
    payload: dict[str, Any] = {
        'version': DATA_PACK_VERSION,
        'format': DATA_PACK_FORMAT,
        'profile': active.to_dict(),
        'profile_digest': active.digest(),
        'plan_count': len(items),
        'workflow_count': workflow_count,
        'clean_count': workflow_count - incomplete_count,
        'incomplete_count': incomplete_count,
        'error_count': error_count,
        'plans': [item.to_dict() for item in items],
        'gate': _decision(error_count, incomplete_count, active)['gate'],
    }
    payload['digest'] = _report_digest(payload)
    return payload


def data_pack_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute a deterministic PASS/FAIL decision from a data report."""

    issues: list[str] = []
    if report.get('version') != DATA_PACK_VERSION:
        issues.append('version')
    if report.get('format') != DATA_PACK_FORMAT:
        issues.append('format')
    if report.get('gate') not in ('PASS', 'FAIL'):
        issues.append('report')
    digest = str(report.get('digest', ''))
    if len(digest) != 64 or digest != _report_digest(report):
        issues.append('digest')
    workflow_count = int(report.get('workflow_count', 0))
    incomplete_count = int(report.get('incomplete_count', 0))
    error_count = int(report.get('error_count', 0))
    clean_count = int(report.get('clean_count', 0))
    if workflow_count != clean_count + incomplete_count:
        issues.append('counts')
    for item in report.get('plans', []):
        item_digest = str(item.get('digest', ''))
        if len(item_digest) != 64 or item_digest != _plan_digest(item):
            issues.append('plan_digest')
        if int(item.get('workflow_count', 0)) != (
                int(item.get('clean_count', 0))
                + int(item.get('incomplete_count', 0))):
            issues.append('plan_counts')
        for workflow in item.get('workflows', []):
            fingerprint = str(workflow.get('fingerprint', ''))
            if (len(fingerprint) != 64
                    or fingerprint != _workflow_fingerprint(workflow)):
                issues.append('workflow_fingerprint')
        for issue_item in item.get('issues', []):
            fingerprint = str(issue_item.get('fingerprint', ''))
            if (len(fingerprint) != 64
                    or fingerprint != _issue_fingerprint(issue_item)):
                issues.append('issue_fingerprint')
    profile_data = report.get('profile') or DEFAULT_DATA_PROFILE.to_dict()
    try:
        profile = DataProfileV2(**profile_data)
    except Exception:
        issues.append('profile')
        profile = DEFAULT_DATA_PROFILE
    expected = _decision(error_count, incomplete_count, profile)
    if report.get('gate') != expected['gate']:
        issues.append('gate')
    issues.extend(expected['issues'])
    return {'gate': 'PASS' if not issues else 'FAIL',
            'issues': sorted(set(issues))}


def build_data_pack_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'DATA_PACK_VERSION': DATA_PACK_VERSION,
        'DATA_PACK_FORMAT': DATA_PACK_FORMAT,
        'DATA_PACK_SKIP_DIRS': DATA_PACK_SKIP_DIRS,
        'DATA_PACK_PREVIEW_DIRS': DATA_PACK_PREVIEW_DIRS,
        'DATA_KINDS': DATA_KINDS,
        'DataProfileV2': DataProfileV2,
        'DEFAULT_DATA_PROFILE': DEFAULT_DATA_PROFILE,
        'DataIssueV2': DataIssueV2,
        'DataWorkflowV2': DataWorkflowV2,
        'DataPackPlanV2': DataPackPlanV2,
        'DataPackError': DataPackError,
        'plan_data_pack': plan_data_pack,
        'load_data_state_v2': load_data_state_v2,
        'write_data_state_v2': write_data_state_v2,
        'data_pack_capabilities': data_pack_capabilities,
        'data_pack_report': data_pack_report,
        'data_pack_gate': data_pack_gate,
        'build_data_pack_namespace': build_data_pack_namespace,
    }


__all__ = [
    'DATA_PACK_VERSION', 'DATA_PACK_FORMAT', 'DATA_PACK_SKIP_DIRS',
    'DATA_PACK_PREVIEW_DIRS', 'DATA_KINDS', 'DataProfileV2',
    'DEFAULT_DATA_PROFILE', 'DataPackError', 'DataIssueV2',
    'DataWorkflowV2', 'DataPackPlanV2', 'plan_data_pack',
    'load_data_state_v2', 'write_data_state_v2', 'data_pack_capabilities',
    'data_pack_report', 'data_pack_gate', 'build_data_pack_namespace',
]
