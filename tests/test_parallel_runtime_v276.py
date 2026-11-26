"""Phase 76: bounded parallel runtime with ordered output and VM parity."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
import pytest
from pealang.analysis import build_analysis_namespace
from pealang.bytecode import Instruction
from pealang.compatibility import Stability, feature_status
from pealang.compiler import compile_source_to_bytecode
from pealang.core_freeze import core_freeze_report
from pealang.help import help as pea_help
from pealang.specification import SPEC_VERSION

SOURCE = 'print task_id'


def make_tasks(module=None, count=3):
    module = module or compile_source_to_bytecode(SOURCE)
    return tuple(pealang.ParallelTask(
        f'task-{index}', module, {'task_id': index})
        for index in range(count))


def test_parallel_support_and_plan_are_deterministic():
    tasks = make_tasks()
    assert pealang.parallel_supported(tasks)
    first = pealang.build_parallel_plan(tasks)
    second = pealang.build_parallel_plan(tasks)
    assert first == second
    assert first.format == pealang.PARALLEL_RUNTIME_FORMAT == 'pea-parallel-runtime-v1'
    assert first.version == pealang.PARALLEL_RUNTIME_VERSION == '3.1.43'
    assert first.supported
    assert len(first.tasks) == 3
    assert first.digest == second.digest
    assert json.loads(first.dumps()) == json.loads(second.dumps())


def test_unsupported_async_module_falls_back_to_sequential_vm():
    module = compile_source_to_bytecode(SOURCE)
    module.code.instructions.append(Instruction('AWAIT'))
    tasks = make_tasks(module)
    assert not pealang.parallel_supported(tasks)
    runtime = pealang.ParallelRuntime(workers=4)
    result = runtime.run(tasks)
    assert result.mode == 'sequential'
    assert result.workers == 1
    assert not result.supported
    assert result.outputs == ((0,), (1,), (2,))
    assert result.results == (None, None, None)
    assert runtime.last_plan.digest == result.plan_digest


def test_runtime_preserves_task_order_with_bounded_workers():
    tasks = make_tasks(count=4)
    runtime = pealang.ParallelRuntime(workers=2)
    result = runtime.run(tasks)
    assert result.mode == 'parallel'
    assert result.workers == 2
    assert result.task_count == 4
    assert result.outputs == ((0,), (1,), (2,), (3,))
    assert result.results == (None, None, None, None)
    assert all(count > 0 for count in result.instructions)
    assert result.plan_digest == pealang.build_parallel_plan(tasks).digest


def test_runtime_rejects_empty_and_invalid_tasks():
    with pytest.raises(pealang.ParallelError):
        pealang.ParallelRuntime().run(())
    with pytest.raises(pealang.ParallelError):
        pealang.build_parallel_plan(('not-a-task',))
    assert not pealang.parallel_supported(())


def test_verify_parallel_parity_covers_supported_and_fallback_paths():
    supported = make_tasks()
    parity = pealang.verify_parallel_parity(supported, workers=3)
    assert parity['ok'] and parity['output_match'] and parity['result_match']
    assert parity['parallel']['mode'] == 'parallel'
    module = compile_source_to_bytecode(SOURCE)
    module.code.instructions.append(Instruction('AWAIT'))
    fallback_parity = pealang.verify_parallel_parity(
        make_tasks(module), workers=3)
    assert fallback_parity['ok']
    assert fallback_parity['parallel']['mode'] == 'sequential'


def test_report_is_stable_and_gate_is_enforced():
    tasks = make_tasks()
    first = pealang.parallel_report(tasks, verify=True, workers=2)
    second = pealang.parallel_report(tasks, verify=True, workers=2)
    assert first == second
    assert first['version'] == pealang.PARALLEL_RUNTIME_VERSION == '3.1.43'
    assert first['format'] == pealang.PARALLEL_RUNTIME_FORMAT
    assert first['mode'] == 'parallel'
    assert first['workers'] == 2
    assert first['task_count'] == 3
    assert first['outputs'] == [['0'], ['1'], ['2']]
    assert first['parity']['ok']
    benchmarked = pealang.parallel_report(tasks, benchmark=True, workers=2)
    assert benchmarked['benchmark']['iterations'] == 25
    assert benchmarked['benchmark']['workers'] == 2
    assert benchmarked['benchmark']['sequential_median_ms'] >= 0
    assert benchmarked['benchmark']['parallel_median_ms'] >= 0
    assert pealang.parallel_gate(first) == {'gate': 'PASS', 'issues': []}
    assert pealang.parallel_gate({'mode': 'unknown'})['gate'] == 'FAIL'
    assert 'parity' in pealang.parallel_gate(
        {'mode': 'parallel', 'gate': 'PASS', 'parity': {'ok': False}})['issues']
    assert 'tasks' in pealang.parallel_gate(
        {'mode': 'parallel', 'gate': 'PASS', 'task_count': 0})['issues']


def test_cli_parallel_command_reports_ordered_parallel_parity(tmp_path):
    source = tmp_path / 'app.pea'
    source.write_text(SOURCE + '\n', encoding='utf-8')
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'parallel', str(source),
         '--verify', '--tasks', '4', '--workers', '2'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['mode'] == 'parallel'
    assert report['workers'] == 2
    assert report['task_count'] == 4
    assert report['outputs'] == [['0'], ['1'], ['2'], ['3']]
    assert report['parity']['ok']
    assert report['version'] == '3.1.43'


def test_feature_flag_help_and_analysis_namespace_document_parallel_runtime():
    assert feature_status('runtime.parallel_runtime_v3').stability == Stability.STABLE
    text = pea_help('parallel')
    assert 'pea parallel' in text
    assert 'build_parallel_plan(tasks)' in text
    namespace = build_analysis_namespace()
    for name in ('ParallelRuntime', 'BuildParallelPlan', 'VerifyParallelParity',
                 'BenchmarkParallel', 'ParallelReport', 'ParallelNamespace'):
        assert name in namespace


def test_release_metadata_is_aligned():
    assert pealang.__version__ == SPEC_VERSION == '5.16.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.16.0'
    assert manifest['previous_version'] == '5.15.0'
    assert pealang.PARALLEL_RUNTIME_VERSION == '3.1.43'
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
