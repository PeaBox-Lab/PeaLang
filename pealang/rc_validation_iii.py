"""PeaLang 0.93 Release Candidate Validation III.

Consolidates extended soak reliability, ecosystem certification, disaster recovery,
and reproducible evidence provenance into deterministic release gates.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


def canonical_digest(value: Any) -> str:
    payload=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return sha256(payload).hexdigest()

@dataclass(frozen=True)
class SoakRun:
    platform: str
    python: str
    duration_minutes: int
    iterations: int
    failures: int=0
    crashes: int=0
    leaks: int=0
    def passed(self, min_minutes: int=120, min_iterations: int=100) -> bool:
        return self.duration_minutes>=min_minutes and self.iterations>=min_iterations and not (self.failures or self.crashes or self.leaks)

@dataclass(frozen=True)
class EcosystemCertification:
    name: str
    version: str
    passed: bool
    evidence_sha256: str

@dataclass(frozen=True)
class RecoveryDrill:
    name: str
    backup_digest: str
    restored_digest: str
    recovery_seconds: float
    max_recovery_seconds: float=300.0
    def passed(self) -> bool:
        return self.backup_digest==self.restored_digest and 0<=self.recovery_seconds<=self.max_recovery_seconds

@dataclass(frozen=True)
class EvidenceRecord:
    name: str
    payload_sha256: str
    builder: str
    source_revision: str
    invocation: str
    def provenance_digest(self) -> str:
        return canonical_digest(asdict(self))


def certify_extended_soak(runs: Iterable[SoakRun], required_platforms=("windows","linux","macos")) -> dict[str,Any]:
    runs=list(runs); present={r.platform.lower() for r in runs}
    missing=sorted(set(required_platforms)-present)
    failed=[asdict(r) for r in runs if not r.passed()]
    return {"passed": bool(runs) and not missing and not failed, "missing_platforms":missing, "failed_runs":failed, "run_count":len(runs)}

def certify_ecosystem(items: Iterable[EcosystemCertification], minimum: int=3) -> dict[str,Any]:
    items=list(items); failed=[asdict(x) for x in items if not x.passed or len(x.evidence_sha256)!=64]
    return {"passed":len(items)>=minimum and not failed,"certified":len(items)-len(failed),"failed":failed}

def certify_recovery(drills: Iterable[RecoveryDrill], minimum: int=2) -> dict[str,Any]:
    drills=list(drills); failed=[asdict(x) for x in drills if not x.passed()]
    return {"passed":len(drills)>=minimum and not failed,"drill_count":len(drills),"failed":failed}

def verify_reproducibility(builds: Iterable[Mapping[str,str]], keys=("api","diagnostics","bytecode","package")) -> dict[str,Any]:
    builds=list(builds)
    drift={k:sorted({b.get(k) for b in builds if b.get(k)}) for k in keys}
    drift={k:v for k,v in drift.items() if len(v)!=1}
    return {"passed":len(builds)>=2 and not drift,"build_count":len(builds),"drift":drift}

def release_candidate_gate(*, soak, ecosystem, recovery, reproducibility, blockers=(), waivers=()) -> dict[str,Any]:
    blocker_list=list(blockers); waiver_list=list(waivers)
    sections={"soak":soak,"ecosystem":ecosystem,"recovery":recovery,"reproducibility":reproducibility}
    passed=all(x.get("passed") is True for x in sections.values()) and not blocker_list
    report={"version":"0.93.0-rc1","passed":passed,"sections":sections,"blockers":blocker_list,"waivers":waiver_list}
    report["evidence_digest"]=canonical_digest(report)
    return report
