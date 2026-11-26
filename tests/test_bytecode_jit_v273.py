"""Phase 73: profile-guided bytecode JIT with guarded deoptimization."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
from pealang.analysis import build_analysis_namespace
from pealang.compatibility import Stability, feature_status
from pealang.compiler import compile_source_to_bytecode
from pealang.core_freeze import core_freeze_report
from pealang.help import help as pea_help
from pealang.specification import SPEC_VERSION


INT_LOOP = 'let i = 0\nwhile i < 3 { print i\n i = i + 1 }'
FLOAT_LOOP = 'let i = 0.0\nwhile i < 3 { print i\n i = i + 1.0 }'
FUNCTION = 'function f(a) { return a + 1 }\nprint f(3)'


def _backedge(module):
    for index, instruction in enumerate(module.code.instructions):
        if (instruction.op == 'JUMP' and isinstance(instruction.arg, int)
                and instruction.arg < index):
            return index, instruction.arg
    raise AssertionError('no loop back-edge in module')


def _run_jit(source, **kwargs):
    module = compile_source_to_bytecode(source)
    output = []
    runtime = pealang.JITRuntime(output.append, **kwargs)
    result = runtime.run(module)
    return module, output, result, runtime


def test_profile_execution_counts_instructions_and_selects_hot_backedge():
    module = compile_source_to_bytecode(INT_LOOP)
    profile = pealang.profile_execution(module)
    assert profile.supported
    assert profile.total > 0
    backedge, entry = _backedge(module)
    assert profile.count(backedge) >= 2
    traces = pealang.select_traces(module, profile)
    assert traces
    assert traces[0].entry == entry
    assert traces[0].backedge == backedge
    assert traces[0].hits >= 2


def test_compile_trace_specializes_integer_arithmetic():
    module = compile_source_to_bytecode(INT_LOOP)
    profile = pealang.profile_execution(module)
    trace = pealang.select_traces(module, profile)[0]
    compiled = pealang.compile_trace(module, trace)
    assert compiled is not None
    assert compiled.length == trace.length
    assert compiled.guarded_ops >= 1


def test_jit_runtime_matches_vm_for_int_loop():
    _, output, result, runtime = _run_jit(INT_LOOP)
    assert output == [0, 1, 2]
    assert result is None
    assert runtime.stats['mode'] == 'jit'
    assert runtime.stats['traces_compiled'] >= 1
    assert runtime.stats['trace_steps'] > 0
    assert runtime.stats['deopts'] == 0


def test_guard_failure_deoptimizes_without_changing_float_output():
    _, output, _, runtime = _run_jit(FLOAT_LOOP)
    assert output == [0.0, 1.0, 2.0]
    assert runtime.stats['deopts'] > 0
    assert runtime.stats['traces_compiled'] >= 1


def test_unsupported_modules_fall_back_to_vm_without_changing_output():
    _, output, result, runtime = _run_jit(FUNCTION)
    assert output == [4]
    assert result is None
    assert runtime.stats['mode'] == 'vm'


def test_verify_jit_parity_passes_on_int_float_and_fallback_paths():
    for source in (INT_LOOP, FLOAT_LOOP, FUNCTION):
        parity = pealang.verify_jit_parity(compile_source_to_bytecode(source))
        assert parity['ok'], (source, parity)
        assert parity['output_match'] and parity['result_match']


def test_bytecode_jit_report_is_stable_and_gated():
    module = compile_source_to_bytecode(INT_LOOP)
    first = pealang.bytecode_jit_report(module, verify=True)
    second = pealang.bytecode_jit_report(module, verify=True)
    assert first == second
    assert first['version'] == pealang.BYTECODE_JIT_VERSION == '3.1.40'
    assert first['mode'] == 'jit'
    assert first['profile']['supported']
    assert first['compiled_traces'][0]['guarded_ops'] >= 1
    assert first['parity']['ok']
    assert pealang.bytecode_jit_gate(first) == {'gate': 'PASS', 'issues': []}


def test_benchmark_reports_medians_without_asserting_timing():
    module = compile_source_to_bytecode(INT_LOOP)
    report = pealang.bytecode_jit_report(module, benchmark=True)
    benchmark = report['benchmark']
    assert benchmark['iterations'] == 25
    assert benchmark['vm_median_ms'] >= 0
    assert benchmark['jit_median_ms'] >= 0


def test_gate_rejects_invalid_mode_compilation_and_failed_parity():
    assert pealang.bytecode_jit_gate({'mode': 'unknown'})['gate'] == 'FAIL'
    broken = pealang.bytecode_jit_gate({'mode': 'jit', 'gate': 'FAIL'})
    assert 'compilation' in broken['issues']
    failed = pealang.bytecode_jit_gate(
        {'mode': 'jit', 'gate': 'PASS', 'parity': {'ok': False}})
    assert failed['gate'] == 'FAIL'
    assert 'parity' in failed['issues']


def test_cli_jit_command_passes_with_parity(tmp_path):
    source = tmp_path / 'app.pea'
    source.write_text(INT_LOOP + '\n', encoding='utf-8')
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'jit', str(source), '--verify'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['mode'] == 'jit'
    assert report['parity']['ok']
    assert report['version'] == '3.1.40'
    assert report['stats']['traces_compiled'] >= 1


def test_cli_jit_fallback_and_optimize_flag(tmp_path):
    source = tmp_path / 'app.pea'
    source.write_text(FUNCTION + '\n', encoding='utf-8')
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'jit', str(source),
         '--verify', '--optimize'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['mode'] == 'vm'
    assert report['parity']['ok']


def test_feature_flag_help_and_analysis_namespace_document_jit():
    assert feature_status('runtime.bytecode_jit_v3').stability == Stability.STABLE
    text = pea_help('jit')
    assert 'pea jit' in text
    assert 'verify_jit_parity()' in text
    namespace = build_analysis_namespace()
    for name in ('JITRuntime', 'VerifyJITParity', 'BenchmarkJIT',
                 'JITReport', 'JITNamespace'):
        assert name in namespace


def test_release_metadata_is_aligned():
    assert pealang.__version__ == SPEC_VERSION == '5.7.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.7.0'
    assert manifest['previous_version'] == '5.6.0'
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
