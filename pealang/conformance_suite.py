"""Curated portable conformance suite for the PeaLang language core.

The 0.40 harness in :mod:`pealang.conformance` generates arithmetic cases and
compares the interpreter with the VM. This module adds a small, deterministic
suite whose cases cover the language-core features introduced in Wave 1. Each
case declares a single portable expectation that is checked on every runtime
that supports its kind.

Case kinds:

``runtime``
    The source must produce the same normalized output on the interpreter and
    the bytecode VM.
``macro``
    The source is expanded with the case's safe macro expander and then run on
    the bytecode VM.
``static``
    The source must produce the declared diagnostic codes.
``module``
    The source is written to a temporary project and checked with project
    analysis, which reports cross-file diagnostics such as ``M201``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from .compiler import compile_source_to_bytecode, compile_source_with_macros
from .metaprogramming import SafeMacro, SafeMacroExpander
from .runtime import execute
from .type_system import SemanticAnalyzer, analyze_project, check_resource_scopes
from .vm import VirtualMachine

SUITE_VERSION = '5.3.0'


@dataclass(frozen=True)
class ConformanceCaseV2:
    """One portable conformance expectation."""

    id: str
    name: str
    category: str
    kind: str
    source: str
    expected: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    expander: Any = None


def _macro_expander():
    expander = SafeMacroExpander()
    expander.define(SafeMacro('twice', 'print double $value', 'print $value + $value'))
    return expander


SUITE_V2 = (
    ConformanceCaseV2('V001', 'arithmetic precedence', 'core', 'runtime',
                      'let x = 2 + 3 * 4\nprint x', ('14',)),
    ConformanceCaseV2('V002', 'function calls', 'core', 'runtime',
                      'function add(a,b){return a+b}\nprint add(2,3)', ('5',)),
    ConformanceCaseV2('V003', 'structured error values', 'errors', 'runtime',
                      'try { throw error("UserError","boom") } catch e { print e["kind"] }',
                      ('UserError',)),
    ConformanceCaseV2('V004', 'iterator consumption', 'iterators', 'runtime',
                      'let it = iter([1,2])\nprint next(it)\nprint next(it)', ('1', '2')),
    ConformanceCaseV2('V005', 'string concatenation', 'strings', 'runtime',
                      'print "hello" + " world"', ('hello world',)),
    ConformanceCaseV2('V006', 'dictionary indexing', 'collections', 'runtime',
                      'let d = {"a": 1}\nprint d["a"]', ('1',)),
    ConformanceCaseV2('V007', 'resource scope binding', 'scopes', 'runtime',
                      'using r = [1,2] {\n print r[0]\n}\nprint "done"', ('1', 'done')),
    ConformanceCaseV2('V008', 'safe macro expansion', 'macros', 'macro',
                      'print double 3', ('6',), expander=_macro_expander()),
    ConformanceCaseV2('V009', 'assignment type check', 'types', 'static',
                      'let x: Int = "bad"', diagnostics=('T201',)),
    ConformanceCaseV2('V010', 'iterator contract', 'iterators', 'static',
                      'for x in 3 { print x }', diagnostics=('I201',)),
    ConformanceCaseV2('V011', 'await contract', 'async', 'static',
                      'let n = 3\nawait n', diagnostics=('A201',)),
    ConformanceCaseV2('V012', 'scope binding check', 'scopes', 'static',
                      'using r = x { r = 3 }', diagnostics=('R202',)),
    ConformanceCaseV2('V013', 'unresolved module import', 'modules', 'module',
                      'import "missing.pea"\n', diagnostics=('M201',)),
)


def _normalize(values):
    """Return a portable tuple of string outputs from any runtime."""

    if values is None:
        return None
    result = []
    for value in values:
        if isinstance(value, bool):
            result.append('true' if value else 'false')
        elif isinstance(value, (dict, list, tuple)):
            result.append(json.dumps(value, sort_keys=True, default=str))
        else:
            result.append(str(value))
    return tuple(result)


def validate_case(case: ConformanceCaseV2) -> list[str]:
    """Return a list of definition problems for *case*."""

    issues = []
    if case.kind not in ('runtime', 'macro', 'static', 'module'):
        issues.append(f"{case.id}: unknown case kind '{case.kind}'")
    if case.kind in ('runtime', 'macro') and not case.expected:
        issues.append(f'{case.id}: runtime cases require expected output')
    if case.kind in ('static', 'module') and not case.diagnostics:
        issues.append(f'{case.id}: static cases require expected diagnostic codes')
    if case.kind == 'macro' and case.expander is None:
        issues.append(f'{case.id}: macro cases require an expander')
    return issues


def run_case(case: ConformanceCaseV2) -> dict[str, Any]:
    """Run one case and return a portable result record."""

    result = {
        'id': case.id,
        'name': case.name,
        'category': case.category,
        'kind': case.kind,
        'expected': list(case.expected),
        'diagnostics': list(case.diagnostics),
        'interpreter': None,
        'vm': None,
        'static': None,
        'ok': False,
    }
    try:
        if case.kind == 'runtime':
            interpreter_out = []
            execute(case.source, output=interpreter_out.append)
            vm_out = []
            vm = VirtualMachine(vm_out.append)
            vm.run(compile_source_to_bytecode(case.source, '<conformance-v2>'))
            result['interpreter'] = list(_normalize(interpreter_out))
            result['vm'] = list(_normalize(vm_out))
            result['ok'] = result['interpreter'] == list(case.expected) == result['vm']
        elif case.kind == 'macro':
            module = compile_source_with_macros(case.source, '<conformance-v2>', case.expander)
            vm_out = []
            VirtualMachine(vm_out.append).run(module)
            result['vm'] = list(_normalize(vm_out))
            result['ok'] = result['vm'] == list(case.expected)
        elif case.kind == 'static':
            codes = {d.code for d in SemanticAnalyzer().analyze(case.source).diagnostics}
            codes.update(d.code for d in check_resource_scopes(case.source)['diagnostics'])
            result['static'] = sorted(codes)
            result['ok'] = set(case.diagnostics).issubset(codes)
        elif case.kind == 'module':
            with TemporaryDirectory() as root:
                path = Path(root) / 'case.pea'
                path.write_text(case.source, encoding='utf-8')
                analysis = analyze_project([str(path)])
            codes = {d.code for _, d in analysis['diagnostics']}
            result['static'] = sorted(codes)
            result['ok'] = set(case.diagnostics).issubset(codes)
        else:
            result['error'] = f"unknown case kind '{case.kind}'"
    except Exception as exc:
        result['error'] = f'{type(exc).__name__}: {exc}'
    return result


def run_conformance_suite_v2(cases=None) -> dict[str, Any]:
    """Run the curated suite, or *cases* when provided, and return a report."""

    selected = list(cases) if cases is not None else list(SUITE_V2)
    issues = [issue for case in selected for issue in validate_case(case)]
    results = [run_case(case) for case in selected]
    passed = sum(1 for item in results if item['ok'])
    return {
        'version': SUITE_VERSION,
        'target': len(results),
        'passed': passed,
        'failed': len(results) - passed,
        'definition_issues': issues,
        'runtimes': {
            'interpreter': sum(item['interpreter'] is not None for item in results),
            'vm': sum(item['vm'] is not None for item in results),
            'static': sum(item['static'] is not None for item in results),
            'macros': sum(1 for item in results if item['kind'] == 'macro' and item['ok']),
        },
        'results': results,
        'ok': passed == len(results) and not issues,
    }


def conformance_report_v2() -> dict[str, Any]:
    """Return the full v2 conformance report."""

    return {'version': SUITE_VERSION, 'suite': run_conformance_suite_v2()}


def conformance_gate_v2(report=None) -> dict[str, Any]:
    """Reduce a v2 report to a stable pass/fail gate."""

    report = report or conformance_report_v2()
    suite = report['suite']
    return {
        'gate': 'PASS' if suite['ok'] else 'FAIL',
        'passed': suite['passed'],
        'failed': suite['failed'],
        'target': suite['target'],
    }
