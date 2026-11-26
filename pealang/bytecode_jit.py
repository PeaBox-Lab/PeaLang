"""Phase 73: profile-guided trace JIT for PeaLang bytecode.

This phase builds on the Phase 71 bytecode optimizer and Phase 72 fast
interpreter. A short profiling run records instruction counts; hot loop
back-edges become compiled traces whose integer arithmetic is specialized with
guards. A guard failure deoptimizes to the standard handler and execution
continues unchanged.

The JIT is an optimization only. It never changes language behavior, and
``verify_jit_parity()`` requires identical VM and JIT output and results before
a host adopts a compiled trace.
"""

from __future__ import annotations

import hashlib
import statistics
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable

from .bytecode import BytecodeModule
from .fast_interpreter import BINARY_OPS, FastFrame, FastProgram, compile_fast_program

BYTECODE_JIT_VERSION = '3.1.40'
SPECIALIZED_OPS = frozenset({'ADD', 'SUB', 'MUL'})
DEFAULT_THRESHOLD = 2
MAX_TRACES = 4
MAX_TRACE_STEPS = 64


class JITDeopt(Exception):
    """Raised inside a compiled trace when a specialization guard fails."""


@dataclass(frozen=True)
class JITProfile:
    """Instruction execution counts from a profiling run."""

    source_name: str
    counts: tuple[int, ...]
    total: int
    supported: bool

    def count(self, index: int) -> int:
        return self.counts[index] if 0 <= index < len(self.counts) else 0

    def to_dict(self) -> dict[str, Any]:
        return {
            'source_name': self.source_name,
            'instructions': len(self.counts),
            'total': self.total,
            'supported': self.supported,
        }


@dataclass(frozen=True)
class HotTrace:
    """A hot loop body selected for compilation."""

    entry: int
    backedge: int
    hits: int
    length: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompiledTrace:
    """A trace with pre-bound and integer-specialized handlers."""

    entry: int
    backedge: int
    guarded_ops: int
    handlers: tuple[Callable[[FastFrame], int | None], ...]

    @property
    def length(self) -> int:
        return len(self.handlers)

    def execute(self, frame: FastFrame, max_steps: int,
                max_instructions: int = 100_000) -> tuple[int, int]:
        """Run the trace and return ``(resume_ip, steps)``."""

        from .vm import VMError

        ip = self.entry
        steps = 0
        while self.entry <= ip <= self.backedge and steps < max_steps:
            if frame.steps >= max_instructions:
                raise VMError('VM instruction limit exceeded')
            frame.steps += 1
            steps += 1
            frame.ip = ip
            target = self.handlers[ip - self.entry](frame)
            ip = target if target is not None else ip + 1
        return ip, steps


def _counting_handler(handler, counts: list[int], index: int):
    def wrapped(frame: FastFrame) -> int | None:
        counts[index] += 1
        return handler(frame)
    return wrapped


def profile_execution(
    module: BytecodeModule, *, max_instructions: int = 100_000,
) -> JITProfile:
    """Record instruction counts with a non-emitting profiling run."""

    unsupported = JITProfile(module.source_name, (), 0, False)
    program = compile_fast_program(module, lambda _value: None)
    if program is None:
        return unsupported
    counts = [0] * len(program.instructions)
    instrumented = FastProgram(
        program.source_name,
        program.instructions,
        tuple(_counting_handler(handler, counts, index)
              for index, handler in enumerate(program.handlers)),
    )
    try:
        instrumented.execute({}, max_instructions)
    except Exception:
        return unsupported
    return JITProfile(
        source_name=module.source_name,
        counts=tuple(counts),
        total=sum(counts),
        supported=True,
    )


def select_traces(
    module: BytecodeModule, profile: JITProfile, *,
    threshold: int = DEFAULT_THRESHOLD, limit: int = MAX_TRACES,
) -> list[HotTrace]:
    """Choose the hottest eligible loop back-edges as JIT traces."""

    if not profile.supported or threshold <= 0:
        return []
    supported = set(BINARY_OPS) | {
        'CONST', 'NULL', 'TRUE', 'FALSE', 'LOAD', 'STORE', 'POP',
        'PRINT', 'NEG', 'NOT', 'JUMP', 'JUMP_IF_FALSE',
    }
    candidates: list[HotTrace] = []
    seen: set[tuple[int, int]] = set()
    for index, instruction in enumerate(module.code.instructions):
        if instruction.op != 'JUMP' or not isinstance(instruction.arg, int):
            continue
        entry = instruction.arg
        if not 0 <= entry <= index or (entry, index) in seen:
            continue
        hits = profile.count(index)
        if hits < threshold:
            continue
        body = module.code.instructions[entry:index + 1]
        if not body or any(item.op not in supported for item in body):
            continue
        seen.add((entry, index))
        candidates.append(HotTrace(entry, index, hits, len(body)))
    candidates.sort(key=lambda trace: (-trace.hits, trace.entry))
    return candidates[:max(1, limit)]


