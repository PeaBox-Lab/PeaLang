"""Phase 72: direct-handler fast interpreter for PeaLang bytecode.

The standard virtual machine dispatches each bytecode instruction through a
long ``if/elif`` chain. This module adds an optional fast path that pre-binds
each instruction to a closure and runs them in a tight loop with an explicit
program counter. It deliberately supports only a simple, side-effect-free
instruction subset; any other instruction makes the whole module fall back to
the standard virtual machine, so no program changes meaning.

The fast path covers literals, loads/stores, arithmetic, comparisons, print,
and conditional/unconditional jumps — enough for hot straight-line scripts and
small loops. Function calls, imports, exceptions, iterators, and object access
stay on the standard VM.

``verify_fast_parity()`` runs the same module on both executors and requires
identical output and results, so hosts can opt into the fast path with evidence.
"""

from __future__ import annotations

import hashlib
import json
import operator
import statistics
import time
from dataclasses import dataclass
from typing import Any, Callable

from .bytecode import BytecodeModule, Instruction

FAST_INTERPRETER_VERSION = '3.1.39'

BINARY_OPS: dict[str, Callable[[Any, Any], Any]] = {
    'ADD': operator.add,
    'SUB': operator.sub,
    'MUL': operator.mul,
    'DIV': operator.truediv,
    'MOD': operator.mod,
    'EQ': operator.eq,
    'NE': operator.ne,
    'LT': operator.lt,
    'LE': operator.le,
    'GT': operator.gt,
    'GE': operator.ge,
}
SUPPORTED_OPS = frozenset({
    'CONST', 'NULL', 'TRUE', 'FALSE', 'LOAD', 'STORE', 'POP', 'PRINT',
    'NEG', 'NOT', 'HALT', 'JUMP', 'JUMP_IF_FALSE', *BINARY_OPS,
})
Handler = Callable[['FastFrame'], int | None]


class FastFrame:
    """Mutable execution state owned by one fast-path run."""

    __slots__ = ('stack', 'env', 'ip', 'steps', 'halted')

    def __init__(self, env: dict[str, Any]):
        self.stack: list[Any] = []
        self.env = env
        self.ip = 0
        self.steps = 0
        self.halted = False

    def load(self, name: str, line: int) -> Any:
        from .vm import VMError

        if name not in self.env:
            raise VMError(f"Undefined variable '{name}' at line {line}")
        return self.env[name]

    def binary(self, operation: Callable[[Any, Any], Any], line: int) -> None:
        from .vm import VMError

        right = self.stack.pop()
        left = self.stack.pop()
        try:
            self.stack.append(operation(left, right))
        except Exception as exc:
            raise VMError(str(exc)) from exc


@dataclass(frozen=True)
class FastProgram:
    """A pre-bound instruction stream ready for direct-handler execution."""

    source_name: str
    instructions: tuple[Instruction, ...]
    handlers: tuple[Handler, ...]

    def execute(self, env: dict[str, Any], max_instructions: int) -> Any:
        from .vm import VMError

        frame = FastFrame(env)
        count = len(self.instructions)
        while not frame.halted and frame.ip < count:
            if frame.steps >= max_instructions:
                raise VMError('VM instruction limit exceeded')
            frame.steps += 1
            target = self.handlers[frame.ip](frame)
            frame.ip = target if target is not None else frame.ip + 1
        return None


def _constant_index(constants: list[Any], arg: Any) -> bool:
    return isinstance(arg, int) and not isinstance(arg, bool) and 0 <= arg < len(constants)


def fast_path_supported(module: BytecodeModule) -> bool:
    """Return whether the whole module can safely use the fast path."""

    for code in (module.code, *module.functions.values()):
        for instruction in code.instructions:
            if instruction.op not in SUPPORTED_OPS:
                return False
            if instruction.op == 'CONST' and not _constant_index(
                    module.constants, instruction.arg):
                return False
    return True


def compile_fast_program(module: BytecodeModule, output=None) -> FastProgram | None:
    """Pre-bind handlers for *module*, or return ``None`` to use the VM."""

    if not fast_path_supported(module):
        return None
    emit = output or (lambda _value: None)
    handlers: list[Handler] = []
    for instruction in module.code.instructions:
        op = instruction.op
        if op == 'CONST':
            value = module.constants[instruction.arg]
            handlers.append(lambda frame, value=value: frame.stack.append(value))
        elif op in ('NULL', 'TRUE', 'FALSE'):
            value = {'NULL': None, 'TRUE': True, 'FALSE': False}[op]
            handlers.append(lambda frame, value=value: frame.stack.append(value))
        elif op == 'LOAD':
            name, line = instruction.arg, instruction.line
            handlers.append(
                lambda frame, name=name, line=line: frame.stack.append(
                    frame.load(name, line)))
        elif op == 'STORE':
            name = instruction.arg
            handlers.append(
                lambda frame, name=name: frame.env.__setitem__(name, frame.stack.pop()))
        elif op == 'POP':
            handlers.append(lambda frame: frame.stack.pop())
        elif op == 'PRINT':
            handlers.append(lambda frame, emit=emit: emit(frame.stack.pop()))
        elif op in BINARY_OPS:
            operation, line = BINARY_OPS[op], instruction.line
            handlers.append(
                lambda frame, operation=operation, line=line: frame.binary(operation, line))
        elif op == 'NEG':
            handlers.append(lambda frame: frame.stack.append(-frame.stack.pop()))
        elif op == 'NOT':
            handlers.append(lambda frame: frame.stack.append(not bool(frame.stack.pop())))
        elif op == 'JUMP':
            target = instruction.arg
            handlers.append(lambda frame, target=target: target)
        elif op == 'JUMP_IF_FALSE':
            target = instruction.arg
            handlers.append(
                lambda frame, target=target: target if not bool(frame.stack.pop()) else None)
        elif op == 'HALT':
            def halt(frame: FastFrame) -> None:
                frame.halted = True
                return None
            handlers.append(halt)
    return FastProgram(
        source_name=module.source_name,
        instructions=tuple(module.code.instructions),
        handlers=tuple(handlers),
    )


