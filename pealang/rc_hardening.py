
"""PeaLang 0.89 release-candidate readiness gates. No new feature family."""
from dataclasses import dataclass,asdict
from enum import Enum
import hashlib,json
class Severity(str,Enum):BLOCKER='blocker';HIGH='high';MEDIUM='medium';LOW='low'
@dataclass(frozen=True)
class Defect:
 defect_id:str;severity:Severity;status:str;summary:str;waiver_id:str|None=None
@dataclass(frozen=True)
class Waiver:
 waiver_id:str;scope:str;owner:str;reason:str;expires_version:str
class DefectRegistry:
 def __init__(self,defects=(),waivers=()):self.defects={x.defect_id:x for x in defects};self.waivers={x.waiver_id:x for x in waivers}
 def unresolved_critical(self):return sorted(x.defect_id for x in self.defects.values() if x.severity in {Severity.BLOCKER,Severity.HIGH} and x.status!='closed' and not (x.waiver_id and x.waiver_id in self.waivers))
 def validate_waivers(self):return sorted(x.defect_id for x in self.defects.values() if x.waiver_id and x.waiver_id not in self.waivers)
@dataclass(frozen=True)
class Evidence:
 name:str;passed:bool;detail:str='';digest:str=''
 @classmethod
 def from_payload(cls,name,passed,payload):
  raw=json.dumps(payload,sort_keys=True,separators=(',',':'),default=str).encode();return cls(name,bool(passed),str(payload),hashlib.sha256(raw).hexdigest())
class RCReadinessGate:
 REQUIRED=('regression','api_compatibility','security','performance','supply_chain','migration','tooling','documentation','cross_platform')
 def evaluate(self,evidence,defects,feature_freeze=True):
  by={x.name:x for x in evidence};checks={'feature_freeze':bool(feature_freeze),'critical_defects':not defects.unresolved_critical(),'waivers':not defects.validate_waivers()}
  for name in self.REQUIRED:checks[name]=bool(name in by and by[name].passed)
  failed=[k for k,v in checks.items() if not v]
  report={'release':'0.89.0rc1','gate':'GO' if not failed else 'NO-GO','checks':checks,'failed':failed,'critical_defects':defects.unresolved_critical(),'evidence':{k:asdict(v) for k,v in sorted(by.items())}}
  report['digest']=hashlib.sha256(json.dumps(report,sort_keys=True,separators=(',',':')).encode()).hexdigest();return report
def documentation_completeness(root):
 from pathlib import Path
 r=Path(root);required=['README.md','CHANGELOG.md','ROADMAP.md','docs/releases/RELEASE_NOTES_0.89.0.md','docs/project/RC_HARDENING_089.md'];missing=[x for x in required if not (r/x).is_file()];return {'passed':not missing,'missing':missing}
def cross_platform_evidence(platforms):
 required={'windows','linux','macos'};actual={str(x).lower() for x in platforms};return {'passed':required<=actual,'missing':sorted(required-actual)}

