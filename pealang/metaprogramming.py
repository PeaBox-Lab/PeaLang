"""Explicit, bounded, hygiene-aware macro expansion for PeaLang source.

The legacy string macros in :mod:`pealang.type_system` are retained for
compatibility. This module provides a stricter expansion layer that validates
definitions, bounds expansion work, and supports capture-avoiding template
markers (``@name``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MAX_SOURCE_LENGTH = 250_000
MAX_PATTERN_LENGTH = 4_000
MAX_TEMPLATE_LENGTH = 8_000
MAX_CAPTURE_LENGTH = 4_000
MAX_VARIABLES = 16
MAX_MACROS = 32
MAX_PASSES = 4
MAX_TOTAL_EXPANSIONS = 512

_IDENT = re.compile(r'^[A-Za-z_]\w*$')
_VARIABLE = re.compile(r'\$([A-Za-z_]\w*)')
_MARKER = re.compile(r'@([A-Za-z_]\w*)')
_PAIRS = {'(': ')', '[': ']', '{': '}'}
_CLOSERS = {')': '(', ']': '[', '}': '{'}


@dataclass(frozen=True)
class MacroIssue:
    """A validation or expansion issue reported by the safe expander."""

    code: str
    message: str
    line: int = 0
    severity: str = 'error'

    def __str__(self):
        where = f' (line {self.line})' if self.line else ''
        return f'{self.code}: {self.message}{where}'


@dataclass(frozen=True)
class MacroExpansionResult:
    """Expanded source together with the macros and issues observed."""

    source: str
    applied: tuple[str, ...] = ()
    issues: tuple[MacroIssue, ...] = ()

    @property
    def ok(self):
        return not any(issue.severity == 'error' for issue in self.issues)


class MacroExpansionError(Exception):
    """Raised by strict expansion helpers when a macro issue is fatal."""


@dataclass(frozen=True)
class SafeMacro:
    """A bounded source macro with named metavariables and hygiene markers."""

    name: str
    pattern: str
    template: str
    hygiene: bool = True
    max_uses: int = 32


def _line_at(text, index):
    return text.count('\n', 0, index) + 1


def _delimiter_issue(text, code, label):
    stack = []
    quote = None
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char == '/' and index + 1 < len(text) and text[index + 1] == '/':
            while index < len(text) and text[index] != '\n':
                index += 1
            continue
        if char in ("'", '"'):
            quote = char
        elif char in _PAIRS:
            stack.append((char, index))
        elif char in _CLOSERS:
            if not stack or stack[-1][0] != _CLOSERS[char]:
                return MacroIssue(code, f'Unbalanced delimiter in {label}', _line_at(text, index))
            stack.pop()
        index += 1
    if stack:
        return MacroIssue(code, f'Unclosed delimiter in {label}', _line_at(text, stack[-1][1]))
    return None


def validate_macro(macro):
    """Return all definition issues for *macro* without raising."""
    issues = []
    if not _IDENT.fullmatch(macro.name):
        issues.append(MacroIssue('MG001', f"Invalid macro name '{macro.name}'"))
    if len(macro.pattern) > MAX_PATTERN_LENGTH:
        issues.append(MacroIssue('MG001', f"Macro '{macro.name}' pattern is too long"))
    if len(macro.template) > MAX_TEMPLATE_LENGTH:
        issues.append(MacroIssue('MG001', f"Macro '{macro.name}' template is too long"))
    if macro.max_uses < 1 or macro.max_uses > MAX_TOTAL_EXPANSIONS:
        issues.append(MacroIssue('MG001', f"Macro '{macro.name}' max_uses is out of range"))
    if r'\$' in macro.pattern or r'\$' in macro.template:
        issues.append(MacroIssue('MG105', f"Macro '{macro.name}' cannot escape metavariables"))

    pattern_vars = set(_VARIABLE.findall(macro.pattern))
    template_vars = set(_VARIABLE.findall(macro.template))
    if not pattern_vars:
        issues.append(MacroIssue('MG102', f"Macro '{macro.name}' pattern declares no metavariables"))
    if len(pattern_vars) > MAX_VARIABLES:
        issues.append(MacroIssue('MG102', f"Macro '{macro.name}' declares too many metavariables"))
    for name in sorted(template_vars - pattern_vars):
        issues.append(MacroIssue('MG102', f"Macro '{macro.name}' template uses unknown metavariable '${name}'"))
    for name in sorted(pattern_vars):
        if name.startswith('__'):
            issues.append(MacroIssue('MG102', f"Macro '{macro.name}' cannot reserve metavariable '${name}'"))
    if not macro.hygiene and _MARKER.search(macro.template):
        issues.append(MacroIssue('MG104', f"Macro '{macro.name}' uses hygiene markers with hygiene disabled"))
    for label, text in (('pattern', macro.pattern), ('template', macro.template)):
        issue = _delimiter_issue(text, 'MG101', f"{macro.name} {label}")
        if issue:
            issues.append(issue)
    return issues


def _escape_literal(text):
    parts = []
    for char in text:
        if char.isspace():
            parts.append(r'\s+')
        else:
            parts.append(re.escape(char))
    return ''.join(parts)


def _compile_pattern(macro):
    names = []
    parts = []
    for index, part in enumerate(_VARIABLE.split(macro.pattern)):
        if index % 2:
            names.append(part)
            parts.append(f'(?P<c{len(names) - 1}>.+?)')
        else:
            parts.append(_escape_literal(part))
    body = ''.join(parts)
    regex = r'^[ \t]*' + body + r'[ \t]*(?://[^\n]*)?$'
    return re.compile(regex, re.MULTILINE | re.DOTALL), tuple(names)


def _render(macro, captures, expander):
    result = macro.template
    if macro.hygiene:
        for name in _MARKER.findall(result):
            result = result.replace('@' + name, expander.gensym(name))
    for name, value in captures.items():
        result = result.replace('$' + name, value)
    return result


class SafeMacroExpander:
    """Validated macro expander with bounded work and capture-avoiding markers."""

    def __init__(self):
        self.macros = {}
        self.issues = []
        self.gen_sym_counter = 0
        self.expansions = 0

    def gensym(self, prefix='gen'):
        self.gen_sym_counter += 1
        return f'__{prefix}_{self.gen_sym_counter}'

    def define(self, macro):
        if len(self.macros) >= MAX_MACROS:
            self.issues.append(MacroIssue('MG001', f'Macro limit of {MAX_MACROS} exceeded'))
            return
        issues = validate_macro(macro)
        if issues:
            self.issues.extend(issues)
            return
        self.macros[macro.name] = macro

    def expand(self, source):
        if len(source) > MAX_SOURCE_LENGTH:
            issue = MacroIssue('MG202', 'Source exceeds safe macro expansion length limit')
            return MacroExpansionResult(source, (), tuple(self.issues) + (issue,))
        self.expansions = 0
        result = source
        applied = []
        issues = list(self.issues)
        changed = False
        for _ in range(MAX_PASSES):
            changed = False
            for macro in self.macros.values():
                result, names, macro_issues = self._expand_once(result, macro)
                applied.extend(names)
                issues.extend(macro_issues)
                if names:
                    changed = True
            if not changed:
                return MacroExpansionResult(result, tuple(applied), tuple(issues))
        if changed:
            issues.append(MacroIssue('MG203', 'Macro expansion did not converge within the safe pass limit'))
        return MacroExpansionResult(result, tuple(applied), tuple(issues))

    def expand_or_raise(self, source):
        result = self.expand(source)
        if not result.ok:
            detail = '; '.join(str(issue) for issue in result.issues if issue.severity == 'error')
            raise MacroExpansionError(detail)
        return result.source

    def _expand_once(self, source, macro):
        regex, names = _compile_pattern(macro)
        applied = []
        issues = []
        used = 0

        def replacer(match):
            nonlocal used
            if used >= macro.max_uses or self.expansions >= MAX_TOTAL_EXPANSIONS:
                issues.append(MacroIssue('MG201', f"Macro '{macro.name}' expansion limit reached"))
                return match.group(0)
            captures = {}
            for index, name in enumerate(names):
                value = match.group(index + 1).strip()
                if len(value) > MAX_CAPTURE_LENGTH:
                    issues.append(MacroIssue('MG202', f"Capture '${name}' exceeds safe length limit"))
                    return match.group(0)
                delimiter_issue = _delimiter_issue(value, 'MG101', f"capture '${name}'")
                if delimiter_issue:
                    issues.append(delimiter_issue)
                    return match.group(0)
                if name in captures and captures[name] != value:
                    issues.append(MacroIssue('MG103', f"Repeated capture '${name}' has inconsistent values"))
                    return match.group(0)
                captures[name] = value
            rendered = _render(macro, captures, self)
            if len(rendered) > MAX_TEMPLATE_LENGTH * 4:
                issues.append(MacroIssue('MG202', f"Macro '{macro.name}' expansion is too large"))
                return match.group(0)
            used += 1
            self.expansions += 1
            applied.append(macro.name)
            return rendered

        return regex.sub(replacer, source), applied, issues


def expand_source_macros(source, expander=None):
    """Expand *source* with *expander*, raising on any fatal macro issue."""
    return (expander or STANDARD_SAFE_MACROS).expand_or_raise(source)


class _StandardSafeMacros(SafeMacroExpander):
    def __init__(self):
        super().__init__()
        self.define(SafeMacro(
            name='try_expr',
            pattern=r'try $expr catch $name => $fallback',
            template='try { $expr } catch $name { $fallback }',
        ))
        self.define(SafeMacro(
            name='unless',
            pattern='unless $cond { $body }',
            template='if (!($cond)) { $body }',
        ))


STANDARD_SAFE_MACROS = _StandardSafeMacros()
