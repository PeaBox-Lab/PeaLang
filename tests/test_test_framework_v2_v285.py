"""Phase 85: deterministic test framework v2 with stable IDs and gates."""

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
from pealang.specification import SPEC_VERSION
from pealang.test_framework_v2 import (DEFAULT_TEST_PROFILE,
                                      TEST_FRAMEWORK_V2_FORMAT,
                                      TEST_FRAMEWORK_V2_VERSION,
                                      TestFrameworkV2Error as FrameworkV2Error,
                                      TestProfileV2 as ProfileV2,
                                      build_test_framework_v2_namespace,
                                      run_test_source_v2,
                                      test_framework_v2_capabilities as framework_v2_capabilities,
                                      test_v2_gate as gate_v2,
                                      test_v2_report as report_v2)

SOURCE = '''describe "math" {
  test "fails" { expect 1 == 2 }
  test "adds" { expect 1 + 1 == 2 }
}
test "truthy" { expect true }
'''
PASS_SOURCE = '''test "ok" { expect true }
test "also ok" { expect 1 + 1 == 2 }
'''


def test_constants_capabilities_and_profile_validation():
    caps = framework_v2_capabilities()
    assert TEST_FRAMEWORK_V2_VERSION == pealang.TEST_FRAMEWORK_V2_VERSION == '3.1.48'
    assert TEST_FRAMEWORK_V2_FORMAT == pealang.TEST_FRAMEWORK_V2_FORMAT == 'pea-test-v2'
    assert caps == framework_v2_capabilities()
    assert caps['version'] == '3.1.48'
    assert caps['executor'] == 'native_vm'
    assert caps['stable_ids'] is True
    assert caps['deterministic_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert caps['options'] == ['filter_text', 'fail_fast', 'max_failures']
    assert DEFAULT_TEST_PROFILE.digest() == ProfileV2().digest()
    with pytest.raises(FrameworkV2Error):
        ProfileV2(filter_text=1)
    with pytest.raises(FrameworkV2Error):
        ProfileV2(max_failures=-1)


def test_discovery_has_stable_ids_order_filtering_and_fail_fast():
    result = run_test_source_v2(SOURCE)
    assert [item.case_id for item in result.cases] == [
        'math::fails@2', 'math::adds@3', 'math::truthy@5',
    ]
    assert [item.passed for item in result.cases] == [False, True, True]
    assert result.passed_count == 2
    assert result.failed_count == 1
    assert result.gate == 'FAIL'
    assert all(len(item.fingerprint()) == 64 for item in result.cases)
    filtered = run_test_source_v2(SOURCE, ProfileV2(filter_text='adds'))
    assert [item.case_id for item in filtered.cases] == ['math::adds@3']
    assert filtered.gate == 'PASS'
    fast = run_test_source_v2(SOURCE, ProfileV2(fail_fast=True))
    assert [item.case_id for item in fast.cases] == ['math::fails@2']
    assert fast.failed_count == 1


def test_digest_ignores_source_names_line_endings_and_timings():
    first = run_test_source_v2(PASS_SOURCE, source_name='C:\\work\\ok.pea')
    second = run_test_source_v2(PASS_SOURCE.replace('\n', '\r\n'),
                                source_name='/other/ok.pea')
    assert first.source_name != second.source_name
    assert first.digest == second.digest
    assert first.gate == 'PASS'
    payload = first.to_dict()
    assert payload['case_count'] == 2
    assert 'elapsed_ms' not in payload
    assert all('elapsed_ms' not in case for case in payload['cases'])
    assert all('<source>' in (case['error'] or '') or case['error'] is None
               for case in payload['cases'])


def test_discovery_failure_is_a_stable_error_case():
    result = run_test_source_v2('describe "broken" { test "oops" {')
    assert len(result.cases) == 1
    case = result.cases[0]
    assert case.case_id == '<discovery>::discovery@1'
    assert case.passed is False
    assert case.error == 'SyntaxError: test discovery failed'
    assert result.gate == 'FAIL'
    assert gate_v2(report_v2([result]))['issues'] == ['failures']


def test_report_and_gate_are_recomputed_and_tamper_detecting():
    result = run_test_source_v2(SOURCE, source_name='C:\\work\\suite.pea')
    report = report_v2([result])
    assert report['version'] == '3.1.48'
    assert report['format'] == 'pea-test-v2'
    assert report['result_count'] == 1
    assert report['case_count'] == 3
    assert report['passed_count'] == 2
    assert report['failed_count'] == 1
    assert report['gate'] == 'FAIL'
    assert len(report['digest']) == 64
    assert gate_v2(report) == {'gate': 'FAIL', 'issues': ['failures']}
    tolerant = report_v2([result], ProfileV2(max_failures=1))
    assert gate_v2(tolerant) == {'gate': 'PASS', 'issues': []}
    assert 'version' in gate_v2({**report, 'version': 'old'})['issues']
    assert 'format' in gate_v2({**report, 'format': 'old'})['issues']
    assert 'digest' in gate_v2({**report, 'digest': 'short'})['issues']
    assert 'digest' in gate_v2({**report, 'digest': '0' * 64})['issues']
    assert 'counts' in gate_v2({**report, 'case_count': 99})['issues']
    tampered = json.loads(json.dumps(report))
    tampered['results'][0]['cases'][0]['fingerprint'] = '0' * 64
    assert 'case_fingerprint' in gate_v2(tampered)['issues']


def test_cli_capabilities_check_emit_filter_and_failure_gate(tmp_path):
    root = Path(__file__).resolve().parent.parent
    caps_result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'test-v2', '--capabilities'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert caps_result.returncode == 0, caps_result.stderr
    assert json.loads(caps_result.stdout)['version'] == '3.1.48'
    passing = tmp_path / 'ok.pea'
    passing.write_text(PASS_SOURCE, encoding='utf-8')
    emit_path = tmp_path / 'tests.json'
    checked = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'test-v2', str(passing),
         '--check', '--emit', str(emit_path)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    assert report['version'] == '3.1.48'
    assert report['case_count'] == 2
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    failing = tmp_path / 'suite.pea'
    failing.write_text(SOURCE, encoding='utf-8')
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'test-v2', str(failing),
         '--check', '--fail-fast'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert strict.returncode == 1, strict.stderr
    strict_report = json.loads(strict.stdout)
    assert strict_report['case_count'] == 1
    assert strict_report['decision']['issues'] == ['failures']
    filtered = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'test-v2', str(failing),
         '--check', '--filter', 'adds'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert filtered.returncode == 0, filtered.stderr
    assert json.loads(filtered.stdout)['decision']['gate'] == 'PASS'


def test_feature_flag_help_and_analysis_namespace_document_test_framework_v2():
    assert feature_status('devx.test_framework_v2').stability == Stability.STABLE
    text = pea_help('test-v2')
    assert 'pea test-v2' in text
    assert 'TestProfileV2 ->' in text
    namespace = build_test_framework_v2_namespace()
    assert namespace['TEST_FRAMEWORK_V2_VERSION'] == '3.1.48'
    assert namespace['build_test_framework_v2_namespace'] is build_test_framework_v2_namespace
    analysis = build_analysis_namespace()
    for name in ('TestProfileV2', 'TestCaseV2', 'TestResultV2',
                 'TestSourceV2', 'TestFileV2', 'TestFrameworkCapabilitiesV2',
                 'TestFrameworkReportV2', 'TestFrameworkGateV2',
                 'TestFrameworkNamespaceV2'):
        assert name in analysis


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.5.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.5.0'
    assert manifest['previous_version'] == '5.4.0'
    assert pealang.TEST_FRAMEWORK_V2_VERSION == '3.1.48'
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
