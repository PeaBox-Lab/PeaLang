"""Phase 71: deterministic peephole optimizer for portable PeaLang bytecode.

Wave 2 starts by optimizing the bytecode that the existing compiler already
emits. The passes are intentionally conservative: they only rewrite bytecode
when the result is provably equivalent, and they never change the frozen 3.0
language surface.

Passes:

``constant_folding``
    Fold ``CONST a, CONST b, OP`` triples (and unary ``NEG``) into one ``CONST``.
    Only numeric arithmetic and same-type comparisons are folded, and division
    by zero is left untouched.

``dead_push_pop``
    Remove a literal push (``CONST``/``NULL``/``TRUE``/``FALSE``) immediately
    followed by ``POP``. Literal pushes have no side effects.

``unreachable_code``
    Drop instructions that cannot be reached from entry or from any jump,
    handler, or iterator end target, then remap every remaining jump target.

Optimization always operates on a deep copy of the supplied module, so the
original artifact is preserved for parity checking and evidence.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import operator
from dataclasses import dataclass
from typing import Any, Callable

from .bytecode import BytecodeModule, Instruction

OPTIMIZER_VERSION = '3.1.38'
CORE_RELEASE_FROZEN_AT = '3.1.37'

ARITHMETIC_OPS: dict[str, Callable[[Any, Any], Any]] = {
    'ADD': operator.add,
    'SUB': operator.sub,
    'MUL': operator.mul,
    'DIV': operator.truediv,
    'MOD': operator.mod,
}
COMPARISON_OPS: dict[str, Callable[[Any, Any], Any]] = {
    'EQ': operator.eq,
    'NE': operator.ne,
    'LT': operator.lt,
    'LE': operator.le,
    'GT': operator.gt,
    'GE': operator.ge,
}
LITERAL_OPS = frozenset({'CONST', 'NULL', 'TRUE', 'FALSE'})
UNCONDITIONAL_TERMINATORS = frozenset({'HALT', 'RETURN', 'RAISE', 'JUMP'})
JUMP_OPS = frozenset({'JUMP', 'JUMP_IF_FALSE'})
TARGET_HOLDERS = frozenset({'PUSH_HANDLER', 'ITER_NEXT'})
TARGET_KEYS = ('catch', 'finally', 'end')

_MISSING = object()


@dataclass(frozen=True)
class OptimizationStats:
    """Counts from one optimization run."""

    constant_folding: int = 0
    dead_push_pop: int = 0
    unreachable_code: int = 0
    instructions_before: int = 0
    instructions_after: int = 0
    constants_before: int = 0
    constants_after: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            'constant_folding': self.constant_folding,
            'dead_push_pop': self.dead_push_pop,
            'unreachable_code': self.unreachable_code,
            'instructions_before': self.instructions_before,
            'instructions_after': self.instructions_after,
            'constants_before': self.constants_before,
            'constants_after': self.constants_after,
        }


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _constant_value(constants: list[Any], arg: Any) -> Any:
    if not _is_int(arg) or not 0 <= arg < len(constants):
        return _MISSING
    return constants[arg]


def _intern_constant(constants: list[Any], value: Any) -> int:
    """Append a constant, reusing an existing entry of the exact same type."""

    for index, existing in enumerate(constants):
        if type(existing) is type(value) and existing == value:
            return index
    constants.append(value)
    return len(constants) - 1


def _foldable_value(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return True
    if isinstance(value, (int, float)):
        try:
            return math.isfinite(value)
        except (OverflowError, ValueError):
            return False
    return isinstance(value, str)


def _fold_pair(op: str, left: Any, right: Any) -> tuple[bool, Any]:
    if op in ARITHMETIC_OPS:
        if not (_is_number(left) and _is_number(right)):
            return False, None
    elif op in COMPARISON_OPS:
        numeric = _is_number(left) and _is_number(right)
        textual = isinstance(left, str) and isinstance(right, str)
        if not (numeric or textual):
            return False, None
    else:
        return False, None
    try:
        result = ARITHMETIC_OPS.get(op, COMPARISON_OPS.get(op))(left, right)
    except (ZeroDivisionError, TypeError, ValueError, OverflowError):
        return False, None
    if not _foldable_value(result):
        return False, None
    return True, result


def fold_constants(
    instructions: list[Instruction], constants: list[Any],
) -> tuple[list[Instruction], int]:
    """Fold literal arithmetic/comparisons into single ``CONST`` pushes."""

    out: list[Instruction] = []
    index = 0
    applied = 0
    while index < len(instructions):
        current = instructions[index]
        if current.op == 'CONST' and index + 1 < len(instructions):
            following = instructions[index + 1]
            if following.op == 'NEG':
                value = _constant_value(constants, current.arg)
                if _is_number(value) and _foldable_value(-value):
                    out.append(Instruction(
                        'CONST', _intern_constant(constants, -value), following.line))
                    applied += 1
                    index += 2
                    continue
            if index + 2 < len(instructions) and following.op == 'CONST':
                operation = instructions[index + 2]
                if operation.op in ARITHMETIC_OPS or operation.op in COMPARISON_OPS:
                    left = _constant_value(constants, current.arg)
                    right = _constant_value(constants, following.arg)
                    if left is not _MISSING and right is not _MISSING:
                        ok, result = _fold_pair(operation.op, left, right)
                        if ok:
                            out.append(Instruction(
                                'CONST', _intern_constant(constants, result),
                                operation.line))
                            applied += 1
                            index += 3
                            continue
        out.append(current)
        index += 1
    return out, applied


def remove_dead_pushes(
    instructions: list[Instruction],
) -> tuple[list[Instruction], int]:
    """Remove literal pushes whose value is immediately discarded."""

    out: list[Instruction] = []
    index = 0
    applied = 0
    while index < len(instructions):
        current = instructions[index]
        if (current.op in LITERAL_OPS and index + 1 < len(instructions)
                and instructions[index + 1].op == 'POP'):
            index += 2
            applied += 1
            continue
        out.append(current)
        index += 1
    return out, applied


def _jump_targets(instruction: Instruction) -> list[int]:
    op = instruction.op
    arg = instruction.arg
    if op in JUMP_OPS and _is_int(arg):
        return [arg]
    if op in TARGET_HOLDERS and isinstance(arg, dict):
        return [arg[key] for key in TARGET_KEYS
                if _is_int(arg.get(key))]
    return []


def _successors(instructions: list[Instruction], index: int) -> list[int]:
    instruction = instructions[index]
    targets = _jump_targets(instruction)
    if instruction.op in UNCONDITIONAL_TERMINATORS:
        return targets
    return targets + ([index + 1] if index + 1 < len(instructions) else [])


def remove_unreachable(
    instructions: list[Instruction],
) -> tuple[list[Instruction], int]:
    """Remove unreachable instructions and remap all jump targets."""

    if not instructions:
        return [], 0
    referenced = {target for instruction in instructions
                  for target in _jump_targets(instruction)}
    reachable: set[int] = set()
    pending = [0]
    while pending:
        index = pending.pop()
        if index in reachable or not 0 <= index < len(instructions):
            continue
        reachable.add(index)
        pending.extend(_successors(instructions, index))
    keep = sorted(reachable | {index for index in referenced
                               if 0 <= index < len(instructions)})
    if len(keep) == len(instructions):
        return instructions, 0
    remap = {old: new for new, old in enumerate(keep)}
    end = len(keep)
    optimized: list[Instruction] = []
    for old in keep:
        instruction = instructions[old]
        if instruction.op in JUMP_OPS and _is_int(instruction.arg):
            instruction = Instruction(
                instruction.op, remap.get(instruction.arg, end), instruction.line)
        elif instruction.op in TARGET_HOLDERS and isinstance(instruction.arg, dict):
            arg = dict(instruction.arg)
            for key in TARGET_KEYS:
                if _is_int(arg.get(key)):
                    arg[key] = remap.get(arg[key], end)
            instruction = Instruction(instruction.op, arg, instruction.line)
        optimized.append(instruction)
    return optimized, len(instructions) - len(keep)


class BytecodeOptimizer:
    """Configurable optimizer; passes default to enabled."""

    def __init__(self, *, constant_folding: bool = True,
                 dead_push_pop: bool = True, unreachable_code: bool = True):
        self.constant_folding = constant_folding
        self.dead_push_pop = dead_push_pop
        self.unreachable_code = unreachable_code
        self.stats: OptimizationStats | None = None

    def optimize(self, module: BytecodeModule) -> BytecodeModule:
        optimized = copy.deepcopy(module)
        counts = {'constant_folding': 0, 'dead_push_pop': 0,
                  'unreachable_code': 0}
        before = sum(len(code.instructions) for code in self._code_objects(optimized))
        constants_before = len(optimized.constants)

        for code in self._code_objects(optimized):
            if self.constant_folding:
                code.instructions, applied = fold_constants(
                    code.instructions, optimized.constants)
                counts['constant_folding'] += applied
            if self.dead_push_pop:
                code.instructions, applied = remove_dead_pushes(code.instructions)
                counts['dead_push_pop'] += applied
            if self.unreachable_code:
                code.instructions, applied = remove_unreachable(code.instructions)
                counts['unreachable_code'] += applied

        after = sum(len(code.instructions) for code in self._code_objects(optimized))
        self.stats = OptimizationStats(
            constant_folding=counts['constant_folding'],
            dead_push_pop=counts['dead_push_pop'],
            unreachable_code=counts['unreachable_code'],
            instructions_before=before,
            instructions_after=after,
            constants_before=constants_before,
            constants_after=len(optimized.constants),
        )
        return optimized

    @staticmethod
    def _code_objects(module: BytecodeModule) -> list[Any]:
        return [module.code, *module.functions.values()]


def optimize_bytecode(module: BytecodeModule, **hints: bool) -> BytecodeModule:
    """Return an optimized deep copy of *module*."""

    return BytecodeOptimizer(**hints).optimize(module)


def optimize_report(module: BytecodeModule, **hints: bool) -> dict[str, Any]:
    """Return deterministic optimization statistics and a digest."""

    optimizer = BytecodeOptimizer(**hints)
    optimized = optimizer.optimize(module)
    stats = optimizer.stats or OptimizationStats()
    payload = {
        'version': OPTIMIZER_VERSION,
        'frozen_at': CORE_RELEASE_FROZEN_AT,
        'stats': stats.to_dict(),
        'digest': hashlib.sha256(optimized.dumps().encode('utf-8')).hexdigest(),
    }
    return {**payload, 'gate': 'PASS' if _report_ok(payload) else 'FAIL'}


def _report_ok(payload: dict[str, Any]) -> bool:
    stats = payload['stats']
    return (stats['instructions_after'] <= stats['instructions_before']
            and stats['constants_after'] >= stats['constants_before'])


def bytecode_optimizer_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Reduce an optimization report (and optional parity check) to PASS/FAIL."""

    issues: list[str] = []
    if report.get('gate') != 'PASS':
        issues.append('optimization')
    if report.get('parity') is not None and not report['parity'].get('ok'):
        issues.append('parity')
    return {'gate': 'PASS' if not issues else 'FAIL', 'issues': issues}


