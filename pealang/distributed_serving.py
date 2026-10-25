"""PeaLang 0.60 distributed serving and Kubernetes operations."""
from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
import hashlib,json,math,time

class DistributedBackend:
 def increment(self,key,window_seconds):raise NotImplementedError
 def get(self,key):raise NotImplementedError
 def set(self,key,value,ttl=None):raise NotImplementedError
class MemoryBackend(DistributedBackend):
 def __init__(self,clock=time.time):self.clock=clock;self.values={};self.windows={}
 def increment(self,key,window_seconds):
  now=self.clock();start,count=self.windows.get(key,(now,0))
  if now-start>=window_seconds:start,count=now,0
  count+=1;self.windows[key]=(start,count);return count
 def get(self,key):return self.values.get(key)
 def set(self,key,value,ttl=None):self.values[key]=value;return value
class RedisBackend(DistributedBackend):
 def __init__(self,url='redis://localhost:6379/0',client=None,prefix='pealang:'):
  if client is None:
   try:import redis
   except ImportError as exc:raise RuntimeError('Redis backend requires optional dependency: redis') from exc
   client=redis.Redis.from_url(url,decode_responses=True)
  self.client,self.prefix=client,prefix
 def increment(self,key,window_seconds):
  k=self.prefix+key;value=self.client.incr(k)
  if value==1:self.client.expire(k,int(window_seconds))
  return int(value)
 def get(self,key):
  value=self.client.get(self.prefix+key)
  if value is None:return None
  try:return json.loads(value)
  except Exception:return value
 def set(self,key,value,ttl=None):
  payload=json.dumps(value);self.client.set(self.prefix+key,payload,ex=ttl);return value
class DistributedRateLimiter:
 def __init__(self,backend,limit=60,window_seconds=60):self.backend,self.limit,self.window=backend,int(limit),int(window_seconds)
 def check(self,client_id):
  count=self.backend.increment('rate:'+str(client_id),self.window)
  if count>self.limit:raise RuntimeError('Distributed rate limit exceeded')
  return self.limit-count
@dataclass
class SharedDeploymentState:
 backend:DistributedBackend
 key:str='deployment'
 def publish(self,plan):return self.backend.set(self.key,plan)
 def current(self):return self.backend.get(self.key)
 def route(self,routing_key):
  plan=self.current() or {};champion=plan.get('champion_version');challenger=plan.get('challenger_version');pct=int(plan.get('challenger_percent',0))
  if not challenger or pct<=0:return champion
  bucket=int(hashlib.sha256(str(routing_key).encode()).hexdigest()[:8],16)%100;return challenger if bucket<pct else champion
@dataclass
class LatencySummary:
 count:int;p50:float|None;p95:float|None;p99:float|None;mean:float|None;maximum:float|None
def latency_summary(values):
 vals=sorted(float(x) for x in values)
 def q(p):
  if not vals:return None
  position=(len(vals)-1)*p;lo=int(position);hi=min(lo+1,len(vals)-1);return vals[lo]+(vals[hi]-vals[lo])*(position-lo)
 return LatencySummary(len(vals),q(.50),q(.95),q(.99),sum(vals)/len(vals) if vals else None,max(vals) if vals else None)
def load_test(call,requests=100,concurrency=10,performance_gate=None):
 from concurrent.futures import ThreadPoolExecutor,as_completed
 latencies=[];errors=0;start=time.perf_counter()
 def one(i):
  s=time.perf_counter();call(i);return (time.perf_counter()-s)*1000
 with ThreadPoolExecutor(max_workers=int(concurrency)) as pool:
  futures=[pool.submit(one,i) for i in range(int(requests))]
  for f in as_completed(futures):
   try:latencies.append(f.result())
   except Exception:errors+=1
 seconds=time.perf_counter()-start;summary=latency_summary(latencies);result={'requests':int(requests),'completed':len(latencies),'errors':errors,'seconds':seconds,'requests_per_second':len(latencies)/seconds if seconds else float('inf'),'latency':summary.__dict__}
 gate=performance_gate or {};violations=[]
 if 'max_error_rate' in gate and errors/max(1,int(requests))>gate['max_error_rate']:violations.append('error rate')
 for key in ('p95','p99'):
  if 'max_'+key+'_ms' in gate and getattr(summary,key) is not None and getattr(summary,key)>gate['max_'+key+'_ms']:violations.append(key+' latency')
 result['gate_passed']=not violations;result['violations']=violations;return result
