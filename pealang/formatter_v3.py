"""Phase 83: deterministic formatter v3 for PeaLang developer tooling.

This module is additive to the existing ``pea fmt`` and ``PeaFormatter``
surfaces. It preserves comments and string contents, normalizes whitespace and
indentation, reports reviewable line edits, and verifies that formatting does not
change the compiled bytecode semantics. All digests exclude wall-clock values,
host paths, and original source text.
"""

from __future__ import annotations

import difflib
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .compiler import compile_source_to_bytecode

FORMATTER_V3_VERSION = '3.1.46'
FORMATTER_V3_FORMAT = 'pea-fmt-v3'
BRACE_STYLES = ('same_line', 'next_line')


class FormatterV3Error(Exception):
    """Raised when a formatter v3 profile or source input is invalid."""


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class FormatProfile:
    """A validated, serializable formatter v3 profile."""

    indent_size: int = 4
    max_line_length: int = 100
    brace_style: str = 'same_line'
    newline_at_eof: bool = True

    def __post_init__(self) -> None:
        if not 1 <= int(self.indent_size) <= 8:
            raise FormatterV3Error('indent_size must be between 1 and 8')
        if int(self.max_line_length) < 40:
            raise FormatterV3Error('max_line_length must be at least 40')
        if self.brace_style not in BRACE_STYLES:
            raise FormatterV3Error(
                'brace_style must be same_line or next_line')

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return _digest(self.to_dict())


DEFAULT_FORMAT_PROFILE = FormatProfile()


