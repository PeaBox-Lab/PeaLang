
"""PeaLang 0.99.2 pre-1.0 evidence inventory and fail-closed gate."""
from pathlib import Path
from dataclasses import dataclass,asdict
from hashlib import sha256
import json
def digest(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
@dataclass(frozen=True)
class Evidence:
 name:str; source:str; sha256:str; verified:bool
 def valid(self): return self.verified and bool(self.source.strip()) and len(self.sha256)==64
REQUIRED=("full-regression","windows-py310","windows-py311","windows-py312","windows-py313","linux-py310","linux-py311","linux-py312","linux-py313","macos-py310","macos-py311","macos-py312","macos-py313","java17","java21","node20","node22","bandit","pip-audit","semgrep","trivy","secret-scan","wheel","sdist","container","sbom","provenance","signatures","clean-install","offline-install","upgrade","rollback")
def evidence_inventory(items):
 items=list(items); good={x.name for x in items if x.valid()}; missing=sorted(set(REQUIRED)-good); invalid=[asdict(x) for x in items if not x.valid()]; return {"passed":not missing and not invalid,"required":len(REQUIRED),"verified":len(good),"missing":missing,"invalid":invalid}
def pre_v1_gate(*,audit_closure,final_gate,evidence,approvals):
 approvals=dict(approvals); sections={"audit_closure":audit_closure,"final_gate":final_gate,"evidence":evidence}; owners={"release-owner","security-owner","operations-owner"}; passed=all(x.get("passed") is True for x in sections.values()) and owners.issubset({k for k,v in approvals.items() if v}); out={"version":"0.99.2","target":"1.0.0","passed":passed,"decision":"READY-FOR-1.0" if passed else "NO-GO","sections":sections,"approvals":approvals};out["digest"]=digest(out);return out
def local_evidence_template(root):
 root=Path(root); return {"version":"0.99.2","policy":"fail-closed","required_evidence":list(REQUIRED),"note":"Populate only with genuine retained CI/scanner/signing/approval evidence."}

