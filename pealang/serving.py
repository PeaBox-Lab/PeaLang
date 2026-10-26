



"""PeaLang 0.58 serving runtime and deployment execution."""
from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
import hashlib,json,time,uuid
from .data import DataFrame
from .mlops import audited_predict
from .mlops_portable import load_pipeline,deployment_manifest,SQLiteMonitoringStore
from .mlops_secure import DeploymentPlan,route_variant

@dataclass
class ServingConfig:
 api_keys:set[str]=field(default_factory=set)
 bearer_tokens:set[str]=field(default_factory=set)
 max_records:int=1000
 max_body_bytes:int=1048576
 audit_db:str='inference-audit.db'
 monitoring_db:str='monitoring.db'
class AuthError(PermissionError):pass
class RequestLimitError(ValueError):pass
class PipelineRuntime:
 def __init__(self,bundles,plan=None,config=None):
  self.pipelines={};self.metadata={};self.config=config or ServingConfig();self.plan=plan
  for version,path in bundles.items():
   pipeline,meta=load_pipeline(path);self.pipelines[str(version)]=pipeline;self.metadata[str(version)]=meta
  if not self.pipelines:raise ValueError('At least one pipeline is required')
  self.audit=SQLiteAuditStore(self.config.audit_db);self.monitoring=SQLiteMonitoringStore(self.config.monitoring_db);self.started=time.time();self.requests=0;self.errors=0;self.latencies=[]
 def authenticate(self,api_key=None,bearer=None):
  if self.config.api_keys and api_key not in self.config.api_keys:raise AuthError('Invalid API key')
  if self.config.bearer_tokens and bearer not in self.config.bearer_tokens:raise AuthError('Invalid bearer token')
  return True
 def version_for(self,key=None):
  if self.plan:return route_variant(self.plan,key or str(uuid.uuid4()))
  return next(iter(self.pipelines))
 def predict(self,records,key=None,api_key=None,bearer=None):
  self.authenticate(api_key,bearer)
  if not isinstance(records,list):raise ValueError('Request payload must be a list of records')
  if len(records)>self.config.max_records:raise RequestLimitError('Maximum records exceeded')
  raw=json.dumps(records,default=str).encode()
  if len(raw)>self.config.max_body_bytes:raise RequestLimitError('Maximum request size exceeded')
  version=self.version_for(key);pipeline=self.pipelines[version];start=time.perf_counter()
  try:
   result=pipeline.predict(DataFrame(records));latency=(time.perf_counter()-start)*1000;self.requests+=1;self.latencies.append(latency);self.audit.record(version,records,result.to_dicts(),latency);self.monitoring.record(version,'latency_ms',latency);self.monitoring.record(version,'request_records',len(records));return {'model_version':version,'predictions':result.to_dicts(),'latency_ms':latency}
  except Exception:
   self.errors+=1;raise
 def metrics(self):
  avg=sum(self.latencies)/len(self.latencies) if self.latencies else 0
  return {'requests_total':self.requests,'errors_total':self.errors,'latency_ms_average':avg,'uptime_seconds':time.time()-self.started}
 def prometheus(self):
  m=self.metrics();return '\n'.join([f'pealang_inference_requests_total {m["requests_total"]}',f'pealang_inference_errors_total {m["errors_total"]}',f'pealang_inference_latency_ms_average {m["latency_ms_average"]}',f'pealang_inference_uptime_seconds {m["uptime_seconds"]}'])+'\n'
class SQLiteAuditStore:
 def __init__(self,path):
  import sqlite3
  self.db=sqlite3.connect(str(path),check_same_thread=False);self.db.execute('create table if not exists audits(request_id text primary key,timestamp text,version text,input_hash text,predictions text,latency_ms real)');self.db.commit()
 def record(self,version,records,predictions,latency):
  from datetime import datetime,timezone
  rid=str(uuid.uuid4());ts=datetime.now(timezone.utc).isoformat();h=hashlib.sha256(json.dumps(records,sort_keys=True,default=str).encode()).hexdigest();self.db.execute('insert into audits values(?,?,?,?,?,?)',(rid,ts,version,h,json.dumps(predictions,default=str),float(latency)));self.db.commit();return rid
 def count(self):return self.db.execute('select count(*) from audits').fetchone()[0]
def create_serving_app(runtime):
 try:from fastapi import FastAPI,Header,HTTPException,Request
 except ImportError as exc:raise RuntimeError('Serving app requires optional dependency: fastapi') from exc
 app=FastAPI(title='PeaLang Serving Runtime',version='0.58.0')
 @app.get('/live')
 def live():return {'status':'live'}
 @app.get('/ready')
 def ready():return {'status':'ready','versions':sorted(runtime.pipelines)}
 @app.get('/metrics')
 def metrics():
  from fastapi.responses import PlainTextResponse
  return PlainTextResponse(runtime.prometheus(),media_type='text/plain; version=0.0.4')
 @app.post('/predict')
 async def predict(request:Request,x_api_key:str|None=Header(default=None),authorization:str|None=Header(default=None),x_routing_key:str|None=Header(default=None)):
  body=await request.body()
  if len(body)>runtime.config.max_body_bytes:raise HTTPException(413,'Maximum request size exceeded')
  try:return runtime.predict(json.loads(body),x_routing_key,x_api_key,authorization.removeprefix('Bearer ') if authorization else None)
  except AuthError as exc:raise HTTPException(401,str(exc))
  except RequestLimitError as exc:raise HTTPException(413,str(exc))
  except Exception as exc:raise HTTPException(400,str(exc))
 return app
def deploy_check(manifest,pipeline_path):
 required={'apiVersion','kind','metadata','spec'};missing=sorted(required-set(manifest));issues=[]
 if missing:issues.append('missing manifest fields: '+', '.join(missing))
 try:load_pipeline(pipeline_path)
 except Exception as exc:issues.append('pipeline load failed: '+str(exc))
 return {'valid':not issues,'issues':issues}
def execute_deployment(manifest_path):
 manifest=json.loads(Path(manifest_path).read_text());bundle=manifest['spec']['bundle'];check=deploy_check(manifest,bundle)
 if not check['valid']:raise ValueError('; '.join(check['issues']))
 return {'manifest':manifest,'pipeline_path':bundle,'environment':manifest['spec'].get('environment','production')}