def formatter_v3_capabilities() -> dict[str, Any]:
    """Return the versioned formatter v3 capability set."""

    return {
        'version': FORMATTER_V3_VERSION,
        'format': FORMATTER_V3_FORMAT,
        'profile': DEFAULT_FORMAT_PROFILE.to_dict(),
        'options': [
            'indent_size', 'max_line_length', 'brace_style', 'newline_at_eof',
        ],
        'brace_styles': list(BRACE_STYLES),
        'preserves_comments': True,
        'idempotent': True,
        'parity_check': 'bytecode',
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


def _split_comment(line: str) -> tuple[str, str]:
    if "'''" in line or '"""' in line:
        return line, ''
    mask = _string_mask(line)
    for index, char in enumerate(line):
        if not mask[index]:
            continue
        if char == '#' or (char == '/' and line[index + 1:index + 2] == '/'):
            return line[:index], line[index:].strip()
    return line, ''


def _brace_delta(code: str) -> int:
    mask = _string_mask(code)
    opens = sum(1 for i, char in enumerate(code) if mask[i] and char == '{')
    closes = sum(1 for i, char in enumerate(code) if mask[i] and char == '}')
    return opens - closes


def _leading_closes(code: str) -> int:
    count = 0
    for char in code.strip():
        if char == '}':
            count += 1
        elif not char.isspace():
            break
    return count


def _normalize_code(code: str) -> str:
    text = code.strip()
    if not text or "'''" in text or '"""' in text:
        return text
    mask = _string_mask(text)
    out: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if not mask[index]:
            out.append(char)
            index += 1
            continue
        if char.isspace():
            end = index
            while end < len(text) and mask[end] and text[end].isspace():
                end += 1
            if (out and out[-1] not in '([{.' and end < len(text)
                    and text[end] not in ',;)]}.:'):
                out.append(' ')
            index = end
            continue
        if char in ',;:':
            while out and out[-1] == ' ':
                out.pop()
            out.append(char)
            end = index + 1
            while end < len(text) and mask[end] and text[end].isspace():
                end += 1
            if char == ',' and end < len(text) and text[end] not in ')]}':
                out.append(' ')
            elif char == ':' and end < len(text) and mask[end]:
                out.append(' ')
            index = end
            continue
        if char in ')]}.([':
            while out and out[-1] == ' ':
                out.pop()
            if char == '}' and out and out[-1] != '{':
                out.append(' ')
            out.append(char)
            end = index + 1
            if char == '}':
                while end < len(text) and mask[end] and text[end].isspace():
                    end += 1
                if end < len(text) and (text[end].isalnum() or text[end] == '_'):
                    out.append(' ')
            index = end if char == '}' else index + 1
            continue
        if char == '{':
            if out and out[-1] not in '([{ ':
                out.append(' ')
            out.append(char)
            end = index + 1
            while end < len(text) and mask[end] and text[end].isspace():
                end += 1
            if end < len(text) and text[end] not in '}]':
                out.append(' ')
            index = end
            continue
        if char in '=<>!+-*/%':
            operator = char
            span = 1
            pair = text[index:index + 2]
            if pair == '->' and mask[index + 1:index + 2] == [True]:
                operator, span = '->', 2
            elif char in '=<>!' and pair.endswith('=') and mask[index + 1:index + 2] == [True]:
                operator, span = char + '=', 2
            previous = out[-1] if out else ''
            unary = (operator in ('+', '-', '!')
                     and (not out or previous in '([{,=:<>!+-*/%'))
            if not unary:
                while out and out[-1] == ' ':
                    out.pop()
                if out:
                    out.append(' ')
            out.append(operator)
            end = index + span
            while end < len(text) and mask[end] and text[end].isspace():
                end += 1
            if end < len(text) and text[end] not in ')]},;':
                out.append(' ')
            index = end
            continue
        out.append(char)
        index += 1
    return ''.join(out).strip()


def _format_text(source: str, active: FormatProfile) -> str:
    lines = source.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    while lines and lines[-1] == '':
        lines.pop()
    out: list[str] = []
    depth = 0
    blanks = 0
    for raw in lines:
        if not raw.strip():
            if out and out[-1] != '' and blanks == 0:
                out.append('')
            blanks += 1
            continue
        blanks = 0
        code, comment = _split_comment(raw)
        stripped = code.strip()
        if not stripped:
            if comment:
                out.append(' ' * (depth * active.indent_size) + comment)
            continue
        indent = max(0, depth - _leading_closes(stripped))
        formatted_line = _normalize_code(stripped)
        prefix = ' ' * (indent * active.indent_size)
        if (active.brace_style == 'next_line'
                and formatted_line.endswith('{')
                and len(formatted_line) > 1):
            before = formatted_line[:-1].rstrip()
            out.append(prefix + before + ((' ' + comment) if comment else ''))
            out.append(prefix + '{')
        else:
            out.append(prefix + formatted_line
                       + ((' ' + comment) if comment else ''))
        depth = max(0, depth + _brace_delta(formatted_line))
    while out and out[0] == '':
        out.pop()
    while out and out[-1] == '':
        out.pop()
    formatted = '\n'.join(out)
    if active.newline_at_eof and formatted:
        formatted += '\n'
    return formatted


def format_source_v3(source: str, profile: FormatProfile | None = None,
                     source_name: str = '<input>') -> FormatResult:
    """Format source text and return deterministic, reviewable evidence."""

    if not isinstance(source, str):
        raise FormatterV3Error('source must be text')
    active = profile or DEFAULT_FORMAT_PROFILE
    normalized = source.replace('\r\n', '\n').replace('\r', '\n')
    formatted = _format_text(normalized, active)
    parity = verify_format_parity(normalized, formatted)
    idempotent = _format_text(formatted, active) == formatted
    diff = tuple(difflib.unified_diff(
        normalized.splitlines(), formatted.splitlines(),
        fromfile=f'{source_name}:before', tofile=f'{source_name}:after',
        n=0, lineterm='',
    ))
    long_lines = tuple(index + 1 for index, line in enumerate(formatted.splitlines())
                       if len(line) > active.max_line_length)
    digest = _digest({
        'version': FORMATTER_V3_VERSION,
        'format': FORMATTER_V3_FORMAT,
        'profile': active.digest(),
        'formatted': formatted,
        'long_lines': list(long_lines),
        'parity': parity,
        'idempotent': idempotent,
    })
    return FormatResult(
        version=FORMATTER_V3_VERSION, format=FORMATTER_V3_FORMAT,
        profile=active.to_dict(), source_name=source_name,
        changed=normalized != formatted, line_count=len(formatted.splitlines()),
        long_lines=long_lines, diff=diff, formatted=formatted,
        parity=parity, idempotent=idempotent, digest=digest,
    )


def format_file_v3(path: str | Path,
                   profile: FormatProfile | None = None) -> FormatResult:
    """Format one file and return its evidence without writing changes."""

    target = Path(path)
    source = target.read_text(encoding='utf-8')
    return format_source_v3(source, profile, target.name)


def _code_payload(code: Any) -> dict[str, Any]:
    return {
        'name': code.name,
        'params': list(code.params),
        'defaults': code.defaults,
        'instructions': [
            [instruction.op, instruction.arg]
            for instruction in code.instructions
        ],
    }


def _semantic_fingerprint(source: str) -> str:
    module = compile_source_to_bytecode(source, '<fmt-v3>')
    return _digest({
        'constants': module.constants,
        'code': _code_payload(module.code),
        'functions': {
            name: _code_payload(code)
            for name, code in sorted(module.functions.items())
        },
    })


def verify_format_parity(original: str, formatted: str) -> dict[str, Any]:
    """Confirm that formatting did not change compiled bytecode semantics."""

    issues: list[str] = []
    before: str | None = None
    after: str | None = None
    try:
        before = _semantic_fingerprint(original)
    except Exception:
        issues.append('original')
    try:
        after = _semantic_fingerprint(formatted)
    except Exception:
        issues.append('formatted')
    if before is not None and after is not None and before != after:
        issues.append('semantics')
    return {
        'passed': not issues,
        'issues': issues,
        'fingerprints': {'original': before, 'formatted': after},
    }


@dataclass(frozen=True)
class FormatResult:
    """Reviewable outcome of one formatter v3 operation."""

    version: str
    format: str
    profile: dict[str, Any]
    source_name: str
    changed: bool
    line_count: int
    long_lines: tuple[int, ...]
    diff: tuple[str, ...]
    formatted: str
    parity: dict[str, Any]
    idempotent: bool
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
            'format': self.format,
            'profile': self.profile,
            'source_name': self.source_name,
            'changed': self.changed,
            'line_count': self.line_count,
            'long_lines': list(self.long_lines),
            'diff': list(self.diff),
            'formatted': self.formatted,
            'parity': self.parity,
            'idempotent': self.idempotent,
            'digest': self.digest,
        }


