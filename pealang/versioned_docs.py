"""Phase 87: deterministic versioned documentation inventory for PeaLang.

This module is additive to the existing ``pea docs`` command. It inventories
Markdown documentation, extracts version references and internal links, and
reports stale versions, broken links, and digest drift as stable evidence. All
output is free of wall-clock values and absolute host paths. It reports a plan;
it does not rewrite documentation.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

VERSIONED_DOCS_VERSION = '3.1.50'
VERSIONED_DOCS_FORMAT = 'pea-docs-v2'
DOCS_V2_SKIP_DIRS = frozenset({
    '.git', '.venv', '__pycache__', '.pea_test_index', 'build', 'node_modules',
})
DOCS_V2_HISTORY_DIRS = frozenset({
    'releases', 'history', 'archive', 'retention',
})
VERSION_RE = re.compile(r'\bv?(\d+\.\d+\.\d+)\b')
LINK_RE = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
EXTERNAL_LINK_PREFIXES = ('http://', 'https://', 'mailto:', 'data:', 'ftp://')


class VersionedDocsError(Exception):
    """Raised when a versioned docs profile or state input is invalid."""


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class DocsProfileV2:
    """A validated, serializable versioned documentation profile."""

    max_files: int = 500
    include_release_notes: bool = False
    check_links: bool = True
    fail_on_drift: bool = False
    current_version: str = ''

    def __post_init__(self) -> None:
        if int(self.max_files) < 1:
            raise VersionedDocsError('max_files must be at least 1')
        if not isinstance(self.current_version, str):
            raise VersionedDocsError('current_version must be a string')

    def effective_version(self) -> str:
        return self.current_version or VERSIONED_DOCS_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return _digest(self.to_dict())


DEFAULT_DOCS_PROFILE = DocsProfileV2()


def versioned_docs_capabilities() -> dict[str, Any]:
    """Return the versioned documentation capability set."""

    return {
        'version': VERSIONED_DOCS_VERSION,
        'format': VERSIONED_DOCS_FORMAT,
        'profile': DEFAULT_DOCS_PROFILE.to_dict(),
        'options': ['max_files', 'include_release_notes', 'check_links',
                    'fail_on_drift', 'current_version'],
        'source_filter': '*.md',
        'version_pattern': 'v?MAJOR.MINOR.PATCH',
        'stable_order': True,
        'wall_clock_excluded': True,
        'host_paths_excluded': True,
        'recomputed_gate': True,
    }


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _discover(root: Path, profile: DocsProfileV2) -> list[str]:
    paths: list[str] = []
    for path in root.rglob('*.md'):
        parts = path.relative_to(root).parts
        if any(part in DOCS_V2_SKIP_DIRS for part in parts[:-1]):
            continue
        if (not profile.include_release_notes
                and any(part in DOCS_V2_HISTORY_DIRS for part in parts[:-1])):
            continue
        paths.append(_relative(path, root))
    return sorted(paths)


def _versions(text: str) -> tuple[str, ...]:
    return tuple(sorted(set(VERSION_RE.findall(text))))


def _links(text: str) -> tuple[str, ...]:
    found: set[str] = set()
    for raw in LINK_RE.findall(text):
        target = raw.strip()
        if (not target or target.startswith('#')
                or target.lower().startswith(EXTERNAL_LINK_PREFIXES)
                or '://' in target):
            continue
        found.add(target.split('#', 1)[0].split('?', 1)[0])
    return tuple(sorted(found))


def _resolve_link(root: Path, doc_path: str, target: str) -> str:
    base = (root / doc_path).parent
    try:
        resolved = (base / target).resolve()
        return _relative(resolved, root.resolve())
    except ValueError:
        return '<external>'


@dataclass(frozen=True)
class DocsIssueV2:
    """One stable versioned-docs issue."""

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
class DocEntryV2:
    """One reviewed documentation entry in a versioned docs plan."""

    path: str
    digest: str
    versions: tuple[str, ...]
    links: tuple[str, ...]
    state: str
    reasons: tuple[str, ...]

    def fingerprint(self) -> str:
        return _digest([
            self.path, self.digest, list(self.versions), list(self.links),
            self.state, list(self.reasons),
        ])

    def to_dict(self) -> dict[str, Any]:
        return {
            'path': self.path,
            'digest': self.digest,
            'versions': list(self.versions),
            'links': list(self.links),
            'state': self.state,
            'reasons': list(self.reasons),
            'fingerprint': self.fingerprint(),
        }


def _decision(error_count: int, drift_count: int,
              profile: DocsProfileV2) -> dict[str, Any]:
    issues: list[str] = []
    if error_count:
        issues.append('errors')
    if profile.fail_on_drift and drift_count:
        issues.append('drift')
    return {'gate': 'FAIL' if issues else 'PASS', 'issues': issues}


@dataclass(frozen=True)
class DocsPlanV2:
    """Reviewable outcome of one versioned documentation inventory."""

    version: str
    format: str
    profile: dict[str, Any]
    current_version: str
    root_name: str
    entries: tuple[DocEntryV2, ...]
    drift: tuple[str, ...]
    issues: tuple[DocsIssueV2, ...]
    gate: str
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
            'format': self.format,
            'profile': self.profile,
            'current_version': self.current_version,
            'root_name': self.root_name,
            'doc_count': len(self.entries),
            'clean_count': len(self.entries) - len(self.drift),
            'drift_count': len(self.drift),
            'error_count': len(self.issues),
            'entries': [item.to_dict() for item in self.entries],
            'drift': list(self.drift),
            'issues': [item.to_dict() for item in self.issues],
            'gate': self.gate,
            'digest': self.digest,
        }


def plan_docs_v2(root: str | Path, profile: DocsProfileV2 | None = None,
                 state: dict[str, str] | None = None) -> DocsPlanV2:
    """Inventory documentation and report stable version/link evidence."""

    base = Path(root)
    if not base.is_dir():
        raise VersionedDocsError('root must be a directory')
    active = profile or DEFAULT_DOCS_PROFILE
    previous = state or {}
    if not isinstance(previous, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in previous.items()):
        raise VersionedDocsError('state must map paths to digests')
    paths = _discover(base, active)
    issues: list[DocsIssueV2] = []
    if len(paths) > active.max_files:
        issues.append(DocsIssueV2(
            'D203', 'error',
            f'Docs inventory has {len(paths)} files, exceeding limit '
            f'{active.max_files}',
            '.',
        ))

    digests: dict[str, str] = {}
    versions: dict[str, tuple[str, ...]] = {}
    links: dict[str, tuple[str, ...]] = {}
    current = active.effective_version()
    for path in paths:
        data = (base / path).read_bytes()
        digests[path] = hashlib.sha256(data).hexdigest()
        text = data.decode('utf-8', errors='replace')
        versions[path] = _versions(text)
        links[path] = _links(text) if active.check_links else ()
        if versions[path] and current not in versions[path]:
            issues.append(DocsIssueV2(
                'D201', 'error',
                f"Doc '{path}' does not reference current version '{current}'",
                path,
            ))
        if active.check_links:
            for target in links[path]:
                resolved = _resolve_link(base, path, target)
                if resolved == '<external>' or not (base / resolved).is_file():
                    issues.append(DocsIssueV2(
                        'D202', 'error',
                        f"Doc '{path}' links to missing '{resolved}'",
                        path,
                    ))

    reasons: dict[str, list[str]] = {
        path: (['new'] if path not in previous
               else ['changed'] if previous[path] != digests[path] else [])
        for path in paths
    }
    drift = tuple(path for path in paths if reasons[path])
    entries = tuple(
        DocEntryV2(
            path=path,
            digest=digests[path],
            versions=versions[path],
            links=links[path],
            state='stale' if reasons[path] else 'current',
            reasons=tuple(reasons[path]),
        )
        for path in paths
    )
    ordered_issues = tuple(sorted(
        issues, key=lambda item: (item.code, item.path, item.message),
    ))
    gate = _decision(len(ordered_issues), len(drift), active)['gate']
    payload = {
        'version': VERSIONED_DOCS_VERSION,
        'format': VERSIONED_DOCS_FORMAT,
        'profile': active.digest(),
        'current_version': current,
        'entries': [item.fingerprint() for item in entries],
        'drift': list(drift),
        'issues': [item.fingerprint() for item in ordered_issues],
        'gate': gate,
    }
    return DocsPlanV2(
        version=VERSIONED_DOCS_VERSION,
        format=VERSIONED_DOCS_FORMAT,
        profile=active.to_dict(),
        current_version=current,
        root_name=base.resolve().name,
        entries=entries,
        drift=drift,
        issues=ordered_issues,
        gate=gate,
        digest=_digest(payload),
    )


def load_docs_state_v2(path: str | Path) -> dict[str, str]:
    """Load versioned docs state, returning empty state when absent."""

    target = Path(path)
    if not target.is_file():
        return {}
    try:
        data = json.loads(target.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise VersionedDocsError('docs state is not valid JSON') from exc
    if data.get('version') != VERSIONED_DOCS_VERSION:
        raise VersionedDocsError('docs state version does not match')
    state = data.get('state', {})
    if not isinstance(state, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in state.items()):
        raise VersionedDocsError('docs state must map paths to digests')
    return dict(state)


def write_docs_state_v2(root: str | Path, plan: DocsPlanV2,
                        path: str | Path | None = None) -> Path:
    """Persist deterministic documentation digest state."""

    target = Path(path) if path is not None else Path(root) / '.pea_docs_v2.json'
    payload = {
        'version': VERSIONED_DOCS_VERSION,
        'format': VERSIONED_DOCS_FORMAT,
        'state': {entry.path: entry.digest for entry in plan.entries},
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


def _entry_fingerprint(item: dict[str, Any]) -> str:
    return _digest([
        item.get('path'), item.get('digest'), list(item.get('versions', [])),
        list(item.get('links', [])), item.get('state'),
        list(item.get('reasons', [])),
    ])


def _plan_digest(item: dict[str, Any]) -> str:
    return _digest({
        'version': item.get('version'),
        'format': item.get('format'),
        'profile': _digest(item.get('profile', {})),
        'current_version': item.get('current_version'),
        'entries': [entry.get('fingerprint') for entry in item.get('entries', [])],
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
        'doc_count': report.get('doc_count'),
        'clean_count': report.get('clean_count'),
        'drift_count': report.get('drift_count'),
        'error_count': report.get('error_count'),
        'plans': [
            {
                'doc_count': item.get('doc_count'),
                'drift_count': item.get('drift_count'),
                'error_count': item.get('error_count'),
                'gate': item.get('gate'),
                'digest': item.get('digest'),
            }
            for item in report.get('plans', [])
        ],
        'gate': report.get('gate'),
    })


def docs_v2_report(plans: Iterable[DocsPlanV2],
                   profile: DocsProfileV2 | None = None) -> dict[str, Any]:
    """Summarize versioned docs plans with a recomputable digest."""

    active = profile or DEFAULT_DOCS_PROFILE
    items = list(plans)
    doc_count = sum(len(item.entries) for item in items)
    drift_count = sum(len(item.drift) for item in items)
    error_count = sum(len(item.issues) for item in items)
    payload: dict[str, Any] = {
        'version': VERSIONED_DOCS_VERSION,
        'format': VERSIONED_DOCS_FORMAT,
        'profile': active.to_dict(),
        'profile_digest': active.digest(),
        'plan_count': len(items),
        'doc_count': doc_count,
        'clean_count': doc_count - drift_count,
        'drift_count': drift_count,
        'error_count': error_count,
        'plans': [item.to_dict() for item in items],
        'gate': _decision(error_count, drift_count, active)['gate'],
    }
    payload['digest'] = _report_digest(payload)
    return payload


def docs_v2_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute a deterministic PASS/FAIL decision from a docs report."""

    issues: list[str] = []
    if report.get('version') != VERSIONED_DOCS_VERSION:
        issues.append('version')
    if report.get('format') != VERSIONED_DOCS_FORMAT:
        issues.append('format')
    if report.get('gate') not in ('PASS', 'FAIL'):
        issues.append('report')
    digest = str(report.get('digest', ''))
    if len(digest) != 64 or digest != _report_digest(report):
        issues.append('digest')
    doc_count = int(report.get('doc_count', 0))
    drift_count = int(report.get('drift_count', 0))
    error_count = int(report.get('error_count', 0))
    clean_count = int(report.get('clean_count', 0))
    if doc_count != clean_count + drift_count:
        issues.append('counts')
    for item in report.get('plans', []):
        item_digest = str(item.get('digest', ''))
        if len(item_digest) != 64 or item_digest != _plan_digest(item):
            issues.append('plan_digest')
        if int(item.get('doc_count', 0)) != (
                int(item.get('clean_count', 0))
                + int(item.get('drift_count', 0))):
            issues.append('plan_counts')
        for entry in item.get('entries', []):
            fingerprint = str(entry.get('fingerprint', ''))
            if (len(fingerprint) != 64
                    or fingerprint != _entry_fingerprint(entry)):
                issues.append('entry_fingerprint')
        for issue_item in item.get('issues', []):
            fingerprint = str(issue_item.get('fingerprint', ''))
            if (len(fingerprint) != 64
                    or fingerprint != _issue_fingerprint(issue_item)):
                issues.append('issue_fingerprint')
    profile_data = report.get('profile') or DEFAULT_DOCS_PROFILE.to_dict()
    try:
        profile = DocsProfileV2(**profile_data)
    except Exception:
        issues.append('profile')
        profile = DEFAULT_DOCS_PROFILE
    expected = _decision(error_count, drift_count, profile)
    if report.get('gate') != expected['gate']:
        issues.append('gate')
    issues.extend(expected['issues'])
    return {'gate': 'PASS' if not issues else 'FAIL',
            'issues': sorted(set(issues))}


