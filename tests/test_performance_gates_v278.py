"""Phase 78: versioned 4.0 performance gates with release evidence."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
import pytest
from pealang.analysis import build_analysis_namespace
from pealang.compatibility import Stability, feature_status
from pealang.compiler import compile_source_to_bytecode
from pealang.core_freeze import core_freeze_report
from pealang.help import help as pea_help
from pealang.specification import SPEC_VERSION


def module():
    return compile_source_to_bytecode('let i = 0\nwhile i < 5 { i = i + 1 }\nprint i')


def test_gate_constants_and_budget_are_pinned():
    assert pealang.PERFORMANCE_GATE_VERSION == '4.0.0'
    assert pealang.PERFORMANCE_GATE_FORMAT == 'pea-performance-gates-v4'
    budget = pealang.GateBudget()
    assert budget.max_mean_ms > 0 and budget.max_p95_ms > 0
    assert budget.require_parity and budget.require_conformance and budget.require_freeze


def test_collect_evidence_is_structured_and_digest_is_stable():
    program = module()
    first = pealang.collect_gate_evidence(program, iterations=2)
    second = pealang.collect_gate_evidence(program, iterations=2)
    assert isinstance(first, pealang.GateEvidence)
    assert first.iterations == 2
    assert first.digest == second.digest
    assert first.parallel_parity_ok and first.profiler_parity_ok
    assert first.conformance_ok and first.freeze_ok
    assert first.mean_ms >= 0 and first.p95_ms >= 0 and first.peak_memory_mb >= 0
    assert first.to_dict()['digest'] == first.digest


def test_gate_report_passes_defaults_and_fails_strict_budget():
    program = module()
    passing = pealang.performance_gate_report(program, iterations=2)
    assert passing['gate'] == 'PASS'
    assert passing['issues'] == []
    assert all(passing['checks'].values())
    assert passing['version'] == '4.0.0'
    assert passing['format'] == pealang.PERFORMANCE_GATE_FORMAT
    assert passing['evidence_digest'] == passing['evidence']['digest']
    assert pealang.performance_gate(passing)['gate'] == 'PASS'
    strict = pealang.performance_gate_report(
        program, budget=pealang.GateBudget(max_mean_ms=-1), iterations=2)
    assert strict['gate'] == 'FAIL'
    assert 'mean_ms' in strict['issues']
    recomputed = pealang.performance_gate(strict)
    assert recomputed['gate'] == 'FAIL'
    assert recomputed['checks']['mean_ms'] is False


def test_malformed_report_is_rejected():
    with pytest.raises(pealang.PerformanceGateError):
        pealang.performance_gate({'budget': {'unknown': 1}, 'evidence': {}})


def test_cli_perf_gate_command_writes_report_and_passes(tmp_path):
    source = tmp_path / 'app.pea'
    report_path = tmp_path / 'gate.json'
    source.write_text('print 42\n', encoding='utf-8')
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'perf-gate', str(source),
         '--iterations', '2', '--workers', '2', '--emit', str(report_path)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['gate'] == 'PASS'
    assert report['version'] == '4.0.0'
    assert report['evidence']['iterations'] == 2
    assert json.loads(report_path.read_text(encoding='utf-8')) == report


def test_feature_flag_help_and_analysis_namespace_document_gates():
    assert feature_status('runtime.performance_gates_v4').stability == Stability.STABLE
    text = pea_help('perf-gate')
    assert 'pea perf-gate' in text
    assert 'performance_gate_report(module)' in text
    namespace = build_analysis_namespace()
    for name in ('GateBudgetV4', 'CollectGateEvidence', 'PerformanceGateReportV4',
                 'PerformanceGateV4', 'PerformanceGatesNamespaceV4'):
        assert name in namespace


def test_release_metadata_is_aligned():
    assert pealang.__version__ == SPEC_VERSION == '5.18.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.18.0'
    assert manifest['previous_version'] == '5.17.0'
    assert pealang.PERFORMANCE_GATE_VERSION == '4.0.0'
    assert pealang.RUNTIME_PROFILER_VERSION == '3.1.43'
    assert pealang.PARALLEL_RUNTIME_VERSION == '3.1.43'
    assert pealang.WASM_BACKEND_VERSION == '3.1.42'
    assert pealang.CORE_RELEASE_FROZEN_AT == '3.1.37'


def test_frozen_core_gate_still_passes():
    report = core_freeze_report()
    assert report['release'] == '3.1.37'
    assert report['freeze']['gate'] == 'PASS'
    assert report['freeze']['digest'] == (
        '2e9f93e8506331d00131a33c3b99d799c3893d5f3ea1680acd3d2458327d461d')
