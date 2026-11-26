"""Phase 78: versioned 4.0 performance gates for PeaLang bytecode.

The gate combines timing evidence from a representative bytecode module with
the deterministic parity, conformance, and frozen-core checks that protect a
release. Timing values are evidence only; the gate result is derived from
explicit budgets and boolean release checks.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from .bytecode import BytecodeModule

PERFORMANCE_GATE_VERSION = '4.0.0'
PERFORMANCE_GATE_FORMAT = 'pea-performance-gates-v4'


class PerformanceGateError(Exception):
    """Raised when a performance gate cannot be assembled."""


@dataclass(frozen=True)
class GateBudget:
    """Explicit, reviewable limits for the 4.0 gate."""

    max_mean_ms: float = 1000.0
    max_p95_ms: float = 2000.0
    max_peak_memory_mb: float = 64.0
    require_parity: bool = True
    require_conformance: bool = True
    require_freeze: bool = True


@dataclass(frozen=True)
class GateEvidence:
    """Timing and release evidence collected for one bytecode module."""

    iterations: int
    mean_ms: float
    p95_ms: float
    peak_memory_mb: float
    parallel_parity_ok: bool
    profiler_parity_ok: bool
    conformance_ok: bool
    freeze_ok: bool
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _module_digest(module: BytecodeModule) -> str:
    return hashlib.sha256(module.dumps().encode('utf-8')).hexdigest()


def collect_gate_evidence(module: BytecodeModule, *, iterations: int = 5,
                          workers: int = 4,
                          max_instructions: int = 100_000) -> GateEvidence:
    """Collect timing, parity, conformance, and freeze evidence for *module*."""

    from .conformance_suite import conformance_report_v2
    from .core_freeze import core_freeze_report
    from .parallel_runtime import (ParallelTask, verify_parallel_parity)
    from .performance_hardening import PerformanceProbe
    from .runtime_profiler import verify_profile_parity
    from .vm import VirtualMachine

    if not isinstance(module, BytecodeModule):
        raise PerformanceGateError('performance gate requires a BytecodeModule')

    probe = PerformanceProbe(warmup=0, iterations=max(1, int(iterations)))
    sample = probe.run(lambda: VirtualMachine(
        lambda _value: None, max_instructions=max_instructions).run(module))

    tasks = (
        ParallelTask('gate-0', module, {}),
        ParallelTask('gate-1', module, {}),
    )
    parallel_parity_ok = verify_parallel_parity(
        tasks, workers=workers, max_instructions=max_instructions)['ok']
    profiler_parity_ok = verify_profile_parity(
        module, max_instructions=max_instructions)['ok']
    conformance = conformance_report_v2()
    conformance_ok = bool(conformance.get('suite', {}).get('ok')) \
        and int(conformance.get('suite', {}).get('failed', 0)) == 0
    freeze_ok = core_freeze_report().get('freeze', {}).get('gate') == 'PASS'

    digest_payload = {
        'format': PERFORMANCE_GATE_FORMAT,
        'module': _module_digest(module),
        'iterations': max(1, int(iterations)),
        'parallel_parity_ok': parallel_parity_ok,
        'profiler_parity_ok': profiler_parity_ok,
        'conformance_ok': conformance_ok,
        'freeze_ok': freeze_ok,
    }
    digest = hashlib.sha256(json.dumps(
        digest_payload, sort_keys=True, separators=(',', ':'),
    ).encode('utf-8')).hexdigest()
    return GateEvidence(
        iterations=max(1, int(iterations)),
        mean_ms=round(sample.mean_ms, 4),
        p95_ms=round(sample.p95_ms, 4),
        peak_memory_mb=round(sample.peak_memory_mb, 4),
        parallel_parity_ok=parallel_parity_ok,
        profiler_parity_ok=profiler_parity_ok,
        conformance_ok=conformance_ok,
        freeze_ok=freeze_ok,
        digest=digest,
    )


def _checks(evidence: GateEvidence, budget: GateBudget) -> dict[str, bool]:
    return {
        'mean_ms': evidence.mean_ms <= budget.max_mean_ms,
        'p95_ms': evidence.p95_ms <= budget.max_p95_ms,
        'peak_memory_mb': evidence.peak_memory_mb <= budget.max_peak_memory_mb,
        'parallel_parity': not budget.require_parity or evidence.parallel_parity_ok,
        'profiler_parity': not budget.require_parity or evidence.profiler_parity_ok,
        'conformance': not budget.require_conformance or evidence.conformance_ok,
        'freeze': not budget.require_freeze or evidence.freeze_ok,
    }


def performance_gate_report(module: BytecodeModule, *, budget: GateBudget | None = None,
                            iterations: int = 5, workers: int = 4,
                            max_instructions: int = 100_000) -> dict[str, Any]:
    """Build a deterministic 4.0 performance gate report for *module*."""

    budget = budget or GateBudget()
    evidence = collect_gate_evidence(
        module, iterations=iterations, workers=workers,
        max_instructions=max_instructions,
    )
    checks = _checks(evidence, budget)
    issues = sorted(name for name, ok in checks.items() if not ok)
    return {
        'version': PERFORMANCE_GATE_VERSION,
        'format': PERFORMANCE_GATE_FORMAT,
        'module_digest': _module_digest(module),
        'evidence_digest': evidence.digest,
        'budget': asdict(budget),
        'evidence': evidence.to_dict(),
        'checks': checks,
        'issues': issues,
        'gate': 'PASS' if not issues else 'FAIL',
    }


def performance_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute a deterministic PASS/FAIL decision from a gate report."""

    try:
        budget = GateBudget(**report.get('budget', {}))
        evidence = GateEvidence(**report.get('evidence', {}))
    except (TypeError, ValueError) as exc:
        raise PerformanceGateError('malformed performance gate report') from exc
    checks = _checks(evidence, budget)
    issues = sorted(name for name, ok in checks.items() if not ok)
    if report.get('gate') == 'FAIL' and not issues:
        issues.append('report')
    return {
        'gate': 'PASS' if not issues else 'FAIL',
        'issues': issues,
        'checks': checks,
    }


def build_performance_gates_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'PERFORMANCE_GATE_VERSION': PERFORMANCE_GATE_VERSION,
        'PERFORMANCE_GATE_FORMAT': PERFORMANCE_GATE_FORMAT,
        'PerformanceGateError': PerformanceGateError,
        'GateBudget': GateBudget,
        'GateEvidence': GateEvidence,
        'collect_gate_evidence': collect_gate_evidence,
        'performance_gate_report': performance_gate_report,
        'performance_gate': performance_gate,
        'build_performance_gates_namespace': build_performance_gates_namespace,
    }


__all__ = [
    'PERFORMANCE_GATE_VERSION', 'PERFORMANCE_GATE_FORMAT',
    'PerformanceGateError', 'GateBudget', 'GateEvidence',
    'collect_gate_evidence', 'performance_gate_report', 'performance_gate',
    'build_performance_gates_namespace',
]
