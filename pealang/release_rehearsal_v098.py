"""PeaLang 0.98 Release Dress Rehearsal evidence gates."""
from dataclasses import dataclass,asdict
from hashlib import sha256
import json
def digest(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
@dataclass(frozen=True)
class RehearsalStep:
 name:str; passed:bool; evidence_sha256:str; source:str
 def valid(self): return self.passed and len(self.evidence_sha256)==64 and bool(self.source.strip())
@dataclass(frozen=True)
class InstallDrill:
 mode:str; platform:str; passed:bool; integrity_before:str; integrity_after:str
 def valid(self): return self.passed and len(self.integrity_before)==64 and self.integrity_before==self.integrity_after
@dataclass(frozen=True)
class OperationalDrill:
 name:str; owner:str; exercised:bool; evidence:str
 def valid(self): return bool(self.owner.strip()) and self.exercised and bool(self.evidence.strip())
def signed_staging_gate(steps,required=("build","sbom","provenance","sign","publish-staging","verify-staging")):
 steps=list(steps); good={x.name for x in steps if x.valid()}; missing=sorted(set(required)-good); bad=[asdict(x) for x in steps if not x.valid()]; return {"passed":not missing and not bad,"missing":missing,"failed":bad}
def install_upgrade_rollback_gate(drills,required_modes=("clean-install","upgrade","rollback")):
 drills=list(drills); good={x.mode for x in drills if x.valid()}; missing=sorted(set(required_modes)-good); bad=[asdict(x) for x in drills if not x.valid()]; return {"passed":not missing and not bad,"missing":missing,"failed":bad}
def operations_gate(drills,required=("support","incident","rollback")):
 drills=list(drills); good={x.name for x in drills if x.valid()}; missing=sorted(set(required)-good); return {"passed":not missing,"missing":missing}
def rehearsal_gate(*,launch97,staging,install,operations,approvals):
 sections={"launch97":launch97,"staging":staging,"install":install,"operations":operations}; approvals=dict(approvals); required={"release-owner","security-owner","operations-owner"}; passed=all(x.get("passed") is True for x in sections.values()) and required.issubset({k for k,v in approvals.items() if v}); out={"version":"0.98.0-rc1","passed":passed,"decision":"REHEARSAL-PASS" if passed else "NO-GO","sections":sections,"approvals":approvals};out["digest"]=digest(out);return out
