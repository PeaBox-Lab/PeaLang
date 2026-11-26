"""Phase 89: deterministic project template catalogs for PeaLang projects.

This module is additive to the existing ``pea scaffold`` and ``pea templates``
commands. It inventories template manifests, validates their dependency graph
and file contracts, and reports a deterministic template order and drift set.
All evidence is free of wall-clock values and absolute host paths. It reports a
plan; it does not create or modify project files.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

PROJECT_TEMPLATES_V2_VERSION = '3.1.52'
PROJECT_TEMPLATES_V2_FORMAT = 'pea-templates-v2'
PROJECT_TEMPLATES_V2_SKIP_DIRS = frozenset({
    '.git', '.venv', '__pycache__', '.pea_modules', '.pea_test_index', 'build',
    'node_modules', 'dist',
})
PROJECT_TEMPLATES_V2_COMMUNITY_DIRS = frozenset({
    'community', 'contrib', 'third-party',
})
TEMPLATE_NAME_RE = re.compile(r'^[a-z][a-z0-9_-]*$')


class ProjectTemplatesV2Error(Exception):
    """Raised when a template profile, manifest, or state input is invalid."""


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class TemplateProfileV2:
    """A validated, serializable project template profile."""

    max_templates: int = 500
    include_community: bool = False
    check_dependencies: bool = True
    fail_on_drift: bool = False
    current_version: str = ''

    def __post_init__(self) -> None:
        if int(self.max_templates) < 1:
            raise ProjectTemplatesV2Error('max_templates must be at least 1')
        if not isinstance(self.current_version, str):
            raise ProjectTemplatesV2Error('current_version must be a string')

    def effective_version(self) -> str:
        return self.current_version or PROJECT_TEMPLATES_V2_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return _digest(self.to_dict())


DEFAULT_TEMPLATE_PROFILE = TemplateProfileV2()


def project_templates_v2_capabilities() -> dict[str, Any]:
    """Return the versioned project template capability set."""

    return {
        'version': PROJECT_TEMPLATES_V2_VERSION,
        'format': PROJECT_TEMPLATES_V2_FORMAT,
        'profile': DEFAULT_TEMPLATE_PROFILE.to_dict(),
        'options': ['max_templates', 'include_community', 'check_dependencies',
                    'fail_on_drift', 'current_version'],
        'source_filter': '*.template.json',
        'stable_order': True,
        'wall_clock_excluded': True,
        'host_paths_excluded': True,
        'recomputed_gate': True,
    }


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _discover(root: Path, profile: TemplateProfileV2) -> list[str]:
    paths: list[str] = []
    for path in root.rglob('*.template.json'):
        parts = path.relative_to(root).parts
        if any(part in PROJECT_TEMPLATES_V2_SKIP_DIRS for part in parts[:-1]):
            continue
        if (not profile.include_community
                and any(part in PROJECT_TEMPLATES_V2_COMMUNITY_DIRS
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
    files = data.get('files')
    requires = data.get('requires', [])
    entrypoints = data.get('entrypoints', [])
    if not isinstance(name, str) or not TEMPLATE_NAME_RE.match(name):
        return None
    if not isinstance(version, str):
        return None
    if (not isinstance(files, list) or not files
            or not all(isinstance(item, str) and item for item in files)):
        return None
    if not isinstance(requires, list) or not all(
            isinstance(item, str) for item in requires):
        return None
    if not isinstance(entrypoints, list) or not all(
            isinstance(item, str) for item in entrypoints):
        return None
    return {
        'name': name,
        'version': version,
        'files': tuple(sorted(set(files))),
        'requires': tuple(sorted(set(requires))),
        'entrypoints': tuple(sorted(set(entrypoints))),
    }


def _canonical_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    items = list(cycle[:-1] if cycle and cycle[-1] == cycle[0] else cycle)
    rotations = [tuple(items[index:] + items[:index])
                 for index in range(len(items))]
    return min(rotations)


@dataclass(frozen=True)
class TemplateIssueV2:
    """One stable project-template issue."""

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
class TemplateNodeV2:
    """One reviewed template node in a project template plan."""

    path: str
    digest: str
    name: str
    version: str
    files: tuple[str, ...]
    requires: tuple[str, ...]
    entrypoints: tuple[str, ...]
    dependencies: tuple[str, ...]
    state: str
    reasons: tuple[str, ...]

    def fingerprint(self) -> str:
        return _digest([
            self.path, self.digest, self.name, self.version,
            list(self.files), list(self.requires), list(self.entrypoints),
            list(self.dependencies), self.state, list(self.reasons),
        ])

    def to_dict(self) -> dict[str, Any]:
        return {
            'path': self.path,
            'digest': self.digest,
            'name': self.name,
            'version': self.version,
            'files': list(self.files),
            'requires': list(self.requires),
            'entrypoints': list(self.entrypoints),
            'dependencies': list(self.dependencies),
            'state': self.state,
            'reasons': list(self.reasons),
            'fingerprint': self.fingerprint(),
        }


def _decision(error_count: int, drift_count: int,
              profile: TemplateProfileV2) -> dict[str, Any]:
    issues: list[str] = []
    if error_count:
        issues.append('errors')
    if profile.fail_on_drift and drift_count:
        issues.append('drift')
    return {'gate': 'FAIL' if issues else 'PASS', 'issues': issues}


@dataclass(frozen=True)
class TemplatePlanV2:
    """Reviewable outcome of one project template inventory."""

    version: str
    format: str
    profile: dict[str, Any]
    root_name: str
    nodes: tuple[TemplateNodeV2, ...]
    build_order: tuple[str, ...]
    drift: tuple[str, ...]
    issues: tuple[TemplateIssueV2, ...]
    gate: str
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
            'format': self.format,
            'profile': self.profile,
            'root_name': self.root_name,
            'template_count': len(self.nodes),
            'clean_count': len(self.nodes) - len(self.drift),
            'drift_count': len(self.drift),
            'error_count': len(self.issues),
            'nodes': [item.to_dict() for item in self.nodes],
            'build_order': list(self.build_order),
            'drift': list(self.drift),
            'issues': [item.to_dict() for item in self.issues],
            'gate': self.gate,
            'digest': self.digest,
        }


def plan_project_templates_v2(root: str | Path,
                              profile: TemplateProfileV2 | None = None,
                              state: dict[str, str] | None = None
                              ) -> TemplatePlanV2:
    """Inventory project templates and report stable contract evidence."""

    base = Path(root)
    if not base.is_dir():
        raise ProjectTemplatesV2Error('root must be a directory')
    active = profile or DEFAULT_TEMPLATE_PROFILE
    previous = state or {}
    if not isinstance(previous, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in previous.items()):
        raise ProjectTemplatesV2Error('state must map paths to digests')
    paths = _discover(base, active)
    issues: list[TemplateIssueV2] = []
    if len(paths) > active.max_templates:
        issues.append(TemplateIssueV2(
            'T203', 'error',
            f'Template catalog has {len(paths)} templates, exceeding limit '
            f'{active.max_templates}',
            '.',
        ))

    digests: dict[str, str] = {}
    manifests: dict[str, dict[str, Any]] = {}
    for path in paths:
        data = (base / path).read_bytes()
        digests[path] = hashlib.sha256(data).hexdigest()
        manifest = _manifest(base, path)
        if manifest is None:
            issues.append(TemplateIssueV2(
                'T204', 'error',
                f"Template manifest '{path}' is invalid",
                path,
            ))
            manifest = {
                'name': '', 'version': '', 'files': (), 'requires': (),
                'entrypoints': (),
            }
        manifests[path] = manifest
        for entrypoint in manifest['entrypoints']:
            if entrypoint not in manifest['files']:
                issues.append(TemplateIssueV2(
                    'T205', 'error',
                    f"Template '{path}' entrypoint '{entrypoint}' is not in files",
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
            elif active.check_dependencies:
                issues.append(TemplateIssueV2(
                    'T201', 'error',
                    f"Template '{name}' required by '{path}' is not present",
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
        issues.append(TemplateIssueV2(
            'T202', 'error',
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
        TemplateNodeV2(
            path=path,
            digest=digests[path],
            name=manifests[path]['name'],
            version=manifests[path]['version'],
            files=manifests[path]['files'],
            requires=manifests[path]['requires'],
            entrypoints=manifests[path]['entrypoints'],
            dependencies=dependencies[path],
            state='stale' if path in stale else 'current',
            reasons=tuple(sorted(set(reasons[path]))),
        )
        for path in paths
    )
    drift = tuple(path for path in paths if path in stale)
    ordered_issues = tuple(sorted(
        issues, key=lambda item: (item.code, item.path, item.message),
    ))
    gate = _decision(len(ordered_issues), len(drift), active)['gate']
    payload = {
        'version': PROJECT_TEMPLATES_V2_VERSION,
        'format': PROJECT_TEMPLATES_V2_FORMAT,
        'profile': active.digest(),
        'nodes': [item.fingerprint() for item in nodes],
        'build_order': order,
        'drift': list(drift),
        'issues': [item.fingerprint() for item in ordered_issues],
        'gate': gate,
    }
    return TemplatePlanV2(
        version=PROJECT_TEMPLATES_V2_VERSION,
        format=PROJECT_TEMPLATES_V2_FORMAT,
        profile=active.to_dict(),
        root_name=base.resolve().name,
        nodes=nodes,
        build_order=tuple(order),
        drift=drift,
        issues=ordered_issues,
        gate=gate,
        digest=_digest(payload),
    )


def load_template_state_v2(path: str | Path) -> dict[str, str]:
    """Load versioned template state, returning empty state when absent."""

    target = Path(path)
    if not target.is_file():
        return {}
    try:
        data = json.loads(target.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ProjectTemplatesV2Error('template state is not valid JSON') from exc
    if data.get('version') != PROJECT_TEMPLATES_V2_VERSION:
        raise ProjectTemplatesV2Error('template state version does not match')
    state = data.get('state', {})
    if not isinstance(state, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in state.items()):
        raise ProjectTemplatesV2Error('template state must map paths to digests')
    return dict(state)


def write_template_state_v2(root: str | Path, plan: TemplatePlanV2,
                            path: str | Path | None = None) -> Path:
    """Persist a deterministic template digest state."""

    target = Path(path) if path is not None else Path(root) / '.pea_templates_v2.json'
    payload = {
        'version': PROJECT_TEMPLATES_V2_VERSION,
        'format': PROJECT_TEMPLATES_V2_FORMAT,
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
        item.get('path'), item.get('digest'), item.get('name'),
        item.get('version'), list(item.get('files', [])),
        list(item.get('requires', [])), list(item.get('entrypoints', [])),
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
        'drift': item.get('drift', []),
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
        'template_count': report.get('template_count'),
        'clean_count': report.get('clean_count'),
        'drift_count': report.get('drift_count'),
        'error_count': report.get('error_count'),
        'plans': [
            {
                'template_count': item.get('template_count'),
                'drift_count': item.get('drift_count'),
                'error_count': item.get('error_count'),
                'gate': item.get('gate'),
                'digest': item.get('digest'),
            }
            for item in report.get('plans', [])
        ],
        'gate': report.get('gate'),
    })


def templates_v2_report(plans: Iterable[TemplatePlanV2],
                        profile: TemplateProfileV2 | None = None
                        ) -> dict[str, Any]:
    """Summarize project template plans with a recomputable digest."""

    active = profile or DEFAULT_TEMPLATE_PROFILE
    items = list(plans)
    template_count = sum(len(item.nodes) for item in items)
    drift_count = sum(len(item.drift) for item in items)
    error_count = sum(len(item.issues) for item in items)
    payload: dict[str, Any] = {
        'version': PROJECT_TEMPLATES_V2_VERSION,
        'format': PROJECT_TEMPLATES_V2_FORMAT,
        'profile': active.to_dict(),
        'profile_digest': active.digest(),
        'plan_count': len(items),
        'template_count': template_count,
        'clean_count': template_count - drift_count,
        'drift_count': drift_count,
        'error_count': error_count,
        'plans': [item.to_dict() for item in items],
        'gate': _decision(error_count, drift_count, active)['gate'],
    }
    payload['digest'] = _report_digest(payload)
    return payload


def templates_v2_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute a deterministic PASS/FAIL decision from a template report."""

    issues: list[str] = []
    if report.get('version') != PROJECT_TEMPLATES_V2_VERSION:
        issues.append('version')
    if report.get('format') != PROJECT_TEMPLATES_V2_FORMAT:
        issues.append('format')
    if report.get('gate') not in ('PASS', 'FAIL'):
        issues.append('report')
    digest = str(report.get('digest', ''))
    if len(digest) != 64 or digest != _report_digest(report):
        issues.append('digest')
    template_count = int(report.get('template_count', 0))
    drift_count = int(report.get('drift_count', 0))
    error_count = int(report.get('error_count', 0))
    clean_count = int(report.get('clean_count', 0))
    if template_count != clean_count + drift_count:
        issues.append('counts')
    for item in report.get('plans', []):
        item_digest = str(item.get('digest', ''))
        if len(item_digest) != 64 or item_digest != _plan_digest(item):
            issues.append('plan_digest')
        if int(item.get('template_count', 0)) != (
                int(item.get('clean_count', 0))
                + int(item.get('drift_count', 0))):
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
    profile_data = report.get('profile') or DEFAULT_TEMPLATE_PROFILE.to_dict()
    try:
        profile = TemplateProfileV2(**profile_data)
    except Exception:
        issues.append('profile')
        profile = DEFAULT_TEMPLATE_PROFILE
    expected = _decision(error_count, drift_count, profile)
    if report.get('gate') != expected['gate']:
        issues.append('gate')
    issues.extend(expected['issues'])
    return {'gate': 'PASS' if not issues else 'FAIL',
            'issues': sorted(set(issues))}