def formatter_v3_report(results: Iterable[FormatResult],
                        profile: FormatProfile | None = None
                        ) -> dict[str, Any]:
    """Summarize formatter v3 results with a stable digest."""

    active = profile or DEFAULT_FORMAT_PROFILE
    items = list(results)
    payload: dict[str, Any] = {
        'version': FORMATTER_V3_VERSION,
        'format': FORMATTER_V3_FORMAT,
        'profile_digest': active.digest(),
        'result_count': len(items),
        'changed_count': sum(1 for item in items if item.changed),
        'results': [item.to_dict() for item in items],
        'gate': 'PASS',
    }
    summary = [{
        'changed': item.changed,
        'line_count': item.line_count,
        'long_lines': list(item.long_lines),
        'parity': item.parity,
        'idempotent': item.idempotent,
        'digest': item.digest,
    } for item in items]
    payload['digest'] = _digest({
        'version': payload['version'],
        'format': payload['format'],
        'profile_digest': payload['profile_digest'],
        'result_count': payload['result_count'],
        'changed_count': payload['changed_count'],
        'results': summary,
        'gate': payload['gate'],
    })
    return payload


def formatter_v3_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute a deterministic PASS/FAIL decision from a formatter report."""

    issues: list[str] = []
    if report.get('version') != FORMATTER_V3_VERSION:
        issues.append('version')
    if report.get('format') != FORMATTER_V3_FORMAT:
        issues.append('format')
    if report.get('gate') != 'PASS':
        issues.append('report')
    if len(str(report.get('digest', ''))) != 64:
        issues.append('digest')
    for item in report.get('results', []):
        if not item.get('idempotent'):
            issues.append('idempotent')
        if not item.get('parity', {}).get('passed'):
            issues.append('parity')
    return {'gate': 'PASS' if not issues else 'FAIL',
            'issues': sorted(set(issues))}


def build_formatter_v3_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'FORMATTER_V3_VERSION': FORMATTER_V3_VERSION,
        'FORMATTER_V3_FORMAT': FORMATTER_V3_FORMAT,
        'BRACE_STYLES': BRACE_STYLES,
        'FormatProfile': FormatProfile,
        'DEFAULT_FORMAT_PROFILE': DEFAULT_FORMAT_PROFILE,
        'FormatResult': FormatResult,
        'FormatterV3Error': FormatterV3Error,
        'format_source_v3': format_source_v3,
        'format_file_v3': format_file_v3,
        'verify_format_parity': verify_format_parity,
        'formatter_v3_capabilities': formatter_v3_capabilities,
        'formatter_v3_report': formatter_v3_report,
        'formatter_v3_gate': formatter_v3_gate,
        'build_formatter_v3_namespace': build_formatter_v3_namespace,
    }


__all__ = [
    'FORMATTER_V3_VERSION', 'FORMATTER_V3_FORMAT', 'BRACE_STYLES',
    'FormatProfile', 'DEFAULT_FORMAT_PROFILE', 'FormatResult',
    'FormatterV3Error', 'format_source_v3', 'format_file_v3',
    'verify_format_parity', 'formatter_v3_capabilities',
    'formatter_v3_report', 'formatter_v3_gate',
    'build_formatter_v3_namespace',
]
