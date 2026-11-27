"""Phase 83: deterministic formatter v3 with reviewable parity evidence."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
import pytest
from pealang.analysis import build_analysis_namespace
from pealang.compatibility import Stability, feature_status
from pealang.core_freeze import core_freeze_report
from pealang.formatter import format_source_ast
from pealang.formatter_v3 import (BRACE_STYLES, DEFAULT_FORMAT_PROFILE,
                                  FORMATTER_V3_FORMAT, FORMATTER_V3_VERSION,
                                  FormatProfile, FormatterV3Error,
                                  build_formatter_v3_namespace,
                                  format_source_v3, formatter_v3_capabilities,
                                  formatter_v3_gate, formatter_v3_report,
                                  verify_format_parity)
from pealang.help import help as pea_help
from pealang.specification import SPEC_VERSION

SOURCE = '''let s = "tag # not comment" // real comment
let n=1+2*3
function f(a,b)->number{
return a+b
}
if n>=7 {print(s)}
'''
EXPECTED = '''let s = "tag # not comment" // real comment
let n = 1 + 2 * 3
function f(a, b) -> number {
    return a + b
}
if n >= 7 { print(s) }
'''


def test_formatter_v3_constants_capabilities_and_profile_validation():
    caps = formatter_v3_capabilities()
    assert FORMATTER_V3_VERSION == pealang.FORMATTER_V3_VERSION == '3.1.46'
    assert FORMATTER_V3_FORMAT == pealang.FORMATTER_V3_FORMAT == 'pea-fmt-v3'
    assert BRACE_STYLES == pealang.BRACE_STYLES == ('same_line', 'next_line')
    assert caps == formatter_v3_capabilities()
    assert caps['version'] == '3.1.46'
    assert caps['preserves_comments'] is True
    assert caps['idempotent'] is True
    assert caps['parity_check'] == 'bytecode'
    assert DEFAULT_FORMAT_PROFILE.digest() == FormatProfile().digest()
    with pytest.raises(FormatterV3Error):
        FormatProfile(indent_size=0)
    with pytest.raises(FormatterV3Error):
        FormatProfile(max_line_length=39)
    with pytest.raises(FormatterV3Error):
        FormatProfile(brace_style='unknown')


def test_formatting_preserves_comments_strings_and_semantics():
    result = format_source_v3(SOURCE)
    assert result.formatted == EXPECTED
    assert result.changed is True
    assert result.idempotent is True
    assert result.parity['passed'] is True
    assert result.parity['fingerprints']['original'] == result.parity['fingerprints']['formatted']
    assert '"tag # not comment"' in result.formatted
    assert '// real comment' in result.formatted
    assert format_source_ast('let x=1\n')
    again = format_source_v3(EXPECTED)
    assert again.changed is False
    assert again.formatted == EXPECTED
    assert again.digest == result.digest


def test_format_profiles_control_indent_and_brace_style():
    source = 'function f(){\nreturn 1\n}\n'
    compact = format_source_v3(source, FormatProfile(indent_size=2))
    assert compact.formatted == 'function f() {\n  return 1\n}\n'
    assert compact.parity['passed'] is True
    split = format_source_v3(
        source, FormatProfile(indent_size=2, brace_style='next_line'))
    assert split.formatted == 'function f()\n{\n  return 1\n}\n'
    assert split.idempotent is True
    assert split.parity['passed'] is True
    assert split.digest != compact.digest


def test_invalid_source_reports_parity_issues_and_fails_gate():
    result = format_source_v3('function f( {')
    assert result.parity['passed'] is False
    assert 'original' in result.parity['issues']
    report = formatter_v3_report([result])
    assert formatter_v3_gate(report)['gate'] == 'FAIL'
    assert 'parity' in formatter_v3_gate(report)['issues']
    mismatch = verify_format_parity('let x = 1\n', 'let x = 2\n')
    assert mismatch['passed'] is False
    assert mismatch['issues'] == ['semantics']


def test_report_and_gate_are_deterministic_and_ignore_host_paths():
    first = format_source_v3(EXPECTED, source_name='C:\\work\\app.pea')
    second = format_source_v3(EXPECTED, source_name='/other/app.pea')
    assert first.source_name != second.source_name
    assert first.digest == second.digest
    report = formatter_v3_report([first])
    assert report == formatter_v3_report([first])
    assert report['version'] == '3.1.46'
    assert report['format'] == 'pea-fmt-v3'
    assert report['result_count'] == 1
    assert report['changed_count'] == 0
    assert len(report['digest']) == 64
    assert formatter_v3_gate(report) == {'gate': 'PASS', 'issues': []}
    assert 'version' in formatter_v3_gate({**report, 'version': 'old'})['issues']
    assert 'format' in formatter_v3_gate({**report, 'format': 'old'})['issues']
    assert 'digest' in formatter_v3_gate({**report, 'digest': 'short'})['issues']


def test_cli_capabilities_check_write_and_emit(tmp_path):
    root = Path(__file__).resolve().parent.parent
    caps_result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'fmt-v3', '--capabilities'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert caps_result.returncode == 0, caps_result.stderr
    assert json.loads(caps_result.stdout)['version'] == '3.1.46'
    source = tmp_path / 'app.pea'
    report_path = tmp_path / 'fmt.json'
    source.write_text(SOURCE, encoding='utf-8')
    checked = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'fmt-v3', str(source),
         '--check', '--emit', str(report_path)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert checked.returncode == 1, checked.stderr
    report = json.loads(checked.stdout)
    assert report['version'] == '3.1.46'
    assert report['changed_count'] == 1
    assert report['results'][0]['changed'] is True
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(report_path.read_text(encoding='utf-8')) == report
    written = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'fmt-v3', str(source), '--write'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert written.returncode == 0, written.stderr
    assert source.read_text(encoding='utf-8') == EXPECTED
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'fmt-v3', str(source), '--check'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['changed_count'] == 0


def test_feature_flag_help_and_analysis_namespace_document_formatter_v3():
    assert feature_status('devx.formatter_v3').stability == Stability.STABLE
    text = pea_help('fmt-v3')
    assert 'pea fmt-v3' in text
    assert 'FormatProfile ->' in text
    namespace = build_formatter_v3_namespace()
    assert namespace['FORMATTER_V3_VERSION'] == '3.1.46'
    assert namespace['build_formatter_v3_namespace'] is build_formatter_v3_namespace
    analysis = build_analysis_namespace()
    for name in ('FormatProfileV3', 'FormatResultV3', 'FormatSourceV3',
                 'FormatFileV3', 'VerifyFormatParityV3',
                 'FormatterCapabilitiesV3', 'FormatterReportV3',
                 'FormatterGateV3', 'FormatterNamespaceV3'):
        assert name in analysis


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.25.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.25.0'
    assert manifest['previous_version'] == '5.24.0'
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
