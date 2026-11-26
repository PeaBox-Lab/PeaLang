"""Phase 85: deterministic test framework v2 for PeaLang developer tooling.

This module is additive to the existing ``pea test`` command and the native
testing helpers. It provides stable test identifiers, deterministic ordering,
and a recomputable PASS/FAIL gate. Elapsed timings and raw host paths are
excluded from evidence and digests so reports compare identically in editors
and CI.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .native_testing import run_source_tests

TEST_FRAMEWORK_V2_VERSION = '3.1.48'
TEST_FRAMEWORK_V2_FORMAT = 'pea-test-v2'
TEST_V2_OPTIONS = ('filter_text', 'fail_fast', 'max_failures')


class TestFrameworkV2Error(Exception):
    """Raised when a test framework v2 profile or source input is invalid."""


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class TestProfileV2:
    """A validated, serializable test framework v2 profile."""

    filter_text: str = ''
    fail_fast: bool = False
    max_failures: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.filter_text, str):
            raise TestFrameworkV2Error('filter_text must be text')
        if int(self.max_failures) < 0:
            raise TestFrameworkV2Error('max_failures must not be negative')

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return _digest(self.to_dict())


DEFAULT_TEST_PROFILE = TestProfileV2()


def test_framework_v2_capabilities() -> dict[str, Any]:
    """Return the versioned test framework v2 capability set."""

    return {
        'version': TEST_FRAMEWORK_V2_VERSION,
        'format': TEST_FRAMEWORK_V2_FORMAT,
        'profile': DEFAULT_TEST_PROFILE.to_dict(),
        'options': list(TEST_V2_OPTIONS),
        'executor': 'native_vm',
        'stable_ids': True,
        'deterministic_order': True,
        'wall_clock_excluded': True,
        'recomputed_gate': True,
    }


def _stable_error(error: str | None, source_name: str) -> str | None:
    if not error:
        return None
    return error.replace(source_name, '<source>').replace('\\', '/')


def _case_id(describe: str, name: str, line: int) -> str:
    return f'{describe or "global"}::{name}@{line}'


@dataclass(frozen=True)
class TestCaseV2:
    """One deterministic test framework v2 case outcome."""

    case_id: str
    name: str
    describe: str
    source_name: str
    line: int
    passed: bool
    error: str | None = None

    def fingerprint(self) -> str:
        return _digest([
            self.case_id, self.name, self.describe, self.line,
            self.passed, self.error or '',
        ])

    def to_dict(self) -> dict[str, Any]:
        return {
            'case_id': self.case_id,
            'name': self.name,
            'describe': self.describe,
            'source_name': self.source_name,
            'line': self.line,
            'passed': self.passed,
            'error': self.error,
            'fingerprint': self.fingerprint(),
        }


def _decision(failed_count: int,
              profile: TestProfileV2) -> dict[str, Any]:
    issues = ['failures'] if failed_count > profile.max_failures else []
    return {'gate': 'FAIL' if issues else 'PASS', 'issues': issues}


def _discovery_failure(source_name: str,
                       exc: Exception) -> TestCaseV2:
    name = 'discovery'
    return TestCaseV2(
        case_id=_case_id('<discovery>', name, 1),
        name=name,
        describe='<discovery>',
        source_name=source_name,
        line=1,
        passed=False,
        error=f'{type(exc).__name__}: test discovery failed',
    )


def run_test_source_v2(source: str, profile: TestProfileV2 | None = None,
                       source_name: str = '<input>') -> TestResultV2:
    """Run native tests from source text and return deterministic evidence."""

    if not isinstance(source, str):
        raise TestFrameworkV2Error('source must be text')
    active = profile or DEFAULT_TEST_PROFILE
    normalized = source.replace('\r\n', '\n').replace('\r', '\n')
    try:
        raw_results = run_source_tests(
            normalized, source_name, active.filter_text or None,
        )
    except Exception as exc:
        cases = (_discovery_failure(source_name, exc),)
    else:
        ordered = sorted(raw_results, key=lambda item: (
            item.describe, item.line, item.name,
        ))
        cases_list: list[TestCaseV2] = []
        for item in ordered:
            cases_list.append(TestCaseV2(
                case_id=_case_id(item.describe, item.name, item.line),
                name=item.name,
                describe=item.describe,
                source_name=source_name,
                line=item.line,
                passed=item.passed,
                error=_stable_error(item.error, source_name),
            ))
            if active.fail_fast and not item.passed:
                break
        cases = tuple(cases_list)
    passed_count = sum(1 for item in cases if item.passed)
    failed_count = len(cases) - passed_count
    gate = _decision(failed_count, active)['gate']
    payload = {
        'version': TEST_FRAMEWORK_V2_VERSION,
        'format': TEST_FRAMEWORK_V2_FORMAT,
        'profile': active.to_dict(),
        'case_count': len(cases),
        'passed_count': passed_count,
        'failed_count': failed_count,
        'cases': [item.fingerprint() for item in cases],
        'gate': gate,
    }
    return TestResultV2(
        version=TEST_FRAMEWORK_V2_VERSION,
        format=TEST_FRAMEWORK_V2_FORMAT,
        profile=active.to_dict(),
        source_name=source_name,
        cases=cases,
        passed_count=passed_count,
        failed_count=failed_count,
        gate=gate,
        digest=_digest(payload),
    )


def run_test_file_v2(path: str | Path,
                     profile: TestProfileV2 | None = None) -> TestResultV2:
    """Run native tests from one file without exposing the host path."""

    target = Path(path)
    source = target.read_text(encoding='utf-8')
    return run_test_source_v2(source, profile, target.name)


@dataclass(frozen=True)
class TestResultV2:
    """Reviewable outcome of one test framework v2 operation."""

    version: str
    format: str
    profile: dict[str, Any]
    source_name: str
    cases: tuple[TestCaseV2, ...]
    passed_count: int
    failed_count: int
    gate: str
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
            'format': self.format,
            'profile': self.profile,
            'source_name': self.source_name,
            'case_count': len(self.cases),
            'passed_count': self.passed_count,
            'failed_count': self.failed_count,
            'gate': self.gate,
            'cases': [item.to_dict() for item in self.cases],
            'digest': self.digest,
        }


def _case_fingerprint(case: dict[str, Any]) -> str:
    return _digest([
        case.get('case_id'), case.get('name'), case.get('describe'),
        case.get('line'), case.get('passed'), case.get('error') or '',
    ])


def _result_digest(item: dict[str, Any]) -> str:
    return _digest({
        'version': item.get('version'),
        'format': item.get('format'),
        'profile': item.get('profile'),
        'case_count': item.get('case_count'),
        'passed_count': item.get('passed_count'),
        'failed_count': item.get('failed_count'),
        'cases': [case.get('fingerprint') for case in item.get('cases', [])],
        'gate': item.get('gate'),
    })


def _report_digest(report: dict[str, Any]) -> str:
    return _digest({
        'version': report.get('version'),
        'format': report.get('format'),
        'profile_digest': report.get('profile_digest'),
        'result_count': report.get('result_count'),
        'case_count': report.get('case_count'),
        'passed_count': report.get('passed_count'),
        'failed_count': report.get('failed_count'),
        'results': [
            {
                'case_count': item.get('case_count'),
                'passed_count': item.get('passed_count'),
                'failed_count': item.get('failed_count'),
                'gate': item.get('gate'),
                'digest': item.get('digest'),
            }
            for item in report.get('results', [])
        ],
        'gate': report.get('gate'),
    })


def test_v2_report(results: Iterable[TestResultV2],
                   profile: TestProfileV2 | None = None) -> dict[str, Any]:
    """Summarize test framework v2 results with a stable digest."""

    active = profile or DEFAULT_TEST_PROFILE
    items = list(results)
    passed_count = sum(item.passed_count for item in items)
    failed_count = sum(item.failed_count for item in items)
    payload: dict[str, Any] = {
        'version': TEST_FRAMEWORK_V2_VERSION,
        'format': TEST_FRAMEWORK_V2_FORMAT,
        'profile': active.to_dict(),
        'profile_digest': active.digest(),
        'result_count': len(items),
        'case_count': sum(len(item.cases) for item in items),
        'passed_count': passed_count,
        'failed_count': failed_count,
        'results': [item.to_dict() for item in items],
        'gate': _decision(failed_count, active)['gate'],
    }
    payload['digest'] = _report_digest(payload)
    return payload


def test_v2_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute a deterministic PASS/FAIL decision from a test report."""

    issues: list[str] = []
    if report.get('version') != TEST_FRAMEWORK_V2_VERSION:
        issues.append('version')
    if report.get('format') != TEST_FRAMEWORK_V2_FORMAT:
        issues.append('format')
    if report.get('gate') not in ('PASS', 'FAIL'):
        issues.append('report')
    digest = str(report.get('digest', ''))
    if len(digest) != 64:
        issues.append('digest')
    elif digest != _report_digest(report):
        issues.append('digest')
    for item in report.get('results', []):
        result_digest = str(item.get('digest', ''))
        if len(result_digest) != 64 or result_digest != _result_digest(item):
            issues.append('result_digest')
        for case in item.get('cases', []):
            fingerprint = str(case.get('fingerprint', ''))
            if len(fingerprint) != 64 or fingerprint != _case_fingerprint(case):
                issues.append('case_fingerprint')
    profile_data = report.get('profile') or DEFAULT_TEST_PROFILE.to_dict()
    try:
        profile = TestProfileV2(**profile_data)
    except Exception:
        issues.append('profile')
        profile = DEFAULT_TEST_PROFILE
    failed_count = int(report.get('failed_count', 0))
    passed_count = int(report.get('passed_count', 0))
    if report.get('case_count') != passed_count + failed_count:
        issues.append('counts')
    expected = _decision(failed_count, profile)
    if report.get('gate') != expected['gate']:
        issues.append('gate')
    issues.extend(expected['issues'])
    return {'gate': 'PASS' if not issues else 'FAIL',
            'issues': sorted(set(issues))}


