"""Phase 72: direct-handler fast interpreter with parity-verified fallback."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
from pealang.compatibility import Stability, feature_status
from pealang.compiler import compile_source_to_bytecode
from pealang.help import help as pea_help
from pealang.specification import SPEC_VERSION


def _run_fast(source, **kwargs):
    module = compile_source_to_bytecode(source)
    output = []
    result = pealang.FastInterpreter(output.append, **kwargs).run(module)
    return module, output, result


def test_fast_path_detects_supported_and_unsupported_modules():
    supported, _, _ = _run_fast('print 1 + 2')
    unsupported, _, _ = _run_fast(
        'function f(a) { return a + 1 }\nprint f(2)')
    assert pealang.fast_path_supported(supported)
    assert not pealang.fast_path_supported(unsupported)
    assert pealang.compile_fast_program(supported) is not None
    assert pealang.compile_fast_program(unsupported) is None


def test_fast_interpreter_matches_vm_for_arithmetic_and_variables():
    _, output, result = _run_fast(
        'let x = 5\nprint x + 1\nx = x * 2\nprint x')
    assert output == [6, 10]
    assert result is None


def test_fast_interpreter_matches_vm_for_loops_and_branches():
    _, output, _ = _run_fast(
        'let i = 0\nwhile i < 3 { print i\n i = i + 1 }')
    assert output == [0, 1, 2]
    _, output, _ = _run_fast(
        'if 1 > 2 { print 10 } else { print 20 }')
    assert output == [20]


def test_fast_interpreter_supports_unary_operations_and_false():
    _, output, _ = _run_fast('print -7\nprint not false\nprint true')
    assert output == [-7, True, True]


def test_unsupported_modules_fall_back_to_vm_without_changing_output():
    source = 'function f(a) { return a + 1 }\nprint f(2)'
    module, _, _ = _run_fast(source)
    output = []
    interpreter = pealang.FastInterpreter(output.append)
    result = interpreter.run(module)
    assert interpreter.last_report['mode'] == 'vm'
    assert output == [3]
    assert result is None


def test_fast_program_executes_prebound_handlers_directly():
    module = compile_source_to_bytecode('print 2 * 4')
    program = pealang.compile_fast_program(module)
    assert program is not None
    output = []
    program_handlers = list(program.handlers)
    pealang.FastInterpreter(output.append).run(module)
    assert len(program_handlers) == len(module.code.instructions)
    assert output == [8]


def test_verify_fast_parity_passes_on_fast_and_fallback_paths():
    for source in (
        'print 1 + 2 * 3',
        'let i = 0\nwhile i < 2 { print i\n i = i + 1 }',
        'function f(a) { return a + 1 }\nprint f(2)',
    ):
        parity = pealang.verify_fast_parity(compile_source_to_bytecode(source))
        assert parity['ok'], (source, parity)
        assert parity['output_match'] and parity['result_match']


def test_fast_interpreter_report_is_stable_and_gated():
    module = compile_source_to_bytecode('print 3 + 4')
    first = pealang.fast_interpreter_report(module, verify=True)
    second = pealang.fast_interpreter_report(module, verify=True)
    assert first == second
    assert first['version'] == pealang.FAST_INTERPRETER_VERSION == '3.1.39'
    assert first['mode'] == 'fast'
    assert first['output'] == ['7']
    assert first['parity']['ok']
    assert pealang.fast_interpreter_gate(first)['gate'] == 'PASS'


def test_benchmark_reports_medians_without_asserting_timing():
    module = compile_source_to_bytecode('print 1 + 2')
    report = pealang.fast_interpreter_report(module, benchmark=True)
    benchmark = report['benchmark']
    assert benchmark['iterations'] == 25
    assert benchmark['vm_median_ms'] >= 0
    assert benchmark['fast_median_ms'] >= 0


def test_gate_rejects_invalid_mode_and_failed_parity():
    assert pealang.fast_interpreter_gate({'mode': 'unknown'})['gate'] == 'FAIL'
    report = {'mode': 'fast', 'parity': {'ok': False}}
    result = pealang.fast_interpreter_gate(report)
    assert result['gate'] == 'FAIL'
    assert 'parity' in result['issues']


def test_cli_fast_command_passes_with_parity(tmp_path):
    source = tmp_path / 'app.pea'
    source.write_text('let x = 2\nprint x * 5\n', encoding='utf-8')
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'fast', str(source), '--verify'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['mode'] == 'fast'
    assert report['parity']['ok']
    assert report['version'] == '3.1.39'


def test_cli_fast_fallback_and_optimize_flag(tmp_path):
    source = tmp_path / 'app.pea'
    source.write_text(
        'function f(a) { return a + 1 }\nprint f(3)\n', encoding='utf-8')
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'fast', str(source),
         '--verify', '--optimize'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['mode'] == 'vm'
    assert not report['fast_path_supported']
    assert report['parity']['ok']


def test_feature_flag_and_help_document_fast_interpreter():
    assert feature_status('runtime.fast_interpreter_v3').stability == Stability.STABLE
    text = pea_help('fast')
    assert 'pea fast' in text
    assert 'verify_fast_parity()' in text


def test_release_metadata_is_aligned():
    assert pealang.__version__ == SPEC_VERSION == '5.20.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.20.0'
    assert manifest['previous_version'] == '5.19.0'
    assert pealang.FAST_INTERPRETER_VERSION == '3.1.39'
    assert pealang.CORE_RELEASE_FROZEN_AT == '3.1.37'
