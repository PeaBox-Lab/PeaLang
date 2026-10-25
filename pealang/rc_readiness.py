

from dataclasses import dataclass,asdict
from enum import Enum
import hashlib,json
class Severity(str,Enum):BLOCKER='blocker';HIGH='high';MEDIUM='medium';LOW='low'
@dataclass(frozen=True)
class Defect:defect_id:str;severity:Severity;status:str;summary:str=''
@dataclass(frozen=True)
class Waiver:waiver_id:str;gate:str;reason:str;approved_by:str;expires_version:str
@dataclass(frozen=True)
class Evidence:gate:str;status:str;digest:str='';detail:str=''
class RCReadiness:
 REQUIRED=('regression','api_compatibility','security','performance','supply_chain','upgrade','documentation','cross_platform')
 def __init__(self,version,feature_freeze=True):self.version=version;self.feature_freeze=feature_freeze;self.evidence={};self.defects=[];self.waivers=[]
 def add_evidence(self,gate,status,payload=None):self.evidence[gate]=Evidence(gate,status.upper(),hashlib.sha256(json.dumps(payload or {},sort_keys=True).encode()).hexdigest());return self
 def add_defect(self,d):self.defects.append(d);return self
 def add_waiver(self,w):
  if not w.reason.strip() or not w.approved_by.strip():raise ValueError('waiver requires reason and approver')
  self.waivers.append(w);return self
 def evaluate(self):
  checks={'feature_freeze':bool(self.feature_freeze)};details={}
  for g in self.REQUIRED:
   e=self.evidence.get(g);waived=any(w.gate==g and w.expires_version==self.version for w in self.waivers);checks[g]=bool(e and e.status=='PASS') or waived;details[g]={'status':e.status if e else 'MISSING','waived':waived}
  critical=[d.defect_id for d in self.defects if d.severity in (Severity.BLOCKER,Severity.HIGH) and d.status.lower() not in ('closed','fixed','resolved')];checks['critical_defects']=not critical
  report={'schema':1,'version':self.version,'decision':'GO' if all(checks.values()) else 'NO-GO','checks':checks,'details':details,'open_critical_defects':critical,'waivers':[asdict(w) for w in self.waivers]};report['report_digest']=hashlib.sha256(json.dumps(report,sort_keys=True,separators=(',',':')).encode()).hexdigest();return report
def documentation_gate(paths,required):
 missing=sorted(set(required)-set(paths));return {'status':'PASS' if not missing else 'FAIL','missing':missing}
def cross_platform_gate(results,required=('linux','windows','macos')):
 missing=[x for x in required if results.get(x)!='PASS'];return {'status':'PASS' if not missing else 'FAIL','missing_or_failed':missing}


