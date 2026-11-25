"""Phase 71: conservative bytecode optimizer and VM parity gate."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
from pealang.bytecode import BytecodeModule, Instruction
from pealang.compatibility import Stability, feature_status
from pealang.compiler import compile_source_to_bytecode
from pealang.help import help as pea_help
from pealang.specification import SPEC_VERSION


def _run(module):
    from pealang.vm import VirtualMachine

    output = []
    machine = VirtualMachine(output.append, max_instructions=10_000)
    result = machine.run(module)
    return output, result


def test_constant_folding_on_real_compiler_output():
    module = compile_source_to_bytecode('print 1 + 2 * 3')
    optimized = pealang.optimize_bytecode(module)
    assert optimized is not module
    assert module.to_dict() == compile_source_to_bytecode(
        'print 1 + 2 * 3').to_dict(), 'original module was mutated'
    assert sum(i.op == 'CONST' for i in optimized.code.instructions) < sum(
        i.op == 'CONST' for i in module.code.instructions)
    assert _run(optimized)[0] == [7]


def test_constant_folding_handles_comparisons_negation_and_zero_division():
    instructions = [
        Instruction('CONST', 0), Instruction('CONST', 1), Instruction('MUL'),
        Instruction('POP'),
        Instruction('CONST', 2), Instruction('CONST', 3), Instruction('LT'),
        Instruction('POP'),
        Instruction('CONST', 4), Instruction('NEG'), Instruction('POP'),
        Instruction('CONST', 5), Instruction('CONST', 6), Instruction('DIV'),
        Instruction('POP'),
        Instruction('HALT'),
    ]
    folded, applied = pealang.fold_constants(instructions, [2, 3, 7, 4, 9, 1, 0])
    assert applied == 3
    assert [i.op for i in folded].count('DIV') == 1


def test_dead_literal_pushes_are_removed():
    instructions = [
        Instruction('CONST', 0), Instruction('POP'),
        Instruction('NULL'), Instruction('POP'),
        Instruction('TRUE'), Instruction('POP'),
        Instruction('PRINT'), Instruction('HALT'),
    ]
    pruned, applied = pealang.remove_dead_pushes(instructions)
    assert applied == 3
    assert [i.op for i in pruned] == ['PRINT', 'HALT']


def test_unreachable_code_remapping_preserves_jump_targets():
    instructions = [
        Instruction('LOAD', 'x'),
        Instruction('JUMP_IF_FALSE', 4),
        Instruction('CONST', 0),
        Instruction('PRINT'),
        Instruction('JUMP', 7),
        Instruction('CONST', 0),
        Instruction('PRINT'),
        Instruction('HALT'),
    ]
    optimized, applied = pealang.remove_unreachable(instructions)
    assert applied == 2
    assert [i.op for i in optimized] == [
        'LOAD', 'JUMP_IF_FALSE', 'CONST', 'PRINT', 'JUMP', 'HALT']
    assert optimized[1].arg == 4
    assert optimized[4].arg == 5


def test_unreachable_code_remapping_preserves_handler_targets():
    instructions = [
        Instruction('PUSH_HANDLER', {'catch': 3, 'finally': None, 'end': None}),
        Instruction('HALT'),
        Instruction('CONST', 0),
        Instruction('PRINT'),
        Instruction('HALT'),
    ]
    optimized, applied = pealang.remove_unreachable(instructions)
    assert applied == 1
    assert optimized[0].arg['catch'] == 2


def test_report_is_deterministic_and_gate_passes():
    module = compile_source_to_bytecode('print 2 + 3')
    first = pealang.optimize_report(module)
    second = pealang.optimize_report(module)
    assert first == second
    assert first['gate'] == 'PASS'
    assert first['version'] == pealang.OPTIMIZER_VERSION == '3.1.38'
    assert first['stats']['constant_folding'] == 1
    assert first['stats']['instructions_after'] < first['stats']['instructions_before']
    assert pealang.bytecode_optimizer_gate(first)['gate'] == 'PASS'


def test_gate_rejects_failed_optimization_and_failed_parity():
    report = {'gate': 'FAIL'}
    result = pealang.bytecode_optimizer_gate(report)
    assert result['gate'] == 'FAIL'
    assert 'optimization' in result['issues']
    report = {'gate': 'PASS', 'parity': {'ok': False}}
    result = pealang.bytecode_optimizer_gate(report)
    assert result['gate'] == 'FAIL'
    assert 'parity' in result['issues']


def test_parity_across_representative_programs():
    sources = [
        'print 1 + 2 * 3',
        'let x = 5\nif x > 3 { print 10 } else { print 20 }',
        'let i = 0\nwhile i < 3 { print i\n i = i + 1 }',
        'function f(a) { return a + 1 }\nprint f(2)',
        'for x in [1,2,3] { if x == 2 { continue } print x }',
        'try { print 1\n throw 5 } catch e { print 2 } finally { print 3 }',
    ]
    for source in sources:
        module = compile_source_to_bytecode(source)
        optimized = pealang.optimize_bytecode(module)
        parity = pealang.verify_optimization(module, optimized)
        assert parity['ok'], (source, parity)
        assert parity['output_match'] and parity['result_match']


def test_function_code_objects_are_optimized_too():
    module = compile_source_to_bytecode(
        'function f() { print 4 + 5\n return 1 }\nprint f()')
    optimizer = pealang.BytecodeOptimizer()
    optimized = optimizer.optimize(module)
    assert optimizer.stats is not None
    assert any(
        'ADD' not in [i.op for i in code.instructions]
        for code in optimized.functions.values()
    )
    assert _run(optimized)[0] == [9, 1]


def test_passes_can_be_disabled_independently():
    module = compile_source_to_bytecode('print 1 + 2')
    disabled = pealang.optimize_bytecode(module, constant_folding=False)
    assert disabled.to_dict() == module.to_dict()
    enabled = pealang.optimize_bytecode(module, constant_folding=True)
    assert enabled.to_dict() != module.to_dict()


def test_cli_optimize_command_passes_with_parity(tmp_path):
    source = tmp_path / 'app.pea'
    source.write_text('print 1 + 2\n', encoding='utf-8')
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'optimize', str(source), '--verify'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['gate'] == 'PASS'
    assert report['parity']['ok']
    assert report['version'] == '3.1.38'


def test_cli_optimize_can_save_optimized_artifact(tmp_path):
    source = tmp_path / 'app.pea'
    source.write_text('print 4 * 5\n', encoding='utf-8')
    output = tmp_path / 'app.opt.peac'
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'optimize', str(source),
         '-o', str(output)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    assert output.is_file()
    assert BytecodeModule.load(output).source_name == str(source)


def test_feature_flag_and_help_document_optimizer():
    assert feature_status('runtime.bytecode_optimizer_v3').stability == Stability.STABLE
    text = pea_help('optimize')
    assert 'pea optimize' in text
    assert 'verify_optimization()' in text


def test_release_metadata_is_aligned():
    assert pealang.__version__ == SPEC_VERSION == '3.1.38'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '3.1.38'
    assert manifest['previous_version'] == '3.1.37'
    assert pealang.CORE_RELEASE_FROZEN_AT == '3.1.37'
