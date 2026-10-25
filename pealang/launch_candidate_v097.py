
"""PeaLang 0.97 1.0 Launch Candidate validation."""
from dataclasses import dataclass,asdict
from hashlib import sha256
import json
def digest(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
@dataclass(frozen=True)
class Change:
 id:str; kind:str; approved:bool
 def allowed(self): return self.approved and self.kind in {"blocker-fix","security-fix","release-metadata"}
@dataclass(frozen=True)
class Artifact:
 name:str; sha256:str; signature_verified:bool; provenance_verified:bool
 def passed(self): return len(self.sha256)==64 and self.signature_verified and self.provenance_verified
@dataclass(frozen=True)
class Playbook:
 name:str; owner:str; tested:bool; evidence:str
 def passed(self): return bool(self.owner.strip()) and self.tested and bool(self.evidence.strip())
@dataclass(frozen=True)
class RollbackCriterion:
 name:str; threshold:float; observed:float
 def breached(self): return self.observed>self.threshold
def freeze_gate(xs):
 xs=list(xs);bad=[asdict(x) for x in xs if not x.allowed()];return {"passed":not bad,"rejected":bad}
def artifact_gate(xs,required=("wheel","sdist","container")):
 xs=list(xs);by={x.name:x for x in xs};missing=sorted(set(required)-set(by));failed=[asdict(x) for x in xs if not x.passed()];return {"passed":not missing and not failed,"missing":missing,"failed":failed}
def playbook_gate(xs,required=("migration","support","incident","rollback")):
 xs=list(xs);good={x.name for x in xs if x.passed()};missing=sorted(set(required)-good);return {"passed":not missing,"missing":missing}
def rollback_gate(xs):
 xs=list(xs);bad=[asdict(x) for x in xs if x.breached()];return {"passed":bool(xs) and not bad,"breached":bad}
def launch_gate(*,freeze,readiness96,artifacts,playbooks,rollback,approvals):
 sections={"freeze":freeze,"readiness96":readiness96,"artifacts":artifacts,"playbooks":playbooks,"rollback":rollback};req={"release-owner","security-owner","operations-owner"};approvals=dict(approvals);passed=all(x.get("passed") is True for x in sections.values()) and req.issubset({k for k,v in approvals.items() if v});out={"version":"0.97.0-rc1","passed":passed,"decision":"LAUNCH-CANDIDATE-PASS" if passed else "NO-GO","sections":sections,"approvals":approvals};out["digest"]=digest(out);return out