def verify_optimization(
    before: BytecodeModule, after: BytecodeModule, *,
    max_instructions: int = 100_000,
) -> dict[str, Any]:
    """Run both modules on the VM and compare output and return value."""

    from .vm import VirtualMachine

    def run(module: BytecodeModule) -> dict[str, Any]:
        output: list[Any] = []
        machine = VirtualMachine(output.append, max_instructions=max_instructions)
        result = machine.run(module)
        return {'output': output, 'result': result,
                'instructions': machine.instructions}

    baseline = run(before)
    optimized = run(after)
    ok = baseline['output'] == optimized['output'] and baseline['result'] == optimized['result']
    return {
        'ok': ok,
        'baseline': baseline,
        'optimized': optimized,
        'output_match': baseline['output'] == optimized['output'],
        'result_match': baseline['result'] == optimized['result'],
    }


def build_bytecode_optimizer_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'OPTIMIZER_VERSION': OPTIMIZER_VERSION,
        'CORE_RELEASE_FROZEN_AT': CORE_RELEASE_FROZEN_AT,
        'OptimizationStats': OptimizationStats,
        'BytecodeOptimizer': BytecodeOptimizer,
        'fold_constants': fold_constants,
        'remove_dead_pushes': remove_dead_pushes,
        'remove_unreachable': remove_unreachable,
        'optimize_bytecode': optimize_bytecode,
        'optimize_report': optimize_report,
        'bytecode_optimizer_gate': bytecode_optimizer_gate,
        'verify_optimization': verify_optimization,
        'build_bytecode_optimizer_namespace': build_bytecode_optimizer_namespace,
    }


__all__ = [
    'OPTIMIZER_VERSION', 'CORE_RELEASE_FROZEN_AT', 'OptimizationStats',
    'BytecodeOptimizer', 'fold_constants', 'remove_dead_pushes',
    'remove_unreachable', 'optimize_bytecode', 'optimize_report',
    'bytecode_optimizer_gate', 'verify_optimization',
    'build_bytecode_optimizer_namespace',
]