def build_project_templates_v2_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'PROJECT_TEMPLATES_V2_VERSION': PROJECT_TEMPLATES_V2_VERSION,
        'PROJECT_TEMPLATES_V2_FORMAT': PROJECT_TEMPLATES_V2_FORMAT,
        'PROJECT_TEMPLATES_V2_SKIP_DIRS': PROJECT_TEMPLATES_V2_SKIP_DIRS,
        'PROJECT_TEMPLATES_V2_COMMUNITY_DIRS': PROJECT_TEMPLATES_V2_COMMUNITY_DIRS,
        'TemplateProfileV2': TemplateProfileV2,
        'DEFAULT_TEMPLATE_PROFILE': DEFAULT_TEMPLATE_PROFILE,
        'TemplateIssueV2': TemplateIssueV2,
        'TemplateNodeV2': TemplateNodeV2,
        'TemplatePlanV2': TemplatePlanV2,
        'ProjectTemplatesV2Error': ProjectTemplatesV2Error,
        'plan_project_templates_v2': plan_project_templates_v2,
        'load_template_state_v2': load_template_state_v2,
        'write_template_state_v2': write_template_state_v2,
        'project_templates_v2_capabilities': project_templates_v2_capabilities,
        'templates_v2_report': templates_v2_report,
        'templates_v2_gate': templates_v2_gate,
        'build_project_templates_v2_namespace': build_project_templates_v2_namespace,
    }


__all__ = [
    'PROJECT_TEMPLATES_V2_VERSION', 'PROJECT_TEMPLATES_V2_FORMAT',
    'PROJECT_TEMPLATES_V2_SKIP_DIRS', 'PROJECT_TEMPLATES_V2_COMMUNITY_DIRS',
    'TemplateProfileV2', 'DEFAULT_TEMPLATE_PROFILE',
    'ProjectTemplatesV2Error', 'TemplateIssueV2', 'TemplateNodeV2',
    'TemplatePlanV2', 'plan_project_templates_v2',
    'load_template_state_v2', 'write_template_state_v2',
    'project_templates_v2_capabilities', 'templates_v2_report',
    'templates_v2_gate', 'build_project_templates_v2_namespace',
]
