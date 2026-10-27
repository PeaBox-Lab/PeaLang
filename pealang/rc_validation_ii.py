"""PeaLang 0.92 release-candidate validation II."""
from dataclasses import dataclass,asdict
import hashlib,json,time

@dataclass(frozen=True)
class TimedEvidence:
 evidence_id:str;kind:str;created_at:float;passed:bool;duration_seconds:float=0.0
class EvidenceFreshness:
 def __init__(self,max_age_seconds=7*24*3600):self.max_age_seconds=float(max_age_seconds)
 def evaluate(self,items,now=None):
  now=time.time() if now is None else now;stale=[];failed=[]
  for x in items:
   if now-x.created_at>self.max_age_seconds:stale.append(x.evidence_id)
   if not x.passed:failed.append(x.evidence_id)
  return {'passed':not stale and not failed and bool(items),'stale':stale,'failed':failed,'count':len(items)}

@dataclass(frozen=True)
class UpgradeDrill:
 source_version:str;target_version:str;upgrade_passed:bool;rollback_passed:bool;reupgrade_passed:bool;integrity_digest_before:str;integrity_digest_after:str
class UpgradeDrillSuite:
 def evaluate(self,drills):
  rows=list(drills);bad=[]
  for x in rows:
   if not(x.upgrade_passed and x.rollback_passed and x.reupgrade_passed and x.integrity_digest_before==x.integrity_digest_after):bad.append(f'{x.source_version}->{x.target_version}')
  return {'passed':bool(rows) and not bad,'drills':len(rows),'failed':bad}

@dataclass(frozen=True)
class CompatibilityObservation:
 build_id:str;api_digest:str;diagnostic_digest:str;bytecode_version:str
class DriftSurveillance:
 def evaluate(self,observations):
  rows=list(observations)
  if not rows:return {'passed':False,'drift':{'missing':['evidence']}}
  fields=('api_digest','diagnostic_digest','bytecode_version');drift={}
  for field in fields:
   values=sorted(set(getattr(x,field) for x in rows))
   if len(values)>1:drift[field]=values
  return {'passed':not drift,'builds':len(rows),'drift':drift}

@dataclass(frozen=True)
class TrendPoint:
 build_id:str;security_failures:int;performance_regression_pct:float;peak_memory_mb:float
class SoakTrendGate:
 def __init__(self,max_performance_regression_pct=10.0,max_memory_growth_pct=15.0):self.max_perf=max_performance_regression_pct;self.max_mem=max_memory_growth_pct
 def evaluate(self,points):
  rows=list(points)
  if not rows:return {'passed':False,'issues':['missing evidence']}
  issues=[]
  if any(x.security_failures for x in rows):issues.append('security_failures')
  if any(x.performance_regression_pct>self.max_perf for x in rows):issues.append('performance_regression')
  if len(rows)>1 and rows[0].peak_memory_mb>0:
   growth=((rows[-1].peak_memory_mb-rows[0].peak_memory_mb)/rows[0].peak_memory_mb)*100
   if growth>self.max_mem:issues.append('memory_growth')
  return {'passed':not issues,'issues':issues,'points':len(rows)}

@dataclass(frozen=True)
class EcosystemCertification:
 integration:str;version:str;passed:bool;required:bool=True
class EcosystemGate:
 def evaluate(self,items):
  rows=list(items);failed=[f'{x.integration}@{x.version}' for x in rows if x.required and not x.passed]
  return {'passed':bool(rows) and not failed,'certifications':len(rows),'failed':failed}

@dataclass(frozen=True)
class RecoveryDrill:
 drill_id:str;failure_injected:bool;recovered:bool;data_integrity:bool;within_rto:bool
class RecoveryGate:
 def evaluate(self,items):
  rows=list(items);failed=[x.drill_id for x in rows if not(x.failure_injected and x.recovered and x.data_integrity and x.within_rto)]
  return {'passed':bool(rows) and not failed,'drills':len(rows),'failed':failed}

@dataclass(frozen=True)
class Waiver:
 waiver_id:str;issue_id:str;expires_at:float;owner:str;reason:str
class WaiverLifecycle:
 def evaluate(self,waivers,now=None):
  now=time.time() if now is None else now;expired=[];invalid=[]
  for x in waivers:
   if x.expires_at<=now:expired.append(x.waiver_id)
   if not x.owner.strip() or not x.reason.strip():invalid.append(x.waiver_id)
  return {'passed':not expired and not invalid,'expired':expired,'invalid':invalid}

def rc92_gate(*,freshness,upgrades,drift,trends,ecosystem,recovery,waivers):
 checks={'freshness':freshness.get('passed',False),'upgrades':upgrades.get('passed',False),'drift':drift.get('passed',False),'trends':trends.get('passed',False),'ecosystem':ecosystem.get('passed',False),'recovery':recovery.get('passed',False),'waivers':waivers.get('passed',False)}
 return {'gate':'GO' if all(checks.values()) else 'NO-GO','checks':checks,'failed':[k for k,v in checks.items() if not v]}
def certification_digest(report):return hashlib.sha256(json.dumps(report,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
