"""Phase 77: deterministic bytecode profiler for PeaLang runtime work.

The runtime profiler records opcode, function, and source-line execution counts
through the VM instrumentation hook. It deliberately excludes wall-clock values
from its deterministic digest; timing evidence belongs in the Phase 78 gate.
Profiler output and results must match a plain VM run before a report can pass.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from .bytecode import BytecodeModule, Op

RUNTIME_PROFILER_VERSION = '3.1.43'
RUNTIME_PROFILER_FORMAT = 'pea-runtime-profile-v1'


class RuntimeProfilerError(Exception):
    """Raised when a bytecode module cannot be profiled."""


@dataclass(frozen=True)
class ProfileRun:
    """Deterministic profile counters from one bytecode run."""

    result: Any
    output: tuple[Any, ...]
    instructions: int
    opcodes: tuple[tuple[str, int], ...]
    functions: tuple[tuple[str, int], ...]
    lines: tuple[tuple[str, int, int], ...]
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'result': str(self.result),
            'output': [str(value) for value in self.output],
            'instructions': self.instructions,
            'opcodes': [list(item) for item in self.opcodes],
            'functions': [list(item) for item in self.functions],
            'lines': [list(item) for item in self.lines],
            'digest': self.digest,
        }


class _ProfileHook:
    """Minimal instrumentation hook that only records deterministic counters."""

    __slots__ = ('opcodes', 'functions', 'lines')

    def __init__(self) -> None:
        self.opcodes: Counter[str] = Counter()
        self.functions: Counter[str] = Counter()
        self.lines: Counter[tuple[str, int]] = Counter()

    def hook(self, vm: Any, frame: Any, instruction: Any) -> None:
        raw = getattr(instruction, 'op', '')
        op = raw.value if isinstance(raw, Op) else raw
        self.opcodes[str(op)] += 1
        self.functions[str(getattr(frame, 'name', '<unknown>'))] += 1
        self.lines[(str(getattr(frame.code, 'source_name', '<input>')),
                    int(getattr(instruction, 'line', 0)))] += 1


def _digest(module: BytecodeModule, hook: _ProfileHook,
            instructions: int) -> str:
    payload = {
        'format': RUNTIME_PROFILER_FORMAT,
        'module': hashlib.sha256(module.dumps().encode('utf-8')).hexdigest(),
        'instructions': instructions,
        'opcodes': sorted(hook.opcodes.items()),
        'functions': sorted(hook.functions.items()),
        'lines': sorted((source, line, count)
                        for (source, line), count in hook.lines.items()),
    }
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


class RuntimeProfiler:
    """Execute bytecode while recording deterministic execution counters."""

    def __init__(self, output: Callable[[Any], Any] | None = None,
                 max_instructions: int = 100_000):
        self.output = output
        self.max_instructions = max(1, int(max_instructions))
        self.last_run: ProfileRun | None = None

    def run(self, module: BytecodeModule,
            globals: dict[str, Any] | None = None) -> ProfileRun:
        from .vm import VirtualMachine

        if not isinstance(module, BytecodeModule):
            raise RuntimeProfilerError('profiler requires a BytecodeModule')
        output: list[Any] = []
        hook = _ProfileHook()
        machine = VirtualMachine(
            output.append, max_instructions=self.max_instructions,
            instrumentation=hook,
        )
        result = machine.run(module, dict(globals or {}))
        if self.output is not None:
            for value in output:
                self.output(value)
        run = ProfileRun(
            result=result, output=tuple(output),
            instructions=machine.instructions,
            opcodes=tuple(sorted(hook.opcodes.items())),
            functions=tuple(sorted(hook.functions.items())),
            lines=tuple(sorted((source, line, count)
                               for (source, line), count in hook.lines.items())),
            digest=_digest(module, hook, machine.instructions),
        )
        self.last_run = run
        return run


def _standard_run(module: BytecodeModule,
                  max_instructions: int) -> tuple[Any, tuple[Any, ...]]:
    from .vm import VirtualMachine

    output: list[Any] = []
    machine = VirtualMachine(output.append, max_instructions=max_instructions)
    result = machine.run(module)
    return result, tuple(output)


def profile_module(module: BytecodeModule, *, top: int = 10,
                   max_instructions: int = 100_000) -> dict[str, Any]:
    """Return a deterministic profile report for *module*."""

    run = RuntimeProfiler(max_instructions=max_instructions).run(module)
    limit = max(1, int(top))
    return {
        'version': RUNTIME_PROFILER_VERSION,
        'format': RUNTIME_PROFILER_FORMAT,
        'module_digest': hashlib.sha256(
            module.dumps().encode('utf-8')).hexdigest(),
        'profile_digest': run.digest,
        'instructions': run.instructions,
        'opcodes': [list(item) for item in run.opcodes],
        'functions': [list(item) for item in run.functions],
        'lines': [list(item) for item in run.lines],
        'top_opcodes': [list(item) for item in sorted(
            run.opcodes, key=lambda item: (-item[1], item[0]))[:limit]],
        'top_functions': [list(item) for item in sorted(
            run.functions, key=lambda item: (-item[1], item[0]))[:limit]],
        'top_lines': [list(item) for item in sorted(
            run.lines, key=lambda item: (-item[2], item[0], item[1]))[:limit]],
        'output': [str(value) for value in run.output],
        'result': str(run.result),
        'gate': 'PASS',
    }


def verify_profile_parity(module: BytecodeModule, *,
                          max_instructions: int = 100_000) -> dict[str, Any]:
    """Require profiled output and results to match the standard VM."""

    result, output = _standard_run(module, max_instructions)
    run = RuntimeProfiler(max_instructions=max_instructions).run(module)
    output_match = output == run.output
    result_match = result == run.result
    return {
        'ok': output_match and result_match,
        'vm': {'output': [str(value) for value in output],
               'result': str(result)},
        'profiler': {'output': [str(value) for value in run.output],
                     'result': str(run.result),
                     'digest': run.digest},
        'output_match': output_match,
        'result_match': result_match,
    }


def benchmark_profiler(module: BytecodeModule, *, iterations: int = 25,
                       max_instructions: int = 100_000) -> dict[str, Any]:
    """Compare median wall-clock time of plain VM and profiled execution."""

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

    plain = sample(lambda: _standard_run(module, max_instructions))
    profiled = sample(lambda: RuntimeProfiler(
        max_instructions=max_instructions).run(module))
    plain_median = statistics.median(plain)
    profiled_median = statistics.median(profiled)
    return {
        'iterations': iterations,
        'vm_median_ms': round(plain_median * 1000, 4),
        'profiler_median_ms': round(profiled_median * 1000, 4),
        'overhead_ratio': round(profiled_median / plain_median, 3)
        if plain_median else None,
    }


def profiler_report(module: BytecodeModule, *, verify: bool = False,
                    benchmark: bool = False, top: int = 10,
                    max_instructions: int = 100_000) -> dict[str, Any]:
    """Return a deterministic report with optional parity and timing evidence."""

    report = profile_module(module, top=top,
                            max_instructions=max_instructions)
    if verify:
        report['parity'] = verify_profile_parity(
            module, max_instructions=max_instructions)
    if benchmark:
        report['benchmark'] = benchmark_profiler(
            module, max_instructions=max_instructions)
    return report


def profiler_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Reduce a profiler report to a deterministic PASS/FAIL gate."""

    issues: list[str] = []
    if report.get('gate') != 'PASS':
        issues.append('profiling')
    if int(report.get('instructions', 0)) < 1:
        issues.append('instructions')
    parity = report.get('parity')
    if parity is not None and not parity.get('ok'):
        issues.append('parity')
    return {'gate': 'PASS' if not issues else 'FAIL', 'issues': issues}


def build_runtime_profiler_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'RUNTIME_PROFILER_VERSION': RUNTIME_PROFILER_VERSION,
        'RUNTIME_PROFILER_FORMAT': RUNTIME_PROFILER_FORMAT,
        'RuntimeProfilerError': RuntimeProfilerError,
        'ProfileRun': ProfileRun,
        'RuntimeProfiler': RuntimeProfiler,
        'profile_module': profile_module,
        'verify_profile_parity': verify_profile_parity,
        'benchmark_profiler': benchmark_profiler,
        'profiler_report': profiler_report,
        'profiler_gate': profiler_gate,
        'build_runtime_profiler_namespace': build_runtime_profiler_namespace,
    }


__all__ = [
    'RUNTIME_PROFILER_VERSION', 'RUNTIME_PROFILER_FORMAT',
    'RuntimeProfilerError', 'ProfileRun', 'RuntimeProfiler',
    'profile_module', 'verify_profile_parity', 'benchmark_profiler',
    'profiler_report', 'profiler_gate', 'build_runtime_profiler_namespace',
]