def build_versioned_docs_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'VERSIONED_DOCS_VERSION': VERSIONED_DOCS_VERSION,
        'VERSIONED_DOCS_FORMAT': VERSIONED_DOCS_FORMAT,
        'DOCS_V2_SKIP_DIRS': DOCS_V2_SKIP_DIRS,
        'DocsProfileV2': DocsProfileV2,
        'DEFAULT_DOCS_PROFILE': DEFAULT_DOCS_PROFILE,
        'DocsIssueV2': DocsIssueV2,
        'DocEntryV2': DocEntryV2,
        'DocsPlanV2': DocsPlanV2,
        'VersionedDocsError': VersionedDocsError,
        'plan_docs_v2': plan_docs_v2,
        'load_docs_state_v2': load_docs_state_v2,
        'write_docs_state_v2': write_docs_state_v2,
        'versioned_docs_capabilities': versioned_docs_capabilities,
        'docs_v2_report': docs_v2_report,
        'docs_v2_gate': docs_v2_gate,
        'build_versioned_docs_namespace': build_versioned_docs_namespace,
    }


__all__ = [
    'VERSIONED_DOCS_VERSION', 'VERSIONED_DOCS_FORMAT', 'DOCS_V2_SKIP_DIRS',
    'DOCS_V2_HISTORY_DIRS', 'DocsProfileV2', 'DEFAULT_DOCS_PROFILE',
    'DocsIssueV2', 'DocEntryV2', 'DocsPlanV2', 'VersionedDocsError',
    'plan_docs_v2', 'load_docs_state_v2', 'write_docs_state_v2',
    'versioned_docs_capabilities', 'docs_v2_report', 'docs_v2_gate',
    'build_versioned_docs_namespace',
]
