"""Phase 84: deterministic linter v3 for PeaLang developer tooling.

This module is additive to the existing ``pea lint`` and ``PeaLinter``
surfaces. It emits stable, reviewable diagnostics with named rules, deterministic
fix hints, and a recomputable PASS/FAIL gate. Digests exclude source names,
wall-clock values, and raw host paths so the same findings hash identically in
editors and CI.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .ast_nodes import (ForStmt, FunctionExpr, FunctionStmt, IfStmt, Literal,
                        MatchStmt, PrintStmt, ReturnStmt, ThrowStmt, VarDecl,
                        WhileStmt)
from .parser import parse_source

LINTER_V3_VERSION = '3.1.47'
LINTER_V3_FORMAT = 'pea-lint-v3'
LINTER_V3_RULES = (
    ('L301', 'warning', 'line_length'),
    ('L302', 'info', 'trailing_whitespace'),
    ('L303', 'info', 'todo_marker'),
    ('L304', 'warning', 'function_naming'),
    ('L305', 'info', 'variable_naming'),
    ('L306', 'warning', 'debug_print'),
    ('L307', 'warning', 'high_complexity'),
    ('L308', 'warning', 'unreachable_code'),
    ('L309', 'error', 'parse_error'),
)


class LinterV3Error(Exception):
    """Raised when a linter v3 profile or source input is invalid."""


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class LintProfileV3:
    """A validated, serializable linter v3 profile."""

    max_line_length: int = 100
    max_complexity: int = 10
    check_naming: bool = True
    check_complexity: bool = True
    check_dead_code: bool = True
    check_style: bool = True
    check_debug_prints: bool = True
    fail_on_warning: bool = False

    def __post_init__(self) -> None:
        if int(self.max_line_length) < 40:
            raise LinterV3Error('max_line_length must be at least 40')
        if int(self.max_complexity) < 1:
            raise LinterV3Error('max_complexity must be at least 1')

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return _digest(self.to_dict())


DEFAULT_LINT_PROFILE = LintProfileV3()


def linter_v3_capabilities() -> dict[str, Any]:
    """Return the versioned linter v3 capability set."""

    return {
        'version': LINTER_V3_VERSION,
        'format': LINTER_V3_FORMAT,
        'profile': DEFAULT_LINT_PROFILE.to_dict(),
        'rules': [
            {'code': code, 'severity': severity, 'name': name}
            for code, severity, name in LINTER_V3_RULES
        ],
        'deterministic_order': True,
        'fix_hints': True,
        'recomputed_gate': True,
    }


def _string_mask(text: str) -> list[bool]:
    mask: list[bool] = []
    quote: str | None = None
    escaped = False
    for char in text:
        if quote is not None:
            mask.append(False)
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
            continue
        mask.append(True)
        if char in ('"', "'"):
            mask[-1] = False
            quote = char
    return mask


def _span(node: Any) -> tuple[int, int]:
    span = getattr(node, 'span', None)
    line = int(getattr(span, 'line', 1) or 1)
    col = int(getattr(span, 'col', 1) or 1)
    return max(1, line), max(1, col)


def _walk(node: Any) -> list[Any]:
    result = [node]
    for attr in sorted(vars(node)) if hasattr(node, '__dict__') else ():
        if attr.startswith('_'):
            continue
        value = getattr(node, attr, None)
        if isinstance(value, (list, tuple)):
            for item in value:
                if hasattr(item, '__dict__'):
                    result.extend(_walk(item))
        elif isinstance(value, dict):
            for item in value.values():
                if hasattr(item, '__dict__'):
                    result.extend(_walk(item))
        elif hasattr(value, '__dict__') and not isinstance(value, str):
            result.extend(_walk(value))
    return result


@dataclass(frozen=True)
class LintDiagnosticV3:
    """One stable linter v3 finding."""

    rule: str
    severity: str
    message: str
    line: int
    col: int
    source_name: str
    fix: str | None = None

    def fingerprint(self) -> str:
        return _digest([
            self.rule, self.severity, self.message,
            self.line, self.col, self.fix or '',
        ])

    def to_dict(self) -> dict[str, Any]:
        return {
            'rule': self.rule,
            'severity': self.severity,
            'message': self.message,
            'line': self.line,
            'col': self.col,
            'source_name': self.source_name,
            'fix': self.fix,
            'fingerprint': self.fingerprint(),
        }


def _diagnostic(rule: str, message: str, line: int, col: int,
                source_name: str, fix: str | None = None) -> LintDiagnosticV3:
    severity = next(item[1] for item in LINTER_V3_RULES if item[0] == rule)
    return LintDiagnosticV3(rule, severity, message, line, col, source_name, fix)


def _line_diagnostics(source: str, profile: LintProfileV3,
                      source_name: str) -> list[LintDiagnosticV3]:
    diagnostics: list[LintDiagnosticV3] = []
    for number, line in enumerate(source.split('\n'), 1):
        if profile.check_style and len(line) > profile.max_line_length:
            diagnostics.append(_diagnostic(
                'L301',
                f'Line length {len(line)} exceeds limit {profile.max_line_length}',
                number, 1, source_name,
            ))
            continue
        if profile.check_style and line != line.rstrip():
            diagnostics.append(_diagnostic(
                'L302', 'Trailing whitespace', number,
                len(line.rstrip()) + 1, source_name, line.rstrip(),
            ))
        mask = _string_mask(line)
        for token in ('TODO', 'FIXME'):
            start = 0
            while True:
                position = line.find(token, start)
                if position < 0:
                    break
                start = position + len(token)
                if all(mask[position:position + len(token)]):
                    diagnostics.append(_diagnostic(
                        'L303', f'{token} marker found', number,
                        position + 1, source_name,
                    ))
                    break
    return diagnostics


def _ast_diagnostics(source: str, profile: LintProfileV3,
                     source_name: str) -> list[LintDiagnosticV3]:
    diagnostics: list[LintDiagnosticV3] = []
    try:
        program = parse_source(source)
    except Exception as exc:
        return [_diagnostic(
            'L309', f'Parse error: {type(exc).__name__}', 1, 1, source_name,
        )]
    nodes = _walk(program)
    for node in nodes:
        line, col = _span(node)
        name = getattr(node, 'name', '')
        if (profile.check_naming and isinstance(node, (FunctionStmt, FunctionExpr))
                and name and name[0].isupper()):
            diagnostics.append(_diagnostic(
                'L304', f"Function '{name}' should start with lowercase",
                line, col, source_name,
            ))
        if (profile.check_naming and isinstance(node, VarDecl)
                and name and name[0].isupper()):
            diagnostics.append(_diagnostic(
                'L305', f"Variable '{name}' should start with lowercase",
                line, col, source_name,
            ))
        if (profile.check_debug_prints and isinstance(node, PrintStmt)
                and isinstance(node.value, Literal)
                and isinstance(node.value.value, str)
                and node.value.value.strip().lower().startswith(('debug', 'dbg'))):
            diagnostics.append(_diagnostic(
                'L306', 'Debug print marker found', line, col, source_name,
            ))
        if (profile.check_complexity
                and isinstance(node, (FunctionStmt, FunctionExpr))):
            complexity = 1 + sum(
                1 for child in nodes
                if isinstance(child, (IfStmt, WhileStmt, ForStmt, MatchStmt))
                and _contains(node, child)
            )
            if complexity > profile.max_complexity:
                diagnostics.append(_diagnostic(
                    'L307',
                    f'Cyclomatic complexity {complexity} exceeds limit {profile.max_complexity}',
                    line, col, source_name,
                ))
        if profile.check_dead_code and isinstance(node, (FunctionStmt, FunctionExpr)):
            terminated = False
            for statement in getattr(node, 'body', []) or []:
                if terminated:
                    diagnostics.append(_diagnostic(
                        'L308', 'Unreachable statement after return or throw',
                        *_span(statement), source_name,
                    ))
                    break
                if isinstance(statement, (ReturnStmt, ThrowStmt)):
                    terminated = True
    return diagnostics


def _contains(parent: Any, child: Any) -> bool:
    return any(item is child for item in _walk(parent))


def lint_source_v3(source: str, profile: LintProfileV3 | None = None,
                   source_name: str = '<input>') -> LintResultV3:
    """Lint source text and return deterministic, reviewable evidence."""

    if not isinstance(source, str):
        raise LinterV3Error('source must be text')
    active = profile or DEFAULT_LINT_PROFILE
    normalized = source.replace('\r\n', '\n').replace('\r', '\n')
    diagnostics = _line_diagnostics(normalized, active, source_name)
    diagnostics.extend(_ast_diagnostics(normalized, active, source_name))
    diagnostics.sort(key=lambda item: (
        item.line, item.col, item.rule, item.severity, item.message,
    ))
    counts = {
        'error': sum(1 for item in diagnostics if item.severity == 'error'),
        'warning': sum(1 for item in diagnostics if item.severity == 'warning'),
        'info': sum(1 for item in diagnostics if item.severity == 'info'),
    }
    gate = _decision(counts, active)['gate']
    payload = {
        'version': LINTER_V3_VERSION,
        'format': LINTER_V3_FORMAT,
        'profile': active.to_dict(),
        'diagnostic_count': len(diagnostics),
        'error_count': counts['error'],
        'warning_count': counts['warning'],
        'info_count': counts['info'],
        'diagnostics': [item.to_dict() for item in diagnostics],
        'gate': gate,
    }
    digest = _digest({
        'version': payload['version'],
        'format': payload['format'],
        'profile': active.digest(),
        'diagnostic_count': payload['diagnostic_count'],
        'error_count': payload['error_count'],
        'warning_count': payload['warning_count'],
        'info_count': payload['info_count'],
        'diagnostics': [item['fingerprint'] for item in payload['diagnostics']],
        'gate': gate,
    })
    return LintResultV3(
        version=LINTER_V3_VERSION, format=LINTER_V3_FORMAT,
        profile=active.to_dict(), source_name=source_name,
        diagnostics=tuple(diagnostics), error_count=counts['error'],
        warning_count=counts['warning'], info_count=counts['info'],
        gate=gate, digest=digest,
    )


def lint_file_v3(path: str | Path,
                 profile: LintProfileV3 | None = None) -> LintResultV3:
    """Lint one file and return its evidence without writing changes."""

    target = Path(path)
    source = target.read_text(encoding='utf-8')
    return lint_source_v3(source, profile, target.name)


@dataclass(frozen=True)
class LintResultV3:
    """Reviewable outcome of one linter v3 operation."""

    version: str
    format: str
    profile: dict[str, Any]
    source_name: str
    diagnostics: tuple[LintDiagnosticV3, ...]
    error_count: int
    warning_count: int
    info_count: int
    gate: str
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
            'format': self.format,
            'profile': self.profile,
            'source_name': self.source_name,
            'diagnostic_count': len(self.diagnostics),
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'info_count': self.info_count,
            'gate': self.gate,
            'diagnostics': [item.to_dict() for item in self.diagnostics],
            'digest': self.digest,
        }


def _decision(counts: dict[str, int],
              profile: LintProfileV3) -> dict[str, Any]:
    issues: list[str] = []
    if counts.get('error', 0) > 0:
        issues.append('errors')
    if profile.fail_on_warning and counts.get('warning', 0) > 0:
        issues.append('warnings')
    return {'gate': 'FAIL' if issues else 'PASS', 'issues': issues}


def _report_digest(report: dict[str, Any]) -> str:
    results = report.get('results', [])
    return _digest({
        'version': report.get('version'),
        'format': report.get('format'),
        'profile_digest': report.get('profile_digest'),
        'result_count': report.get('result_count'),
        'diagnostic_count': report.get('diagnostic_count'),
        'error_count': report.get('error_count'),
        'warning_count': report.get('warning_count'),
        'info_count': report.get('info_count'),
        'results': [
            {
                'diagnostic_count': item.get('diagnostic_count'),
                'error_count': item.get('error_count'),
                'warning_count': item.get('warning_count'),
                'info_count': item.get('info_count'),
                'gate': item.get('gate'),
                'digest': item.get('digest'),
            }
            for item in results
        ],
        'gate': report.get('gate'),
    })


def lint_v3_report(results: Iterable[LintResultV3],
                   profile: LintProfileV3 | None = None) -> dict[str, Any]:
    """Summarize linter v3 results with a stable, recomputable digest."""

    active = profile or DEFAULT_LINT_PROFILE
    items = list(results)
    counts = {
        'error': sum(item.error_count for item in items),
        'warning': sum(item.warning_count for item in items),
        'info': sum(item.info_count for item in items),
    }
    payload: dict[str, Any] = {
        'version': LINTER_V3_VERSION,
        'format': LINTER_V3_FORMAT,
        'profile': active.to_dict(),
        'profile_digest': active.digest(),
        'result_count': len(items),
        'diagnostic_count': sum(len(item.diagnostics) for item in items),
        'error_count': counts['error'],
        'warning_count': counts['warning'],
        'info_count': counts['info'],
        'results': [item.to_dict() for item in items],
        'gate': 'FAIL' if _decision(counts, active)['issues'] else 'PASS',
    }
    payload['digest'] = _report_digest(payload)
    return payload


def lint_v3_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute a deterministic PASS/FAIL decision from a linter report."""

    issues: list[str] = []
    if report.get('version') != LINTER_V3_VERSION:
        issues.append('version')
    if report.get('format') != LINTER_V3_FORMAT:
        issues.append('format')
    if report.get('gate') not in ('PASS', 'FAIL'):
        issues.append('report')
    digest = str(report.get('digest', ''))
    if len(digest) != 64:
        issues.append('digest')
    elif digest != _report_digest(report):
        issues.append('digest')
    for item in report.get('results', []):
        if len(str(item.get('digest', ''))) != 64:
            issues.append('result_digest')
    profile_data = report.get('profile') or DEFAULT_LINT_PROFILE.to_dict()
    try:
        profile = LintProfileV3(**profile_data)
    except Exception:
        issues.append('profile')
        profile = DEFAULT_LINT_PROFILE
    expected = _decision({
        'error': int(report.get('error_count', 0)),
        'warning': int(report.get('warning_count', 0)),
    }, profile)
    if report.get('gate') != expected['gate']:
        issues.append('gate')
    issues.extend(expected['issues'])
    return {'gate': 'PASS' if not issues else 'FAIL',
            'issues': sorted(set(issues))}


