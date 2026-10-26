
"""PeaLang 0.99 Final 1.0 Release Gate."""
from dataclasses import dataclass,asdict
from hashlib import sha256
import json
def digest(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
@dataclass(frozen=True)
class ClosureItem:
 id:str; category:str; severity:str; status:str; waiver_expires:str|None=None
 def blocks(self):
  open_=self.status.lower() not in {"closed","resolved"}
  severe=self.severity.lower() in {"critical","high"}
  bad_waiver=self.status.lower()=="waived" and not self.waiver_expires
  return (open_ and severe) or bad_waiver
@dataclass(frozen=True)
class FinalDocument:
 name:str; present:bool; reviewed:bool; sha256:str
 def valid(self): return self.present and self.reviewed and len(self.sha256)==64
@dataclass(frozen=True)
class FinalArtifact:
 name:str; version:str; sha256:str; signature_verified:bool; provenance_verified:bool; sbom_verified:bool
 def valid(self): return self.version=="1.0.0" and len(self.sha256)==64 and self.signature_verified and self.provenance_verified and self.sbom_verified
def closure_gate(items):
 items=list(items); blocking=[asdict(x) for x in items if x.blocks()]; return {"passed":not blocking,"blocking":blocking,"items":len(items)}
def documentation_gate(items,required=("README","user-guide","basics","api-reference","upgrade-guide","support-policy","security","release-notes","changelog")):
 items=list(items); good={x.name for x in items if x.valid()}; missing=sorted(set(required)-good); invalid=[asdict(x) for x in items if not x.valid()]; return {"passed":not missing and not invalid,"missing":missing,"invalid":invalid}
def final_artifact_gate(items,required=("wheel","sdist","container")):
 items=list(items); good={x.name for x in items if x.valid()}; missing=sorted(set(required)-good); invalid=[asdict(x) for x in items if not x.valid()]; return {"passed":not missing and not invalid,"missing":missing,"invalid":invalid}
def final_go_no_go(*,rehearsal98,closure,documentation,artifacts,security,compatibility,operations,approvals):
 sections={"rehearsal98":rehearsal98,"closure":closure,"documentation":documentation,"artifacts":artifacts,"security":security,"compatibility":compatibility,"operations":operations}; approvals=dict(approvals); owners={"release-owner","security-owner","operations-owner"}; passed=all(x.get("passed") is True for x in sections.values()) and owners.issubset({k for k,v in approvals.items() if v}); out={"version":"0.99.0-rc1","target":"1.0.0","passed":passed,"decision":"GO-1.0" if passed else "NO-GO","sections":sections,"approvals":approvals};out["dossier_digest"]=digest(out);return out

