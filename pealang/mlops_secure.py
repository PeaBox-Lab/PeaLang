

"""PeaLang 0.56 secure bundles and monitoring operations."""
from __future__ import annotations
from dataclasses import dataclass,asdict,field
from datetime import datetime,timezone,timedelta
from pathlib import Path
import base64,hashlib,json,uuid

def _utc():return datetime.now(timezone.utc).isoformat()
def sign_bundle(path,private_key):
 p=Path(path);manifest=p/'manifest.json';payload=manifest.read_bytes()
 try:
  from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
  key=Ed25519PrivateKey.from_private_bytes(private_key) if isinstance(private_key,bytes) else private_key
 except ImportError as exc:raise RuntimeError('Bundle signing requires optional dependency: cryptography') from exc
 sig=key.sign(payload);record={'algorithm':'Ed25519','manifest_sha256':hashlib.sha256(payload).hexdigest(),'signature':base64.b64encode(sig).decode()};(p/'signature.json').write_text(json.dumps(record,indent=2));return record
def verify_bundle_signature(path,public_key):
 p=Path(path);payload=(p/'manifest.json').read_bytes();record=json.loads((p/'signature.json').read_text())
 if hashlib.sha256(payload).hexdigest()!=record['manifest_sha256']:return False
 try:
  from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
  key=Ed25519PublicKey.from_public_bytes(public_key) if isinstance(public_key,bytes) else public_key;key.verify(base64.b64decode(record['signature']),payload);return True
 except Exception:return False
def encrypt_artifact(source,target,key):
 try:from cryptography.fernet import Fernet
 except ImportError as exc:raise RuntimeError('Artifact encryption requires optional dependency: cryptography') from exc
 data=Path(source).read_bytes();Path(target).write_bytes(Fernet(key).encrypt(data));return str(target)
def decrypt_artifact(source,target,key):
 from cryptography.fernet import Fernet
 Path(target).write_bytes(Fernet(key).decrypt(Path(source).read_bytes()));return str(target)
@dataclass
class MonitoringEvent:
 event_id:str;model_id:str;metric:str;value:float;timestamp:str=field(default_factory=_utc);dimensions:dict=field(default_factory=dict)
class MonitoringStore:
 def __init__(self,path):self.path=Path(path);self.events=[];self._load()
 def _load(self):
  if self.path.exists():self.events=[MonitoringEvent(**x) for x in json.loads(self.path.read_text())]
 def _save(self):self.path.parent.mkdir(parents=True,exist_ok=True);self.path.write_text(json.dumps([asdict(x) for x in self.events],indent=2))
 def record(self,model_id,metric,value,dimensions=None,timestamp=None):
  e=MonitoringEvent(str(uuid.uuid4()),model_id,metric,float(value),timestamp or _utc(),dimensions or {});self.events.append(e);self._save();return e
 def query(self,model_id=None,metric=None,since=None):
  return [e for e in self.events if (model_id is None or e.model_id==model_id) and (metric is None or e.metric==metric) and (since is None or e.timestamp>=since)]
 def summary(self,model_id,metric,since=None):
  vals=[e.value for e in self.query(model_id,metric,since)];return {'count':len(vals),'min':min(vals) if vals else None,'max':max(vals) if vals else None,'mean':sum(vals)/len(vals) if vals else None}
@dataclass
class AlertRule:
 metric:str;threshold:float;operator:str='>';severity:str='warning';rollback:bool=False
@dataclass
class Alert:
 alert_id:str;model_id:str;metric:str;value:float;severity:str;created_at:str=field(default_factory=_utc);status:str='open';acknowledged_by:str|None=None
def evaluate_alerts(model_id,events,rules):
 out=[]
 for e in events:
  for r in rules:
   hit=e.metric==r.metric and ((r.operator=='>' and e.value>r.threshold) or (r.operator=='>=' and e.value>=r.threshold) or (r.operator=='<' and e.value<r.threshold) or (r.operator=='<=' and e.value<=r.threshold))
   if hit:out.append(Alert(str(uuid.uuid4()),model_id,e.metric,e.value,r.severity))
 return out
def acknowledge(alert,user):alert.status='acknowledged';alert.acknowledged_by=user;return alert
@dataclass
class PromotionPolicy:
 required_stage:str='approved';required_approvers:int=1;max_drift:float|None=None
def can_promote(entry,approvers,metrics,policy=PromotionPolicy()):
 reasons=[]
 if entry.stage!=policy.required_stage:reasons.append('stage must be '+policy.required_stage)
 if len(set(approvers))<policy.required_approvers:reasons.append('insufficient approvers')
 if policy.max_drift is not None and metrics.get('drift',0)>policy.max_drift:reasons.append('drift threshold exceeded')
 return {'allowed':not reasons,'reasons':reasons}
@dataclass
class DeploymentPlan:
 model_id:str;champion_version:str;challenger_version:str|None=None;challenger_percent:int=0;rollback_version:str|None=None
def route_variant(plan,key):
 if not plan.challenger_version or plan.challenger_percent<=0:return plan.champion_version
 bucket=int(hashlib.sha256(str(key).encode()).hexdigest()[:8],16)%100;return plan.challenger_version if bucket<plan.challenger_percent else plan.champion_version
def compare_variants(champion_metrics,challenger_metrics,metric='accuracy',higher_is_better=True):
 a=champion_metrics[metric];b=challenger_metrics[metric];return {'winner':'challenger' if (b>a if higher_is_better else b<a) else 'champion','champion':a,'challenger':b}
def should_rollback(alerts,critical_severities=('critical',)):
 return any(a.status=='open' and a.severity in critical_severities for a in alerts)
def structured_inference_log(model_id,version,input_count,latency_ms,status='ok',request_id=None):return {'request_id':request_id or str(uuid.uuid4()),'timestamp':_utc(),'model_id':model_id,'version':version,'input_count':int(input_count),'latency_ms':float(latency_ms),'status':status}


