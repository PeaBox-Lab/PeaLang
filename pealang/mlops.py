



"""PeaLang 0.55 ML deployment, monitoring and governance."""
from __future__ import annotations
from dataclasses import dataclass,field,asdict
from datetime import datetime,timezone
from pathlib import Path
from math import log
from collections import Counter,defaultdict
import hashlib,json,time,uuid
from .data import DataFrame
from .ml import save_model,load_model,validate_prediction_schema,classification_metrics

BUNDLE_VERSION='1'
def _utc():return datetime.now(timezone.utc).isoformat()
def create_model_bundle(model,path,metadata=None,model_id=None,version='1.0.0'):
 p=Path(path);p.mkdir(parents=True,exist_ok=True);save_model(model,p/'model.json')
 manifest={'bundle_version':BUNDLE_VERSION,'model_id':model_id or str(uuid.uuid4()),'model_version':version,'model_type':model.__class__.__name__,'created_at':_utc(),'features':list(getattr(model,'features',[]) or []),'metadata':metadata or {}}
 raw=(p/'model.json').read_bytes();manifest['model_sha256']=hashlib.sha256(raw).hexdigest();(p/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');return manifest
def load_model_bundle(path):
 p=Path(path);manifest=json.loads((p/'manifest.json').read_text(encoding='utf-8'))
 if manifest.get('bundle_version')!=BUNDLE_VERSION:raise ValueError('Unsupported model bundle version: '+str(manifest.get('bundle_version')))
 raw=(p/'model.json').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=manifest['model_sha256']:raise ValueError('Model bundle integrity check failed')
 return load_model(p/'model.json'),manifest
def batch_predict(model,frame,batch_size=1000,name='prediction'):
 validate_prediction_schema(model,frame);rows=frame.to_dicts();out=[]
 for i in range(0,len(rows),int(batch_size)):out.extend(model.predict(DataFrame(rows[i:i+int(batch_size)]),name).to_dicts())
 return DataFrame(out)
@dataclass
class PredictionAudit:
 prediction_id:str;model_id:str;model_version:str;timestamp:str;input_hash:str;prediction:object;latency_ms:float
 def to_dict(self):return asdict(self)
def audited_predict(model,frame,model_id='model',model_version='1',name='prediction'):
 start=time.perf_counter();result=model.predict(frame,name);elapsed=(time.perf_counter()-start)*1000;audits=[]
 for source,row in zip(frame.to_dicts(),result.to_dicts()):audits.append(PredictionAudit(str(uuid.uuid4()),model_id,model_version,_utc(),hashlib.sha256(json.dumps(source,sort_keys=True,default=str).encode()).hexdigest(),row.get(name),elapsed/max(1,result.row_count)))
 return result,DataFrame([a.to_dict() for a in audits])
def population_stability_index(reference,current,bins=10):
 ref=[float(x) for x in reference if x is not None];cur=[float(x) for x in current if x is not None]
 if not ref or not cur:return None
 edges=[min(ref)+(max(ref)-min(ref))*i/bins for i in range(1,bins)]
 def dist(vals):
  counts=[0]*bins
  for v in vals:
   idx=sum(v>e for e in edges);counts[idx]+=1
  return [max(c/len(vals),1e-6) for c in counts]
 a,b=dist(ref),dist(cur);return sum((y-x)*log(y/x) for x,y in zip(a,b))
def categorical_drift(reference,current):
 a=Counter(reference);b=Counter(current);keys=set(a)|set(b);na=max(1,sum(a.values()));nb=max(1,sum(b.values()));return .5*sum(abs(a[k]/na-b[k]/nb) for k in keys)
def prediction_drift(reference,current):return categorical_drift(reference,current)
def group_fairness(actual,predicted,groups):
 stats={}
 for g in sorted(set(groups),key=str):
  idx=[i for i,x in enumerate(groups) if x==g];a=[actual[i] for i in idx];p=[predicted[i] for i in idx];m=classification_metrics(a,p);m['selection_rate']=sum(p)/len(p) if p else 0;stats[str(g)]=m
 rates=[x['selection_rate'] for x in stats.values()];return {'groups':stats,'demographic_parity_difference':max(rates)-min(rates) if rates else 0,'disparate_impact_ratio':min(rates)/max(rates) if rates and max(rates) else None}
def optimize_threshold(actual,probabilities,metric='f1',steps=101):
 best=None
 for i in range(steps):
  t=i/(steps-1);pred=[int(p>=t) for p in probabilities];score=classification_metrics(actual,pred)[metric]
  if best is None or score>best['score']:best={'threshold':t,'score':score,'metric':metric}
 return best
class PlattCalibrator:
 def __init__(self):self.a=1.;self.b=0.
 def fit(self,scores,labels,epochs=1000,learning_rate=.05):
  x=[float(v) for v in scores];y=[float(v) for v in labels]
  for _ in range(epochs):
   p=[1/(1+__import__('math').exp(-max(-30,min(30,self.a*v+self.b)))) for v in x];e=[q-t for q,t in zip(p,y)];self.a-=learning_rate*sum(z*v for z,v in zip(e,x))/len(x);self.b-=learning_rate*sum(e)/len(x)
  return self
 def transform(self,scores):return [1/(1+__import__('math').exp(-max(-30,min(30,self.a*float(v)+self.b)))) for v in scores]
@dataclass
class RegistryEntry:
 model_id:str;version:str;stage:str='draft';bundle_path:str='';created_at:str=field(default_factory=_utc);approved_by:str|None=None;rollback_to:str|None=None
class ModelRegistry:
 STAGES=('draft','validated','approved','production','retired')
 def __init__(self,path):self.path=Path(path);self.entries=[];self._load()
 def _load(self):
  if self.path.exists():self.entries=[RegistryEntry(**x) for x in json.loads(self.path.read_text())]
 def _save(self):self.path.parent.mkdir(parents=True,exist_ok=True);self.path.write_text(json.dumps([asdict(x) for x in self.entries],indent=2))
 def register(self,model_id,version,bundle_path,rollback_to=None):
  e=RegistryEntry(model_id,version,'draft',str(bundle_path),rollback_to=rollback_to);self.entries.append(e);self._save();return e
 def transition(self,model_id,version,stage,approved_by=None):
  if stage not in self.STAGES:raise ValueError('Invalid lifecycle stage: '+stage)
  e=self.get(model_id,version);e.stage=stage;e.approved_by=approved_by;self._save();return e
 def get(self,model_id,version):
  for e in self.entries:
   if e.model_id==model_id and e.version==version:return e
  raise KeyError(model_id+'@'+version)
 def production(self,model_id):
  matches=[e for e in self.entries if e.model_id==model_id and e.stage=='production'];return matches[-1] if matches else None
def compatibility_report(training_schema,serving_frame):
 required=list(training_schema.get('required_features',training_schema.get('features',[])));missing=[x for x in required if x not in serving_frame.columns];extra=[x for x in serving_frame.columns if x not in required];return {'compatible':not missing,'missing':missing,'extra':extra}
def inference_benchmark(model,frame,iterations=100):
 start=time.perf_counter();rows=0
 for _ in range(iterations):rows+=model.predict(frame).row_count
 seconds=time.perf_counter()-start;return {'iterations':iterations,'rows':rows,'seconds':seconds,'rows_per_second':rows/seconds if seconds else float('inf')}
def create_fastapi_app(model,name='prediction'):
 try:from fastapi import FastAPI,HTTPException
 except ImportError as exc:raise RuntimeError('FastAPI inference adapter requires optional dependency: fastapi') from exc
 app=FastAPI(title='PeaLang Model Inference',version='0.55.0')
 @app.get('/health')
 def health():return {'status':'ok'}
 @app.post('/predict')
 def predict(payload:list[dict]):
  try:return model.predict(DataFrame(payload),name).to_dicts()
  except Exception as exc:raise HTTPException(status_code=400,detail=str(exc))
 return app




