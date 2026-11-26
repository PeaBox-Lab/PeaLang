"""Phase 77: deterministic runtime profiler with VM parity."""

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

LOOP = 'let i = 0\nwhile i < 3 { print i\n i = i + 1 }'


def module():
    return compile_source_to_bytecode(LOOP)


def test_profile_module_is_deterministic_and_counts_hotspots():
    program = module()
    first = pealang.profile_module(program, top=3)
    second = pealang.profile_module(program, top=3)
    assert first == second
    assert first['version'] == pealang.RUNTIME_PROFILER_VERSION == '3.1.43'
    assert first['format'] == pealang.RUNTIME_PROFILER_FORMAT == 'pea-runtime-profile-v1'
    assert first['instructions'] > 0
    assert len(first['profile_digest']) == 64
    assert first['opcodes'] == sorted(first['opcodes'])
    assert first['functions'] == sorted(first['functions'])
    assert first['lines'] == sorted(first['lines'])
    assert len(first['top_opcodes']) == 3
    assert first['top_opcodes'][0][1] >= first['top_opcodes'][-1][1]
    assert first['output'] == ['0', '1', '2']


def test_runtime_profiler_run_carries_profile_counters():
    program = module()
    profiler = pealang.RuntimeProfiler()
    run = profiler.run(program)
    assert isinstance(run, pealang.ProfileRun)
    assert profiler.last_run == run
    assert run.instructions > 0
    assert dict(run.opcodes)['PRINT'] == 3
    assert run.output == (0, 1, 2)
    assert len(run.digest) == 64
    assert run.to_dict()['digest'] == run.digest
    with pytest.raises(pealang.RuntimeProfilerError):
        profiler.run('not bytecode')


def test_verify_profile_parity_matches_vm():
    parity = pealang.verify_profile_parity(module())
    assert parity['ok']
    assert parity['output_match'] and parity['result_match']
    assert parity['vm']['output'] == parity['profiler']['output'] == ['0', '1', '2']
    assert parity['profiler']['digest']


def test_report_benchmark_and_gate_are_enforced():
    program = module()
    first = pealang.profiler_report(program, verify=True, benchmark=True, top=2)
    second = pealang.profiler_report(program, verify=True, benchmark=True, top=2)
    report_without_timing = {k: v for k, v in first.items() if k != 'benchmark'}
    report_without_timing_2 = {k: v for k, v in second.items() if k != 'benchmark'}
    assert report_without_timing == report_without_timing_2
    assert first['parity']['ok']
    assert first['benchmark']['iterations'] == 25
    assert first['benchmark']['vm_median_ms'] >= 0
    assert first['benchmark']['profiler_median_ms'] >= 0
    assert pealang.profiler_gate(first) == {'gate': 'PASS', 'issues': []}
    assert pealang.profiler_gate({'gate': 'FAIL'})['gate'] == 'FAIL'
    assert 'instructions' in pealang.profiler_gate(
        {'gate': 'PASS', 'instructions': 0})['issues']
    assert 'parity' in pealang.profiler_gate(
        {'gate': 'PASS', 'instructions': 1, 'parity': {'ok': False}})['issues']


def test_cli_profiler_command_writes_report_and_passes_parity(tmp_path):
    source = tmp_path / 'app.pea'
    report_path = tmp_path / 'profile.json'
    source.write_text(LOOP + '\n', encoding='utf-8')
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'profiler', str(source),
         '--verify', '--top', '2', '--emit', str(report_path)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['version'] == '3.1.43'
    assert report['parity']['ok']
    assert json.loads(report_path.read_text(encoding='utf-8')) == report


def test_feature_flag_help_and_analysis_namespace_document_profiler():
    assert feature_status('runtime.profiler_v3').stability == Stability.STABLE
    text = pea_help('profiler')
    assert 'pea profiler' in text
    assert 'profile_module(module)' in text
    namespace = build_analysis_namespace()
    for name in ('RuntimeProfiler', 'ProfileModule', 'VerifyProfileParity',
                 'BenchmarkProfiler', 'ProfilerReport', 'RuntimeProfilerNamespace'):
        assert name in namespace


def test_release_metadata_is_aligned():
    assert pealang.__version__ == SPEC_VERSION == '5.11.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.11.0'
    assert manifest['previous_version'] == '5.10.0'
    assert pealang.RUNTIME_PROFILER_VERSION == '3.1.43'
    assert pealang.PERFORMANCE_GATE_VERSION == '4.0.0'
    assert pealang.PARALLEL_RUNTIME_VERSION == '3.1.43'
    assert pealang.WASM_BACKEND_VERSION == '3.1.42'
    assert pealang.CORE_RELEASE_FROZEN_AT == '3.1.37'


def test_frozen_core_gate_still_passes():
    report = core_freeze_report()
    assert report['release'] == '3.1.37'
    assert report['freeze']['gate'] == 'PASS'
    assert report['freeze']['digest'] == (
        '2e9f93e8506331d00131a33c3b99d799c3893d5f3ea1680acd3d2458327d461d')
