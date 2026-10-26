


"""PeaLang 0.94 Release Candidate Validation IV: release engineering closure."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from hashlib import sha256
import json
from typing import Any,Iterable,Mapping

def digest(v:Any)->str:
 return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True)
class InstallProbe:
 os:str; python:str; artifact:str; fresh_install:bool; upgrade:bool; rollback:bool; offline:bool
 def passed(self)->bool: return self.fresh_install and self.upgrade and self.rollback and self.offline

@dataclass(frozen=True)
class ArtifactBuild:
 kind:str; digest_sha256:str; sbom_sha256:str; provenance_sha256:str

@dataclass(frozen=True)
class ReviewClosure:
 dependency_audit:bool; license_review:bool; security_review:bool; critical_findings:int=0; high_findings:int=0
 def passed(self)->bool:
  return self.dependency_audit and self.license_review and self.security_review and self.critical_findings==0 and self.high_findings==0

@dataclass(frozen=True)
class RunbookProbe:
 name:str; tested:bool; owner:str; recovery_minutes:float; target_minutes:float=30.0
 def passed(self)->bool: return self.tested and bool(self.owner.strip()) and 0<=self.recovery_minutes<=self.target_minutes

def install_matrix(probes:Iterable[InstallProbe], required_os=("windows","linux","macos"), required_python=("3.10","3.11","3.12","3.13"))->dict[str,Any]:
 probes=list(probes); cells={(p.os.lower(),p.python) for p in probes if p.passed()}
 required={(o,v) for o in required_os for v in required_python}; missing=sorted(required-cells)
 return {"passed":not missing,"required_cells":len(required),"passing_cells":len(required)-len(missing),"missing":missing}

def reproducible_artifacts(build_sets:Iterable[Iterable[ArtifactBuild]], required=("wheel","sdist","container"))->dict[str,Any]:
 sets=[list(x) for x in build_sets]; drift={}
 for kind in required:
  vals=[next((x for x in run if x.kind==kind),None) for run in sets]
  sig={(x.digest_sha256,x.sbom_sha256,x.provenance_sha256) for x in vals if x}
  if len(vals)<2 or any(x is None for x in vals) or len(sig)!=1: drift[kind]=len(sig)
 return {"passed":len(sets)>=2 and not drift,"build_sets":len(sets),"drift":drift}

def review_gate(review:ReviewClosure)->dict[str,Any]: return {"passed":review.passed(),**asdict(review)}

def runbook_gate(probes:Iterable[RunbookProbe], minimum=4)->dict[str,Any]:
 probes=list(probes); failed=[asdict(p) for p in probes if not p.passed()]
 return {"passed":len(probes)>=minimum and not failed,"runbooks":len(probes),"failed":failed}

def v1_evidence_gate(*,install,reproducibility,reviews,runbooks,rc93,blockers=())->dict[str,Any]:
 sections={"install":install,"reproducibility":reproducibility,"reviews":reviews,"runbooks":runbooks,"rc93":rc93}; blockers=list(blockers)
 result={"version":"0.94.0-rc1","passed":all(x.get("passed") is True for x in sections.values()) and not blockers,"sections":sections,"blockers":blockers}
 result["digest"]=digest(result); return result



