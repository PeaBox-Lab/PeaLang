

"""Beta/pilot and 1.0-readiness evidence model for PeaLang 0.41."""
from dataclasses import dataclass,asdict,field
from pathlib import Path
import json,time
@dataclass
class Pilot:
 name:str;host:str;scenario:str;status:str='planned';evidence:list[str]=field(default_factory=list)
@dataclass
class PerformanceThresholds:
 max_regression_pct:float=10.0
 max_startup_ms:float=100.0
 max_p95_invoke_ms:float=25.0
@dataclass
class ReadinessReport:
 version:str='0.41';pilots:list=field(default_factory=list);stable_hosts:list=field(default_factory=list);thresholds:dict=field(default_factory=dict);security_review:dict=field(default_factory=dict);migration:dict=field(default_factory=dict)
 def gates(self):
  completed=sum(1 for p in self.pilots if p.get('status')=='validated')
  return {'two_validated_pilots':completed>=2,'three_stable_hosts':len(self.stable_hosts)>=3,'performance_thresholds_defined':bool(self.thresholds),'security_review_pack_ready':bool(self.security_review.get('prepared')),'migration_report_ready':bool(self.migration.get('prepared'))}
 def ok(self):return all(self.gates().values())
 def to_dict(self):return {**asdict(self),'gates':self.gates(),'ok':self.ok()}
def default_report():
 return ReadinessReport(pilots=[asdict(Pilot('HR bonus rules','Python/FastAPI','embedded compensation rule extension')),asdict(Pilot('Service extension','Java sidecar','Java host invokes signed PeaLang module'))],stable_hosts=['Python embedding','Java runtime sidecar','TypeScript runtime client'],thresholds=asdict(PerformanceThresholds()),security_review={'prepared':True,'scope':['runtime permissions','resource limits','package signatures','registry replay','safe extraction','browser capability profile'],'external_review_completed':False},migration={'prepared':True,'from':'0.x','to':'1.0','open_items':['stability promotion decisions','PEAC compatibility promise','coverage/CI evidence','pilot validation evidence']})
def save_report(path,report=None):
 r=report or default_report();Path(path).write_text(json.dumps(r.to_dict(),indent=2)+'\n');return r.to_dict()


