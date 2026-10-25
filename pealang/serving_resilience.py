"""PeaLang 0.59 secure and resilient model serving."""
from __future__ import annotations
from dataclasses import dataclass,field
from collections import defaultdict,deque
from concurrent.futures import ThreadPoolExecutor,TimeoutError as FutureTimeout
from pathlib import Path
import json,os,threading,time,uuid
from .mlops_portable import load_pipeline
from .mlops_secure import verify_bundle_signature,decrypt_artifact,DeploymentPlan,should_rollback

class RateLimitExceeded(RuntimeError):pass
class ConcurrencyLimitExceeded(RuntimeError):pass
class ServingTimeout(RuntimeError):pass
@dataclass
class ResilienceConfig:
 requests_per_minute:int=60
 max_concurrency:int=8
 request_timeout_seconds:float=30
 audit_retention_days:int=30
 log_path:str|None=None
 @classmethod
 def from_env(cls,prefix='PEALANG_SERVE_'):
  return cls(int(os.getenv(prefix+'RATE_LIMIT',60)),int(os.getenv(prefix+'MAX_CONCURRENCY',8)),float(os.getenv(prefix+'TIMEOUT',30)),int(os.getenv(prefix+'AUDIT_RETENTION_DAYS',30)),os.getenv(prefix+'LOG_PATH'))
class SlidingWindowRateLimiter:
 def __init__(self,limit,window_seconds=60,clock=time.time):self.limit,self.window,self.clock=int(limit),float(window_seconds),clock;self.events=defaultdict(deque);self.lock=threading.Lock()
 def check(self,key):
  now=self.clock()
  with self.lock:
   q=self.events[str(key)]
   while q and q[0]<=now-self.window:q.popleft()
   if len(q)>=self.limit:raise RateLimitExceeded('Rate limit exceeded')
   q.append(now);return self.limit-len(q)
class StructuredLogger:
 def __init__(self,path=None):self.path=Path(path) if path else None;self.records=[];self.lock=threading.Lock()
 def log(self,event,**fields):
  record={'timestamp':time.time(),'event':event,**fields}
  with self.lock:
   self.records.append(record)
   if self.path:self.path.parent.mkdir(parents=True,exist_ok=True);self.path.open('a',encoding='utf-8').write(json.dumps(record,default=str)+'\n')
  return record
class ResilientRuntime:
 def __init__(self,runtime,config=None):
  self.runtime=runtime;self.config=config or ResilienceConfig();self.rate=SlidingWindowRateLimiter(self.config.requests_per_minute);self.slots=threading.BoundedSemaphore(self.config.max_concurrency);self.pool=ThreadPoolExecutor(max_workers=self.config.max_concurrency);self.logger=StructuredLogger(self.config.log_path);self.degraded=False
 def predict(self,records,client_id='anonymous',correlation_id=None,**auth):
  cid=correlation_id or str(uuid.uuid4());self.rate.check(client_id)
  if not self.slots.acquire(blocking=False):raise ConcurrencyLimitExceeded('Concurrency limit exceeded')
  start=time.perf_counter();self.logger.log('prediction_started',correlation_id=cid,client_id=client_id,count=len(records))
  try:
   future=self.pool.submit(self.runtime.predict,records,key=cid,**auth)
   try:result=future.result(timeout=self.config.request_timeout_seconds)
   except FutureTimeout:future.cancel();self.degraded=True;raise ServingTimeout('Prediction timed out')
   self.logger.log('prediction_completed',correlation_id=cid,version=result['model_version'],latency_ms=(time.perf_counter()-start)*1000);return {**result,'correlation_id':cid}
  except Exception as exc:self.logger.log('prediction_failed',correlation_id=cid,error=str(exc));raise
  finally:self.slots.release()
 def health(self):return {'status':'degraded' if self.degraded else 'healthy','loaded_versions':sorted(self.runtime.pipelines)}
 def switch_plan(self,plan):self.runtime.plan=plan;return plan
 def reload(self,version,path):
  pipeline,meta=load_pipeline(path);self.runtime.pipelines[str(version)]=pipeline;self.runtime.metadata[str(version)]=meta;self.logger.log('model_reloaded',version=str(version));return str(version)
 def rollback_on_alerts(self,alerts):
  if should_rollback(alerts) and self.runtime.plan and self.runtime.plan.rollback_version:
   self.runtime.plan=DeploymentPlan(self.runtime.plan.model_id,self.runtime.plan.rollback_version,None,0,self.runtime.plan.rollback_version);self.logger.log('automatic_rollback',version=self.runtime.plan.champion_version);return True
  return False
def verify_signed_pipeline(path,public_key):
 return verify_bundle_signature(path,public_key)
def load_encrypted_pipeline(encrypted_path,key,temp_path):decrypt_artifact(encrypted_path,temp_path,key);return load_pipeline(temp_path)
def prune_audits(sqlite_store,retention_days=30,now=None):
 cutoff=(now or time.time())-int(retention_days)*86400;cur=sqlite_store.db.execute('delete from audits where timestamp < datetime(?, "unixepoch")',(cutoff,));sqlite_store.db.commit();return cur.rowcount
class TraceHooks:
 def __init__(self,on_start=None,on_end=None):self.on_start=on_start;self.on_end=on_end
 def start(self,name,attributes=None):
  token={'trace_id':str(uuid.uuid4()),'name':name,'started':time.time(),'attributes':attributes or {}}
  if self.on_start:self.on_start(token)
  return token
 def end(self,token,error=None):
  token.update({'ended':time.time(),'error':str(error) if error else None})
  if self.on_end:self.on_end(token)
  return token
