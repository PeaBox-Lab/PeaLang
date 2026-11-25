"""Phase 69: curated portable conformance suite and CI gate."""

import json
import subprocess
import sys
from pathlib import Path

from pealang import (
    ConformanceCaseV2,
    conformance_gate_v2,
    conformance_report_v2,
    run_conformance_suite_v2,
    validate_case,
)
from pealang.conformance import conformance_report
from pealang.conformance_suite import SUITE_V2, SUITE_VERSION, _normalize, run_case
from pealang.help import help as pea_help


def test_curated_suite_passes():
    report = run_conformance_suite_v2()
    assert report['version'] == SUITE_VERSION
    assert report['target'] == len(SUITE_V2) == 13
    assert report['failed'] == 0
    assert report['ok'] is True
    assert report['definition_issues'] == []
    assert report['runtimes']['interpreter'] >= 7
    assert report['runtimes']['vm'] >= 8
    assert report['runtimes']['static'] >= 5


def test_report_and_gate_are_stable():
    report = conformance_report_v2()
    gate = conformance_gate_v2(report)
    assert report['suite']['ok'] is True
    assert gate == {'gate': 'PASS', 'passed': 13, 'failed': 0, 'target': 13}


def test_runtime_case_detects_output_mismatch():
    case = ConformanceCaseV2('X001', 'bad sum', 'core', 'runtime', 'print 1 + 1', ('3',))
    result = run_case(case)
    assert result['ok'] is False
    assert result['interpreter'] == ['2']
    assert result['vm'] == ['2']


def test_static_case_detects_missing_diagnostic():
    case = ConformanceCaseV2('X002', 'missing code', 'types', 'static',
                             'let x: Int = "bad"', diagnostics=('A201',))
    result = run_case(case)
    assert result['ok'] is False
    assert 'T201' in result['static']
    assert 'A201' not in result['static']


def test_macro_case_expands_then_compiles():
    case = next(item for item in SUITE_V2 if item.kind == 'macro')
    result = run_case(case)
    assert result['ok'] is True
    assert result['vm'] == ['6']
    assert result['interpreter'] is None


def test_definition_validation_reports_invalid_cases():
    assert validate_case(ConformanceCaseV2('X3', 'bad kind', 'x', 'other', 'print 1'))
    assert validate_case(ConformanceCaseV2('X4', 'no output', 'x', 'runtime', 'print 1'))
    assert validate_case(ConformanceCaseV2('X5', 'no codes', 'x', 'static', 'print 1'))
    assert validate_case(ConformanceCaseV2('X6', 'no expander', 'x', 'macro', 'print double 1', ('1',)))
    assert validate_case(SUITE_V2[0]) == []


def test_custom_cases_run_independently_of_curated_suite():
    cases = [ConformanceCaseV2('X007', 'one', 'core', 'runtime', 'print 1', ('1',))]
    report = run_conformance_suite_v2(cases)
    assert report['target'] == 1
    assert report['passed'] == 1
    assert report['runtimes']['interpreter'] == 1


def test_normalization_is_portable():
    assert _normalize([True, False, [1, 2], {'b': 2, 'a': 1}]) == (
        'true', 'false', '[1, 2]', '{"a": 1, "b": 2}',
    )


def test_cli_conformance_v2_prints_passing_json():
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'conformance-v2'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['suite']['ok'] is True
    assert conformance_gate_v2(report)['gate'] == 'PASS'


def test_legacy_conformance_harness_still_passes_and_help_documents_v2():
    legacy = conformance_report()
    assert legacy['conformance']['ok'] is True
    assert legacy['fuzz']['ok'] is True
    text = pea_help('conformance')
    assert 'conformance-v2' in text
    assert 'PASS/FAIL' in text