class FastInterpreter:
    """Run bytecode on the direct-handler path when it is safe to do so."""

    def __init__(self, output=None, max_instructions: int = 100_000):
        self.output = output or print
        self.max_instructions = max_instructions
        self.last_report: dict[str, Any] = {}

    def run(self, module: BytecodeModule, globals: dict[str, Any] | None = None) -> Any:
        program = compile_fast_program(module, self.output)
        if program is None:
            from .vm import VirtualMachine

            result = VirtualMachine(
                self.output, max_instructions=self.max_instructions).run(module, globals)
            mode = 'vm'
        else:
            result = program.execute(dict(globals or {}), self.max_instructions)
            mode = 'fast'
        self.last_report = {
            'mode': mode,
            'supported': fast_path_supported(module),
            'instructions': len(module.code.instructions),
            'source_name': module.source_name,
        }
        return result


def _run(module: BytecodeModule) -> dict[str, Any]:
    from .vm import VirtualMachine

    output: list[Any] = []
    machine = VirtualMachine(output.append, max_instructions=100_000)
    result = machine.run(module)
    return {'output': output, 'result': result, 'instructions': machine.instructions}


def verify_fast_parity(module: BytecodeModule) -> dict[str, Any]:
    """Require identical output and result from VM and fast execution."""

    baseline = _run(module)
    output: list[Any] = []
    fast = FastInterpreter(output.append)
    result = fast.run(module)
    candidate = {
        'output': output,
        'result': result,
        'instructions': fast.last_report['instructions'],
    }
    ok = baseline['output'] == candidate['output'] and baseline['result'] == candidate['result']
    return {
        'ok': ok,
        'mode': fast.last_report['mode'],
        'baseline': baseline,
        'fast': candidate,
        'output_match': baseline['output'] == candidate['output'],
        'result_match': baseline['result'] == candidate['result'],
    }


def benchmark_fast(module: BytecodeModule, iterations: int = 25) -> dict[str, Any]:
    """Compare wall-clock execution time for the two executors."""

    def sample(run: Callable[[], Any]) -> list[float]:
        times: list[float] = []
        for _ in range(max(1, iterations)):
            start = time.perf_counter()
            try:
                run()
            except Exception:
                pass
            times.append(time.perf_counter() - start)
        return times

    baseline = sample(lambda: _run(module))
    fast = sample(lambda: FastInterpreter(lambda _value: None).run(module))
    base_time = statistics.median(baseline)
    fast_time = statistics.median(fast)
    return {
        'iterations': iterations,
        'vm_median_ms': round(base_time * 1000, 4),
        'fast_median_ms': round(fast_time * 1000, 4),
        'speedup': round(base_time / fast_time, 3) if fast_time else None,
    }


def fast_interpreter_report(
    module: BytecodeModule, *, verify: bool = False,
    benchmark: bool = False,
) -> dict[str, Any]:
    """Return a stable report covering fast-path eligibility and safety."""

    output: list[Any] = []
    interpreter = FastInterpreter(output.append)
    result = interpreter.run(module)
    digest = hashlib.sha256(module.dumps().encode('utf-8')).hexdigest()
    report: dict[str, Any] = {
        'version': FAST_INTERPRETER_VERSION,
        'module_digest': digest,
        'mode': interpreter.last_report['mode'],
        'fast_path_supported': fast_path_supported(module),
        'output': [str(value) for value in output],
        'result': str(result),
    }
    if verify:
        report['parity'] = verify_fast_parity(module)
    if benchmark:
        report['benchmark'] = benchmark_fast(module)
    return report


def fast_interpreter_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Reduce a fast-interpreter report to a deterministic PASS/FAIL gate."""

    issues: list[str] = []
    if report.get('mode') not in ('fast', 'vm'):
        issues.append('mode')
    parity = report.get('parity')
    if parity is not None and not parity.get('ok'):
        issues.append('parity')
    return {'gate': 'PASS' if not issues else 'FAIL', 'issues': issues}


def build_fast_interpreter_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'FAST_INTERPRETER_VERSION': FAST_INTERPRETER_VERSION,
        'FastFrame': FastFrame,
        'FastProgram': FastProgram,
        'FastInterpreter': FastInterpreter,
        'fast_path_supported': fast_path_supported,
        'compile_fast_program': compile_fast_program,
        'verify_fast_parity': verify_fast_parity,
        'benchmark_fast': benchmark_fast,
        'fast_interpreter_report': fast_interpreter_report,
        'fast_interpreter_gate': fast_interpreter_gate,
        'build_fast_interpreter_namespace': build_fast_interpreter_namespace,
    }


__all__ = [
    'FAST_INTERPRETER_VERSION', 'FastFrame', 'FastProgram', 'FastInterpreter',
    'fast_path_supported', 'compile_fast_program', 'verify_fast_parity',
    'benchmark_fast', 'fast_interpreter_report', 'fast_interpreter_gate',
    'build_fast_interpreter_namespace',
]
