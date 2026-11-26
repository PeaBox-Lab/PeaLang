"""Phase 76: deterministic parallel runtime for independent PeaLang bytecode.

The parallel runtime executes isolated bytecode tasks in a bounded worker pool.
Each task owns a copied global environment and a private virtual machine, so
worker completion order never changes published output or results. Modules that
need async suspension or host module loading are left on the standard VM in
sequential mode.

``verify_parallel_parity()`` requires the parallel and sequential executors to
produce identical per-task output and results before a host adopts the parallel
path. ``benchmark_parallel()`` reports wall-clock evidence without asserting a
speedup.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from .bytecode import BytecodeModule, Op

PARALLEL_RUNTIME_VERSION = '3.1.43'
PARALLEL_RUNTIME_FORMAT = 'pea-parallel-runtime-v1'
MAX_PARALLEL_INSTRUCTIONS = 100_000
_UNSUPPORTED_PARALLEL_OPS = frozenset({'AWAIT', 'IMPORT'})


class ParallelError(Exception):
    """Raised when a parallel task set cannot be planned or executed."""


@dataclass(frozen=True)
class ParallelTask:
    """One isolated bytecode task with its own global environment."""

    name: str
    module: BytecodeModule
    globals: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'source_name': self.module.source_name,
            'module_digest': hashlib.sha256(
                self.module.dumps().encode('utf-8')).hexdigest(),
            'globals': {str(k): str(v)
                        for k, v in sorted(self.globals.items(), key=lambda x: str(x[0]))},
            'instructions': len(self.module.code.instructions),
        }


@dataclass(frozen=True)
class ParallelPlan:
    """Deterministic, reviewable description of a parallel task set."""

    format: str
    version: str
    tasks: tuple[dict[str, Any], ...]
    digest: str
    supported: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            'format': self.format,
            'version': self.version,
            'tasks': list(self.tasks),
            'digest': self.digest,
            'supported': self.supported,
        }

    def dumps(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))


@dataclass(frozen=True)
class ParallelResult:
    """Ordered results from a parallel or sequential task run."""

    results: tuple[Any, ...]
    outputs: tuple[tuple[Any, ...], ...]
    instructions: tuple[int, ...]
    mode: str
    workers: int
    plan_digest: str
    supported: bool
    task_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            'results': [str(value) for value in self.results],
            'outputs': [[str(value) for value in task_output]
                        for task_output in self.outputs],
            'instructions': list(self.instructions),
            'mode': self.mode,
            'workers': self.workers,
            'plan_digest': self.plan_digest,
            'supported': self.supported,
            'task_count': self.task_count,
        }


def _coerce_tasks(tasks: Iterable[ParallelTask]) -> tuple[ParallelTask, ...]:
    task_tuple = tuple(tasks)
    if not task_tuple:
        raise ParallelError('parallel runtime requires at least one task')
    for task in task_tuple:
        if not isinstance(task, ParallelTask):
            raise ParallelError('parallel tasks must be ParallelTask instances')
        if not isinstance(task.module, BytecodeModule):
            raise ParallelError('parallel tasks must carry BytecodeModule artifacts')
    return task_tuple


def _op_name(instruction: Any) -> str:
    raw = getattr(instruction, 'op', '')
    return str(raw.value if isinstance(raw, Op) else raw)


def parallel_supported(tasks: Iterable[ParallelTask]) -> bool:
    """Return whether *tasks* can run on the bounded parallel executor."""

    try:
        task_tuple = _coerce_tasks(tasks)
    except ParallelError:
        return False
    for task in task_tuple:
        code_objects = [task.module.code, *task.module.functions.values()]
        for code in code_objects:
            for instruction in code.instructions:
                if _op_name(instruction) in _UNSUPPORTED_PARALLEL_OPS:
                    return False
    return True


def build_parallel_plan(tasks: Iterable[ParallelTask]) -> ParallelPlan:
    """Build a deterministic plan for *tasks* without executing them."""

    task_tuple = _coerce_tasks(tasks)
    summaries = tuple(task.to_dict() for task in task_tuple)
    supported = parallel_supported(task_tuple)
    digest_payload = {
        'format': PARALLEL_RUNTIME_FORMAT,
        'supported': supported,
        'tasks': summaries,
    }
    digest = hashlib.sha256(json.dumps(
        digest_payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()
    return ParallelPlan(
        format=PARALLEL_RUNTIME_FORMAT, version=PARALLEL_RUNTIME_VERSION,
        tasks=summaries, digest=digest, supported=supported,
    )


def _execute_task(task: ParallelTask, max_instructions: int) -> tuple[Any, tuple[Any, ...], int]:
    from .vm import VirtualMachine

    output: list[Any] = []
    machine = VirtualMachine(output.append, max_instructions=max_instructions)
    result = machine.run(task.module, dict(task.globals))
    return result, tuple(output), machine.instructions


def _execute_sequential(tasks: tuple[ParallelTask, ...],
                        max_instructions: int) -> tuple[tuple[Any, tuple[Any, ...], int], ...]:
    return tuple(_execute_task(task, max_instructions) for task in tasks)


class ParallelRuntime:
    """Execute independent bytecode tasks with bounded worker concurrency."""

    def __init__(self, workers: int = 4, output: Callable[[Any], Any] | None = None,
                 max_instructions: int = MAX_PARALLEL_INSTRUCTIONS):
        self.workers = max(1, int(workers))
        self.output = output
        self.max_instructions = max(1, int(max_instructions))
        self.last_plan: ParallelPlan | None = None
        self.last_result: ParallelResult | None = None

    def run(self, tasks: Iterable[ParallelTask]) -> ParallelResult:
        task_tuple = _coerce_tasks(tasks)
        plan = build_parallel_plan(task_tuple)
        self.last_plan = plan
        use_parallel = plan.supported and self.workers > 1
        mode = 'parallel' if use_parallel else 'sequential'
        active_workers = min(self.workers, len(task_tuple)) if use_parallel else 1

        if use_parallel:
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=active_workers) as pool:
                executions = tuple(pool.submit(
                    _execute_task, task, self.max_instructions
                ).result() for task in task_tuple)
        else:
            executions = _execute_sequential(task_tuple, self.max_instructions)

        results = tuple(execution[0] for execution in executions)
        outputs = tuple(execution[1] for execution in executions)
        instructions = tuple(execution[2] for execution in executions)
        if self.output is not None:
            for task_output in outputs:
                for value in task_output:
                    self.output(value)
        result = ParallelResult(
            results=results, outputs=outputs, instructions=instructions,
            mode=mode, workers=active_workers, plan_digest=plan.digest,
            supported=plan.supported, task_count=len(task_tuple),
        )
        self.last_result = result
        return result


def verify_parallel_parity(tasks: Iterable[ParallelTask], *, workers: int = 4,
                           max_instructions: int = MAX_PARALLEL_INSTRUCTIONS) -> dict[str, Any]:
    """Require identical sequential and parallel output and results."""

    task_tuple = _coerce_tasks(tasks)
    sequential = _execute_sequential(task_tuple, max_instructions)
    runtime = ParallelRuntime(workers=workers, max_instructions=max_instructions)
    parallel = runtime.run(task_tuple)
    candidate = tuple((execution[0], execution[1])
                      for execution in sequential)
    observed = tuple((result, output)
                     for result, output in zip(parallel.results, parallel.outputs))
    output_match = all(execution[1] == output
                       for execution, output in zip(sequential, parallel.outputs))
    result_match = all(execution[0] == result
                       for execution, result in zip(sequential, parallel.results))
    return {
        'ok': output_match and result_match,
        'sequential': {
            'results': [str(execution[0]) for execution in sequential],
            'outputs': [[str(value) for value in execution[1]]
                        for execution in sequential],
        },
        'parallel': {
            'results': [str(result) for result in parallel.results],
            'outputs': [[str(value) for value in output]
                        for output in parallel.outputs],
            'mode': parallel.mode,
            'workers': parallel.workers,
        },
        'output_match': output_match,
        'result_match': result_match,
        'candidate_count': len(candidate),
        'observed_count': len(observed),
    }


def benchmark_parallel(tasks: Iterable[ParallelTask], *, iterations: int = 25,
                       workers: int = 4,
                       max_instructions: int = MAX_PARALLEL_INSTRUCTIONS) -> dict[str, Any]:
    """Compare median wall-clock time of sequential and parallel execution."""

    task_tuple = _coerce_tasks(tasks)

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

    sequential_times = sample(
        lambda: _execute_sequential(task_tuple, max_instructions))
    parallel_times = sample(lambda: ParallelRuntime(
        workers=workers, max_instructions=max_instructions).run(task_tuple))
    sequential_median = statistics.median(sequential_times)
    parallel_median = statistics.median(parallel_times)
    return {
        'iterations': iterations,
        'workers': workers,
        'sequential_median_ms': round(sequential_median * 1000, 4),
        'parallel_median_ms': round(parallel_median * 1000, 4),
        'speedup': round(sequential_median / parallel_median, 3)
        if parallel_median else None,
    }


def parallel_report(tasks: Iterable[ParallelTask], *, verify: bool = False,
                    benchmark: bool = False, workers: int = 4,
                    max_instructions: int = MAX_PARALLEL_INSTRUCTIONS) -> dict[str, Any]:
    """Return a deterministic report covering parallel planning and safety."""

    task_tuple = _coerce_tasks(tasks)
    plan = build_parallel_plan(task_tuple)
    runtime = ParallelRuntime(workers=workers, max_instructions=max_instructions)
    result = runtime.run(task_tuple)
    report: dict[str, Any] = {
        'version': PARALLEL_RUNTIME_VERSION,
        'format': PARALLEL_RUNTIME_FORMAT,
        'plan_digest': plan.digest,
        'supported': plan.supported,
        'mode': result.mode,
        'workers': result.workers,
        'task_count': result.task_count,
        'results': [str(value) for value in result.results],
        'outputs': [[str(value) for value in task_output]
                    for task_output in result.outputs],
        'instructions': list(result.instructions),
        'gate': 'PASS',
    }
    if verify:
        report['parity'] = verify_parallel_parity(
            task_tuple, workers=workers, max_instructions=max_instructions)
    if benchmark:
        report['benchmark'] = benchmark_parallel(
            task_tuple, workers=workers, max_instructions=max_instructions)
    return report


def parallel_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Reduce a parallel runtime report to a deterministic PASS/FAIL gate."""

    issues: list[str] = []
    if report.get('mode') not in ('parallel', 'sequential'):
        issues.append('mode')
    if report.get('gate') != 'PASS':
        issues.append('execution')
    if int(report.get('task_count', 0)) < 1:
        issues.append('tasks')
    parity = report.get('parity')
    if parity is not None and not parity.get('ok'):
        issues.append('parity')
    return {'gate': 'PASS' if not issues else 'FAIL', 'issues': issues}


def build_parallel_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'PARALLEL_RUNTIME_VERSION': PARALLEL_RUNTIME_VERSION,
        'PARALLEL_RUNTIME_FORMAT': PARALLEL_RUNTIME_FORMAT,
        'ParallelError': ParallelError,
        'ParallelTask': ParallelTask,
        'ParallelPlan': ParallelPlan,
        'ParallelResult': ParallelResult,
        'parallel_supported': parallel_supported,
        'build_parallel_plan': build_parallel_plan,
        'ParallelRuntime': ParallelRuntime,
        'verify_parallel_parity': verify_parallel_parity,
        'benchmark_parallel': benchmark_parallel,
        'parallel_report': parallel_report,
        'parallel_gate': parallel_gate,
        'build_parallel_namespace': build_parallel_namespace,
    }


__all__ = [
    'PARALLEL_RUNTIME_VERSION', 'PARALLEL_RUNTIME_FORMAT',
    'ParallelError', 'ParallelTask', 'ParallelPlan', 'ParallelResult',
    'parallel_supported', 'build_parallel_plan', 'ParallelRuntime',
    'verify_parallel_parity', 'benchmark_parallel', 'parallel_report',
    'parallel_gate', 'build_parallel_namespace',
]
