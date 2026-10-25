
"""PeaLang 0.91 release-candidate validation I."""
from dataclasses import dataclass,asdict
import hashlib,json
from typing import Mapping

SUPPORTED_PYTHONS=("3.10","3.11","3.12","3.13")
SUPPORTED_PLATFORMS=("windows","linux","macos")

@dataclass(frozen=True)
class SoakEvidence:
 platform:str
 python:str
 tests_passed:int
 tests_failed:int=0
 duration_seconds:float=0.0
 def passed(self):return self.tests_failed==0 and self.tests_passed>0

class CrossPlatformSoak:
 def __init__(self,evidence=()):self.evidence=list(evidence)
 def add(self,item):self.evidence.append(item);return self
 def matrix(self):return {(x.platform.lower(),x.python):x for x in self.evidence}
 def evaluate(self,required_platforms=SUPPORTED_PLATFORMS,required_pythons=SUPPORTED_PYTHONS):
  matrix=self.matrix();missing=[];failed=[]
  for os_name in required_platforms:
   for py in required_pythons:
    item=matrix.get((os_name,py))
    if item is None:missing.append(f"{os_name}/py{py}")
    elif not item.passed():failed.append(f"{os_name}/py{py}")
  return {"passed":not missing and not failed,"missing":missing,"failed":failed,"observed":len(matrix)}

@dataclass(frozen=True)
class UpgradeFixture:
 source_version:str
 target_version:str
 migrated:bool
 rollback_verified:bool
 data_integrity:bool

class UpgradeValidation:
 def evaluate(self,fixtures):
  rows=list(fixtures);bad=[f"{x.source_version}->{x.target_version}" for x in rows if not(x.migrated and x.rollback_verified and x.data_integrity)]
  return {"passed":bool(rows) and not bad,"validated":len(rows),"failed":bad}

class FrozenContractSurveillance:
 def __init__(self,api_digest,diagnostic_codes=(),bytecode_version=None):
  self.api_digest=api_digest;self.diagnostic_codes=tuple(sorted(set(diagnostic_codes)));self.bytecode_version=bytecode_version
 def compare(self,current_api_digest,current_diagnostics=(),current_bytecode_version=None):
  checks={"api":current_api_digest==self.api_digest,"diagnostics":tuple(sorted(set(current_diagnostics)))==self.diagnostic_codes,"bytecode":current_bytecode_version==self.bytecode_version}
  return {"passed":all(checks.values()),"checks":checks}

@dataclass(frozen=True)
class SoakGate:
 security_passed:bool
 performance_passed:bool
 packaging_passed:bool
 offline_install_passed:bool

@dataclass(frozen=True)
class RCBlocker:
 blocker_id:str
 severity:str
 status:str
 waiver_id:str|None=None

class BlockerRegistry:
 def evaluate(self,items):
  blockers=[];invalid_waivers=[]
  for x in items:
   sev=x.severity.lower();status=x.status.lower()
   if sev in {"blocker","critical","high"} and status not in {"closed","waived"}:blockers.append(x.blocker_id)
   if status=="waived" and not x.waiver_id:invalid_waivers.append(x.blocker_id)
  return {"passed":not blockers and not invalid_waivers,"open_blockers":blockers,"invalid_waivers":invalid_waivers}

def rc91_gate(*,cross_platform,upgrades,frozen_contract,soak,blockers):
 checks={"cross_platform":bool(cross_platform.get("passed")),"upgrades":bool(upgrades.get("passed")),"frozen_contract":bool(frozen_contract.get("passed")),"security":soak.security_passed,"performance":soak.performance_passed,"packaging":soak.packaging_passed,"offline_install":soak.offline_install_passed,"blockers":bool(blockers.get("passed"))}
 return {"gate":"GO" if all(checks.values()) else "NO-GO","checks":checks,"failed":[k for k,v in checks.items() if not v]}

def evidence_digest(*evidence):
 normalized=[asdict(x) if hasattr(x,"__dataclass_fields__") else x for x in evidence]
 return hashlib.sha256(json.dumps(normalized,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