def _specialized_handler(operation: Callable[[Any, Any], Any]):
    def handler(frame: FastFrame) -> None:
        if len(frame.stack) < 2:
            raise JITDeopt()
        left = frame.stack[-2]
        right = frame.stack[-1]
        if type(left) is not int or type(right) is not int:
            raise JITDeopt()
        frame.stack.pop()
        frame.stack.pop()
        try:
            frame.stack.append(operation(left, right))
        except Exception as exc:
            from .vm import VMError

            raise VMError(str(exc)) from exc
    return handler


def compile_trace(
    module: BytecodeModule, trace: HotTrace, output=None,
) -> CompiledTrace | None:
    """Pre-bind a trace, specializing integer arithmetic with deopt guards."""

    program = compile_fast_program(module, output)
    if program is None:
        return None
    handlers: list[Callable[[FastFrame], int | None]] = []
    guarded = 0
    for index in range(trace.entry, trace.backedge + 1):
        instruction = module.code.instructions[index]
        if instruction.op in SPECIALIZED_OPS:
            handlers.append(_specialized_handler(BINARY_OPS[instruction.op]))
            guarded += 1
        else:
            handlers.append(program.handlers[index])
    return CompiledTrace(
        entry=trace.entry, backedge=trace.backedge,
        guarded_ops=guarded, handlers=tuple(handlers),
    )


class JITRuntime:
    """Execute bytecode with compiled traces where profiling found hot loops."""

    def __init__(self, output=None, *, threshold: int = DEFAULT_THRESHOLD,
                 max_instructions: int = 100_000,
                 max_trace_steps: int = MAX_TRACE_STEPS,
                 profile: JITProfile | None = None):
        self.output = output or print
        self.threshold = threshold
        self.max_instructions = max_instructions
        self.max_trace_steps = max_trace_steps
        self.profile = profile
        self.stats: dict[str, Any] = {}

    def run(self, module: BytecodeModule, globals: dict[str, Any] | None = None) -> Any:
        from .vm import VMError, VirtualMachine

        profile = self.profile or profile_execution(
            module, max_instructions=self.max_instructions)
        program = compile_fast_program(module, self.output)
        stats = {
            'profile_total': profile.total,
            'mode': 'vm' if program is None else 'jit',
            'traces_selected': 0,
            'traces_compiled': 0,
            'trace_steps': 0,
            'deopts': 0,
        }
        if program is None:
            result = VirtualMachine(
                self.output, max_instructions=self.max_instructions).run(module, globals)
            self.stats = stats
            return result

        traces = select_traces(module, profile, threshold=self.threshold)
        compiled = [item for item in (compile_trace(module, trace, self.output)
                                      for trace in traces) if item is not None]
        by_entry = {trace.entry: trace for trace in compiled}
        stats['traces_selected'] = len(traces)
        stats['traces_compiled'] = len(compiled)

        frame = FastFrame(dict(globals or {}))
        count = len(program.handlers)
        while not frame.halted and frame.ip < count:
            if frame.steps >= self.max_instructions:
                raise VMError('VM instruction limit exceeded')
            frame.steps += 1
            trace = by_entry.get(frame.ip)
            if trace is None:
                target = program.handlers[frame.ip](frame)
                frame.ip = target if target is not None else frame.ip + 1
                continue
            try:
                resume, steps = trace.execute(
                    frame, self.max_trace_steps, self.max_instructions)
                stats['trace_steps'] += steps
            except JITDeopt:
                stats['deopts'] += 1
                resume = frame.ip
                target = program.handlers[resume](frame)
                resume = target if target is not None else resume + 1
            frame.ip = resume
        self.stats = stats
        return None


def _standard_run(module: BytecodeModule) -> dict[str, Any]:
    from .vm import VirtualMachine

    output: list[Any] = []
    machine = VirtualMachine(output.append, max_instructions=100_000)
    result = machine.run(module)
    return {'output': output, 'result': result, 'instructions': machine.instructions}


