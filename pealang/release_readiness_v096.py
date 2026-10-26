


"""PeaLang 0.96 Release Readiness Closure."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from hashlib import sha256
import json
from typing import Any,Iterable,Mapping

def digest(v:Any)->str: return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
@dataclass(frozen=True)
class ReadinessEvidence:
 area:str; source:str; sha256:str; verified:bool
 def passed(self): return self.verified and bool(self.source.strip()) and len(self.sha256)==64
@dataclass(frozen=True)
class ResidualRisk:
 id:str; severity:str; mitigation:str; owner:str; accepted:bool=False
 def releasable(self): return self.severity.lower() not in {"critical","high"} and bool(self.mitigation.strip()) and bool(self.owner.strip())
@dataclass(frozen=True)
class ReadinessCheck:
 name:str; passed:bool; evidence:str

def documentation_support_gate(checks:Iterable[ReadinessCheck], required=("user-guide","basics","api-docs","upgrade-guide","support-policy","release-notes")):
 checks=list(checks); good={x.name for x in checks if x.passed and x.evidence.strip()}; missing=sorted(set(required)-good); failed=[asdict(x) for x in checks if not x.passed or not x.evidence.strip()]
 return {"passed":not missing and not failed,"missing":missing,"failed":failed}
def package_ops_gate(checks:Iterable[ReadinessCheck], required=("wheel","sdist","container","offline-install","rollback","backup-restore","monitoring")):
 checks=list(checks); good={x.name for x in checks if x.passed and x.evidence.strip()}; missing=sorted(set(required)-good)
 return {"passed":not missing,"missing":missing}
def evidence_gate(items:Iterable[ReadinessEvidence], required=("rc95","security","license","cross-platform","reproducibility","operations")):
 items=list(items); good={x.area for x in items if x.passed()}; missing=sorted(set(required)-good); rejected=[asdict(x) for x in items if not x.passed()]
 return {"passed":not missing and not rejected,"missing":missing,"rejected":rejected}
def residual_risk_gate(risks:Iterable[ResidualRisk]):
 risks=list(risks); blocking=[asdict(x) for x in risks if not x.releasable()]; return {"passed":not blocking,"blocking":blocking,"risk_count":len(risks)}
def readiness_dossier(*,evidence,documentation,package_ops,risks,rc95,approvals:Mapping[str,bool]):
 sections={"evidence":evidence,"documentation":documentation,"package_ops":package_ops,"risks":risks,"rc95":rc95}; approvals=dict(approvals)
 passed=all(x.get("passed") is True for x in sections.values()) and {"release-owner","security-owner","operations-owner"}.issubset({k for k,v in approvals.items() if v})
 out={"version":"0.96.0-rc1","decision":"READY-FOR-1.0" if passed else "NO-GO","passed":passed,"sections":sections,"approvals":approvals}; out["dossier_digest"]=digest(out); return out



