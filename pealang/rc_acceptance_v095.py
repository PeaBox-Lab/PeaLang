


"""PeaLang 0.95 Final RC Acceptance gates."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from hashlib import sha256
import json
from typing import Any,Iterable,Mapping

def digest(v:Any)->str:
 return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True)
class EvidenceItem:
 gate:str; source:str; sha256:str; verified:bool; external:bool=True
 def passed(self)->bool: return self.verified and len(self.sha256)==64 and bool(self.source.strip())

@dataclass(frozen=True)
class Blocker:
 id:str; severity:str; status:str; waiver_expires:str|None=None
 def open_release_blocker(self)->bool:
  return self.severity.lower() in {"critical","high"} and self.status.lower() not in {"closed","resolved"}

@dataclass(frozen=True)
class SignedArtifact:
 name:str; sha256:str; signature_verified:bool; provenance_verified:bool
 def passed(self)->bool: return len(self.sha256)==64 and self.signature_verified and self.provenance_verified

@dataclass(frozen=True)
class DryRunStep:
 name:str; passed:bool; rollback_tested:bool=False

def evidence_ingestion(items:Iterable[EvidenceItem], required=("install-matrix","security-review","license-review","runbooks","reproducibility"))->dict[str,Any]:
 items=list(items); good={x.gate for x in items if x.passed()}; missing=sorted(set(required)-good); bad=[asdict(x) for x in items if not x.passed()]
 return {"passed":not missing and not bad,"accepted":len(items)-len(bad),"missing":missing,"rejected":bad}

def blocker_burndown(items:Iterable[Blocker])->dict[str,Any]:
 items=list(items); open_=[asdict(x) for x in items if x.open_release_blocker()]; stale=[asdict(x) for x in items if x.status.lower()=="waived" and not x.waiver_expires]
 return {"passed":not open_ and not stale,"open_release_blockers":open_,"invalid_waivers":stale}

def artifact_signing(items:Iterable[SignedArtifact], required=("wheel","sdist","container"))->dict[str,Any]:
 items=list(items); by={x.name:x for x in items}; missing=[n for n in required if n not in by]; failed=[asdict(x) for x in items if not x.passed()]
 return {"passed":not missing and not failed,"missing":missing,"failed":failed}

def release_dry_run(steps:Iterable[DryRunStep], required=("build","test","sign","publish-staging","install-staging","rollback"))->dict[str,Any]:
 steps=list(steps); by={x.name:x for x in steps}; missing=[n for n in required if n not in by]; failed=[asdict(x) for x in steps if not x.passed]; rollback=by.get("rollback")
 return {"passed":not missing and not failed and bool(rollback and rollback.rollback_tested),"missing":missing,"failed":failed,"rollback_tested":bool(rollback and rollback.rollback_tested)}

def go_no_go(*,evidence,blockers,artifacts,dry_run,rc94,manual_approvals:Mapping[str,bool])->dict[str,Any]:
 sections={"evidence":evidence,"blockers":blockers,"artifacts":artifacts,"dry_run":dry_run,"rc94":rc94}; approvals=dict(manual_approvals)
 passed=all(x.get("passed") is True for x in sections.values()) and bool(approvals) and all(approvals.values())
 out={"version":"0.95.0-rc1","decision":"GO" if passed else "NO-GO","passed":passed,"sections":sections,"manual_approvals":approvals}; out["decision_digest"]=digest(out); return out



