"""Phase 84: deterministic linter v3 with stable rules and gates."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
import pytest
from pealang.analysis import build_analysis_namespace
from pealang.compatibility import Stability, feature_status
from pealang.core_freeze import core_freeze_report
from pealang.help import help as pea_help
from pealang.linter_v3 import (DEFAULT_LINT_PROFILE, LINTER_V3_FORMAT,
                               LINTER_V3_RULES, LINTER_V3_VERSION,
                               LintProfileV3, LinterV3Error,
                               build_linter_v3_namespace, lint_source_v3,
                               linter_v3_capabilities, lint_v3_gate,
                               lint_v3_report)
from pealang.specification import SPEC_VERSION

SOURCE = '''function BadName(a,b){
let Upper=1   # TODO
if a { return b }
return 2
let dead=3
}
function Debug(){
print("DEBUG start")
}
'''
LINE_SOURCE = 'let ok = 1   \n# TODO marker\nlet long = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"\n'


def test_linter_v3_constants_capabilities_and_profile_validation():
    caps = linter_v3_capabilities()
    assert LINTER_V3_VERSION == pealang.LINTER_V3_VERSION == '3.1.47'
    assert LINTER_V3_FORMAT == pealang.LINTER_V3_FORMAT == 'pea-lint-v3'
    assert caps == linter_v3_capabilities()
    assert caps['version'] == '3.1.47'
    assert caps['deterministic_order'] is True
    assert caps['fix_hints'] is True
    assert caps['recomputed_gate'] is True
    assert len(caps['rules']) == 9
    assert [item['code'] for item in caps['rules']] == [
        item[0] for item in LINTER_V3_RULES
    ]
    assert DEFAULT_LINT_PROFILE.digest() == LintProfileV3().digest()
    with pytest.raises(LinterV3Error):
        LintProfileV3(max_line_length=39)
    with pytest.raises(LinterV3Error):
        LintProfileV3(max_complexity=0)


def test_line_rules_emit_stable_fix_hints():
    profile = LintProfileV3(max_line_length=40)
    result = lint_source_v3(LINE_SOURCE, profile, 'C:\\work\\app.pea')
    found = {item.rule: item for item in result.diagnostics}
    assert set(found) == {'L301', 'L302', 'L303'}
    assert found['L301'].line == 3
    assert found['L301'].severity == 'warning'
    assert found['L302'].line == 1
    assert found['L302'].fix == 'let ok = 1'
    assert found['L303'].line == 2
    assert found['L303'].col == 3
    assert len(found['L302'].fingerprint()) == 64
    assert lint_source_v3(LINE_SOURCE, profile, '/other/app.pea').digest == result.digest


def test_ast_rules_cover_naming_complexity_dead_code_and_debug_prints():
    profile = LintProfileV3(max_complexity=1)
    result = lint_source_v3(SOURCE, profile)
    assert [item.rule for item in result.diagnostics] == [
        'L304', 'L307', 'L305', 'L303', 'L308', 'L304', 'L306',
    ]
    assert result.warning_count == 5
    assert result.info_count == 2
    assert result.error_count == 0
    assert result.gate == 'PASS'
    assert all(item.source_name == '<input>' for item in result.diagnostics)
    assert all(item.line >= 1 and item.col >= 1 for item in result.diagnostics)


def test_parse_error_is_a_deterministic_error_diagnostic():
    result = lint_source_v3('function f({')
    assert [item.rule for item in result.diagnostics] == ['L309']
    assert result.diagnostics[0].severity == 'error'
    assert result.diagnostics[0].message.startswith('Parse error: ')
    assert result.error_count == 1
    assert result.gate == 'FAIL'
    report = lint_v3_report([result])
    assert lint_v3_gate(report)['gate'] == 'FAIL'
    assert 'errors' in lint_v3_gate(report)['issues']


def test_report_and_gate_are_deterministic_and_recomputed():
    profile = LintProfileV3(max_complexity=1)
    first = lint_source_v3(SOURCE, profile, 'C:\\work\\app.pea')
    second = lint_source_v3(SOURCE, profile, '/other/app.pea')
    assert first.source_name != second.source_name
    assert first.digest == second.digest
    report = lint_v3_report([first], profile)
    second_report = lint_v3_report([second], profile)
    assert report['digest'] == second_report['digest']
    assert report['diagnostic_count'] == second_report['diagnostic_count']
    assert report['results'][0]['source_name'] != second_report['results'][0]['source_name']
    assert report['version'] == '3.1.47'
    assert report['format'] == 'pea-lint-v3'
    assert report['result_count'] == 1
    assert report['diagnostic_count'] == 7
    assert len(report['digest']) == 64
    assert lint_v3_gate(report) == {'gate': 'PASS', 'issues': []}
    assert 'version' in lint_v3_gate({**report, 'version': 'old'})['issues']
    assert 'format' in lint_v3_gate({**report, 'format': 'old'})['issues']
    assert 'digest' in lint_v3_gate({**report, 'digest': 'short'})['issues']
    assert 'digest' in lint_v3_gate({**report, 'digest': '0' * 64})['issues']
    assert 'gate' in lint_v3_gate({**report, 'gate': 'FAIL'})['issues']
    strict_report = lint_v3_report([first], LintProfileV3(
        max_complexity=1, fail_on_warning=True,
    ))
    assert strict_report['gate'] == 'FAIL'
    assert lint_v3_gate(strict_report)['issues'] == ['warnings']


def test_cli_capabilities_check_emit_and_strict_gate(tmp_path):
    root = Path(__file__).resolve().parent.parent
    caps_result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'lint-v3', '--capabilities'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert caps_result.returncode == 0, caps_result.stderr
    assert json.loads(caps_result.stdout)['version'] == '3.1.47'
    source = tmp_path / 'app.pea'
    report_path = tmp_path / 'lint.json'
    source.write_text('function BadName(){return 1}\nlet Upper=1   \n', encoding='utf-8')
    checked = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'lint-v3', str(source),
         '--check', '--emit', str(report_path)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    assert report['version'] == '3.1.47'
    assert report['diagnostic_count'] == 3
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(report_path.read_text(encoding='utf-8')) == report
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'lint-v3', str(source),
         '--check', '--fail-on-warning'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['warnings']


def test_feature_flag_help_and_analysis_namespace_document_linter_v3():
    assert feature_status('devx.linter_v3').stability == Stability.STABLE
    text = pea_help('lint-v3')
    assert 'pea lint-v3' in text
    assert 'LintProfileV3 ->' in text
    namespace = build_linter_v3_namespace()
    assert namespace['LINTER_V3_VERSION'] == '3.1.47'
    assert namespace['build_linter_v3_namespace'] is build_linter_v3_namespace
    analysis = build_analysis_namespace()
    for name in ('LintProfileV3', 'LintDiagnosticV3', 'LintResultV3',
                 'LintSourceV3', 'LintFileV3', 'LinterCapabilitiesV3',
                 'LinterReportV3', 'LinterGateV3', 'LinterNamespaceV3'):
        assert name in analysis


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.15.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.15.0'
    assert manifest['previous_version'] == '5.14.0'
    assert pealang.LINTER_V3_VERSION == '3.1.47'
    assert pealang.FORMATTER_V3_VERSION == '3.1.46'
    assert pealang.DAP_V2_VERSION == '3.1.45'
    assert pealang.LSP_V2_VERSION == '3.1.44'
    assert pealang.PARALLEL_RUNTIME_VERSION == '3.1.43'
    assert pealang.RUNTIME_PROFILER_VERSION == '3.1.43'
    assert pealang.WASM_BACKEND_VERSION == '3.1.42'
    assert pealang.NATIVE_BACKEND_VERSION == '3.1.41'
    assert pealang.BYTECODE_JIT_VERSION == '3.1.40'
    assert pealang.FAST_INTERPRETER_VERSION == '3.1.39'
    assert pealang.OPTIMIZER_VERSION == '3.1.38'
    assert pealang.CORE_RELEASE_FROZEN_AT == '3.1.37'


def test_frozen_core_gate_still_passes():
    report = core_freeze_report()
    assert report['release'] == '3.1.37'
    assert report['freeze']['gate'] == 'PASS'
    assert report['freeze']['digest'] == (
        '2e9f93e8506331d00131a33c3b99d799c3893d5f3ea1680acd3d2458327d461d')
