"""PeaLang v0.76 release hardening and adversarial governance gates."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from typing import Any,Iterable
import hashlib,json

@dataclass(frozen=True)
class SecurityProbe:
    name:str
    tool:str
    args:tuple[Any,...]=()
    expect_allowed:bool=False
    call_index:int=0

@dataclass(frozen=True)
class ProbeResult:
    name:str
    passed:bool
    observed_allowed:bool
    reason:str

class AdversarialAgentSuite:
    def __init__(self,policy): self.policy=policy
    def run(self,probes:Iterable[SecurityProbe]):
        out=[]
        for probe in probes:
            decision=self.policy.evaluate(probe.tool,probe.call_index)
            observed=bool(decision.allowed and not decision.requires_approval)
            out.append(ProbeResult(probe.name,observed==probe.expect_allowed,observed,decision.reason))
        return out
    @staticmethod
    def summary(results):
        results=list(results);passed=sum(x.passed for x in results)
        return {"total":len(results),"passed":passed,"failed":len(results)-passed,"gate":"PASS" if passed==len(results) else "FAIL"}

class PublicAPIGate:
    """Compare symbol snapshots and reject removals unless explicitly approved."""
    def compare(self,baseline,current,approved_removals=()):
        base=set(baseline);cur=set(current);approved=set(approved_removals)
        removed=sorted(base-cur);unexpected=sorted(set(removed)-approved);added=sorted(cur-base)
        return {"baseline":len(base),"current":len(cur),"added":added,"removed":removed,"approved_removals":sorted(approved & set(removed)),"unexpected_removals":unexpected,"gate":"PASS" if not unexpected else "FAIL"}

@dataclass(frozen=True)
class ReleaseThresholds:
    minimum_tests:int=455
    minimum_security_probe_pass_rate:float=1.0
    maximum_unexpected_api_removals:int=0
    maximum_unexpected_file_removals:int=0

class ReleaseHardeningGate:
    def evaluate(self,test_count,probe_summary,api_report,retention_report,thresholds=ReleaseThresholds()):
        checks={
            "tests":int(test_count)>=thresholds.minimum_tests,
            "security_probes":(probe_summary.get("passed",0)/max(1,probe_summary.get("total",0)))>=thresholds.minimum_security_probe_pass_rate,
            "public_api":len(api_report.get("unexpected_removals",[]))<=thresholds.maximum_unexpected_api_removals,
            "retention":len(retention_report.get("unexpected_missing",[]))<=thresholds.maximum_unexpected_file_removals,
        }
        return {"gate":"PASS" if all(checks.values()) else "FAIL","checks":checks,"thresholds":asdict(thresholds)}

def sha256_manifest(root):
    root=Path(root);rows=[]
    for p in sorted(root.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts:
            rows.append({"path":str(p.relative_to(root)).replace('\\','/'),"size":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    return rows