def build_test_framework_v2_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'TEST_FRAMEWORK_V2_VERSION': TEST_FRAMEWORK_V2_VERSION,
        'TEST_FRAMEWORK_V2_FORMAT': TEST_FRAMEWORK_V2_FORMAT,
        'TEST_V2_OPTIONS': TEST_V2_OPTIONS,
        'TestProfileV2': TestProfileV2,
        'DEFAULT_TEST_PROFILE': DEFAULT_TEST_PROFILE,
        'TestCaseV2': TestCaseV2,
        'TestResultV2': TestResultV2,
        'TestFrameworkV2Error': TestFrameworkV2Error,
        'run_test_source_v2': run_test_source_v2,
        'run_test_file_v2': run_test_file_v2,
        'test_framework_v2_capabilities': test_framework_v2_capabilities,
        'test_v2_report': test_v2_report,
        'test_v2_gate': test_v2_gate,
        'build_test_framework_v2_namespace': build_test_framework_v2_namespace,
    }


__all__ = [
    'TEST_FRAMEWORK_V2_VERSION', 'TEST_FRAMEWORK_V2_FORMAT',
    'TEST_V2_OPTIONS', 'TestProfileV2', 'DEFAULT_TEST_PROFILE',
    'TestCaseV2', 'TestResultV2', 'TestFrameworkV2Error',
    'run_test_source_v2', 'run_test_file_v2',
    'test_framework_v2_capabilities', 'test_v2_report', 'test_v2_gate',
    'build_test_framework_v2_namespace',
]