def verify_jit_parity(module: BytecodeModule, **kwargs: Any) -> dict[str, Any]:
    """Require identical VM and JIT output and results."""

    baseline = _standard_run(module)
    output: list[Any] = []
    runtime = JITRuntime(output.append, **kwargs)
    result = runtime.run(module)
    candidate = {'output': output, 'result': result, 'stats': runtime.stats}
    ok = baseline['output'] == candidate['output'] and baseline['result'] == candidate['result']
    return {
        'ok': ok,
        'baseline': baseline,
        'jit': candidate,
        'output_match': baseline['output'] == candidate['output'],
        'result_match': baseline['result'] == candidate['result'],
    }


def benchmark_jit(module: BytecodeModule, iterations: int = 25) -> dict[str, Any]:
    """Compare median wall-clock time of the VM and JIT runtime."""

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

    baseline = sample(lambda: _standard_run(module))
    jit = sample(lambda: JITRuntime(lambda _value: None, threshold=1).run(module))
    base_time = statistics.median(baseline)
    jit_time = statistics.median(jit)
    return {
        'iterations': iterations,
        'vm_median_ms': round(base_time * 1000, 4),
        'jit_median_ms': round(jit_time * 1000, 4),
        'speedup': round(base_time / jit_time, 3) if jit_time else None,
    }


def bytecode_jit_report(
    module: BytecodeModule, *, threshold: int = DEFAULT_THRESHOLD,
    verify: bool = False, benchmark: bool = False,
) -> dict[str, Any]:
    """Return a deterministic report describing profiling and compilation."""

    profile = profile_execution(module)
    traces = select_traces(module, profile, threshold=threshold)
    compiled = [item for item in (compile_trace(module, trace) for trace in traces)
                if item is not None]
    output: list[Any] = []
    runtime = JITRuntime(output.append, threshold=threshold, profile=profile)
    result = runtime.run(module)
    report: dict[str, Any] = {
        'version': BYTECODE_JIT_VERSION,
        'module_digest': hashlib.sha256(
            module.dumps().encode('utf-8')).hexdigest(),
        'threshold': threshold,
        'profile': profile.to_dict(),
        'traces': [trace.to_dict() for trace in traces],
        'compiled_traces': [
            {'entry': item.entry, 'backedge': item.backedge,
             'guarded_ops': item.guarded_ops, 'length': item.length}
            for item in compiled],
        'stats': runtime.stats,
        'mode': runtime.stats['mode'],
        'output': [str(value) for value in output],
        'result': str(result),
        'gate': 'PASS',
    }
    if verify:
        report['parity'] = verify_jit_parity(module, threshold=threshold)
    if benchmark:
        report['benchmark'] = benchmark_jit(module)
    return report


def bytecode_jit_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Reduce a JIT report to a deterministic PASS/FAIL gate."""

    issues: list[str] = []
    if report.get('mode') not in ('jit', 'vm'):
        issues.append('mode')
    if report.get('gate') != 'PASS':
        issues.append('compilation')
    parity = report.get('parity')
    if parity is not None and not parity.get('ok'):
        issues.append('parity')
    return {'gate': 'PASS' if not issues else 'FAIL', 'issues': issues}


def build_bytecode_jit_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'BYTECODE_JIT_VERSION': BYTECODE_JIT_VERSION,
        'JITProfile': JITProfile,
        'HotTrace': HotTrace,
        'CompiledTrace': CompiledTrace,
        'profile_execution': profile_execution,
        'select_traces': select_traces,
        'compile_trace': compile_trace,
        'JITRuntime': JITRuntime,
        'verify_jit_parity': verify_jit_parity,
        'benchmark_jit': benchmark_jit,
        'bytecode_jit_report': bytecode_jit_report,
        'bytecode_jit_gate': bytecode_jit_gate,
        'build_bytecode_jit_namespace': build_bytecode_jit_namespace,
    }


__all__ = [
    'BYTECODE_JIT_VERSION', 'JITDeopt', 'JITProfile', 'HotTrace', 'CompiledTrace',
    'profile_execution', 'select_traces', 'compile_trace', 'JITRuntime',
    'verify_jit_parity', 'benchmark_jit', 'bytecode_jit_report',
    'bytecode_jit_gate', 'build_bytecode_jit_namespace',
]