def build_linter_v3_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'LINTER_V3_VERSION': LINTER_V3_VERSION,
        'LINTER_V3_FORMAT': LINTER_V3_FORMAT,
        'LINTER_V3_RULES': LINTER_V3_RULES,
        'LintProfileV3': LintProfileV3,
        'DEFAULT_LINT_PROFILE': DEFAULT_LINT_PROFILE,
        'LintDiagnosticV3': LintDiagnosticV3,
        'LintResultV3': LintResultV3,
        'LinterV3Error': LinterV3Error,
        'lint_source_v3': lint_source_v3,
        'lint_file_v3': lint_file_v3,
        'linter_v3_capabilities': linter_v3_capabilities,
        'lint_v3_report': lint_v3_report,
        'lint_v3_gate': lint_v3_gate,
        'build_linter_v3_namespace': build_linter_v3_namespace,
    }


__all__ = [
    'LINTER_V3_VERSION', 'LINTER_V3_FORMAT', 'LINTER_V3_RULES',
    'LintProfileV3', 'DEFAULT_LINT_PROFILE', 'LintDiagnosticV3',
    'LintResultV3', 'LinterV3Error', 'lint_source_v3', 'lint_file_v3',
    'linter_v3_capabilities', 'lint_v3_report', 'lint_v3_gate',
    'build_linter_v3_namespace',
]