@dataclass
class KubernetesConfig:
 name:str='pealang-model';image:str='pealang/model:0.60.0';port:int=8000;replicas:int=2;cpu_request:str='250m';memory_request:str='256Mi';cpu_limit:str='1';memory_limit:str='1Gi';min_replicas:int=2;max_replicas:int=10;target_cpu:int=70;config_map:str|None=None;secret_name:str|None=None
def kubernetes_manifests(config=KubernetesConfig()):
 c=config;env_from=[]
 if c.config_map:env_from.append({'configMapRef':{'name':c.config_map}})
 if c.secret_name:env_from.append({'secretRef':{'name':c.secret_name}})
 container={'name':'server','image':c.image,'ports':[{'containerPort':c.port}],'resources':{'requests':{'cpu':c.cpu_request,'memory':c.memory_request},'limits':{'cpu':c.cpu_limit,'memory':c.memory_limit}},'startupProbe':{'httpGet':{'path':'/live','port':c.port},'failureThreshold':30,'periodSeconds':2},'readinessProbe':{'httpGet':{'path':'/ready','port':c.port},'periodSeconds':5},'livenessProbe':{'httpGet':{'path':'/live','port':c.port},'periodSeconds':10},'lifecycle':{'preStop':{'exec':{'command':['sh','-c','sleep 10']}}}}
 if env_from:container['envFrom']=env_from
 deployment={'apiVersion':'apps/v1','kind':'Deployment','metadata':{'name':c.name},'spec':{'replicas':c.replicas,'selector':{'matchLabels':{'app':c.name}},'template':{'metadata':{'labels':{'app':c.name}},'spec':{'terminationGracePeriodSeconds':30,'containers':[container]}}}}
 service={'apiVersion':'v1','kind':'Service','metadata':{'name':c.name},'spec':{'selector':{'app':c.name},'ports':[{'port':80,'targetPort':c.port}]}}
 hpa={'apiVersion':'autoscaling/v2','kind':'HorizontalPodAutoscaler','metadata':{'name':c.name},'spec':{'scaleTargetRef':{'apiVersion':'apps/v1','kind':'Deployment','name':c.name},'minReplicas':c.min_replicas,'maxReplicas':c.max_replicas,'metrics':[{'type':'Resource','resource':{'name':'cpu','target':{'type':'Utilization','averageUtilization':c.target_cpu}}}]}}
 monitor={'apiVersion':'monitoring.coreos.com/v1','kind':'ServiceMonitor','metadata':{'name':c.name},'spec':{'selector':{'matchLabels':{'app':c.name}},'endpoints':[{'port':'http','path':'/metrics','interval':'30s'}]}}
 return [deployment,service,hpa,monitor]
def write_kubernetes_manifests(directory,config=KubernetesConfig()):
 p=Path(directory);p.mkdir(parents=True,exist_ok=True);names=['deployment','service','hpa','servicemonitor']
 for name,doc in zip(names,kubernetes_manifests(config)):(p/(name+'.json')).write_text(json.dumps(doc,indent=2)+'\n')
 return [str(p/(x+'.json')) for x in names]
class OpenTelemetryHooks:
 def __init__(self,tracer=None):
  if tracer is None:
   try:from opentelemetry import trace;tracer=trace.get_tracer('pealang.serving')
   except ImportError:tracer=None
  self.tracer=tracer
 def span(self,name,attributes=None):
  if self.tracer:return self.tracer.start_as_current_span(name,attributes=attributes or {})
  class Noop:
   def __enter__(self):return self
   def __exit__(self,*args):return False
  return Noop()

