


"""Observability and operations hardening for PeaLang 0.80."""
from __future__ import annotations
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib, json, platform, re, time, uuid, zipfile
from pathlib import Path
from typing import Any, Callable, Mapping

_TP=re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([01][0-9a-f])$")
_CTX:ContextVar["TraceContext|None"]=ContextVar("pealang_trace_context",default=None)
_SECRETS=("token","password","secret","authorization","cookie","api_key","apikey","credential")

@dataclass(frozen=True)
class TraceContext:
 trace_id:str; span_id:str; trace_flags:str="01"; baggage:Mapping[str,str]=field(default_factory=dict)
 @classmethod
 def new(cls,baggage=None):return cls(uuid.uuid4().hex,uuid.uuid4().hex[:16],"01",dict(baggage or {}))
 @classmethod
 def from_headers(cls,headers):
  h={str(k).lower():str(v) for k,v in headers.items()};m=_TP.match(h.get("traceparent",""))
  if not m:return None
  bag={}
  for item in h.get("baggage","").split(","):
   if "=" in item:
    k,v=item.strip().split("=",1)
    if k:bag[k]=v
  return cls(m.group(1),m.group(2),m.group(3),bag)
 def child(self):return TraceContext(self.trace_id,uuid.uuid4().hex[:16],self.trace_flags,dict(self.baggage))
 def headers(self):
  h={"traceparent":f"00-{self.trace_id}-{self.span_id}-{self.trace_flags}"}
  if self.baggage:h["baggage"]=",".join(f"{k}={v}" for k,v in sorted(self.baggage.items()))
  return h
class SpanStatus(str,Enum):OK="ok";ERROR="error"
@dataclass(frozen=True)
class SpanRecord:
 name:str;trace_id:str;span_id:str;parent_span_id:str|None;started_ns:int;ended_ns:int;status:SpanStatus;attributes:Mapping[str,Any]=field(default_factory=dict);error_type:str|None=None
 @property
 def duration_ms(self):return (self.ended_ns-self.started_ns)/1_000_000
class InMemorySpanExporter:
 def __init__(self,capacity=10000):
  if capacity<1:raise ValueError("capacity must be positive")
  self.capacity=capacity;self.records=[]
 def export(self,record):
  self.records.append(record)
  if len(self.records)>self.capacity:del self.records[:len(self.records)-self.capacity]
class Tracer:
 def __init__(self,exporter=None,clock=time.time_ns):self.exporter=exporter or InMemorySpanExporter();self.clock=clock
 @contextmanager
 def span(self,name,attributes=None,context=None):
  parent=context or _CTX.get();active=parent.child() if parent else TraceContext.new();token=_CTX.set(active);started=self.clock();status=SpanStatus.OK;error=None
  try:yield active
  except Exception as exc:status=SpanStatus.ERROR;error=exc.__class__.__name__;raise
  finally:
   ended=self.clock();_CTX.reset(token);self.exporter.export(SpanRecord(name,active.trace_id,active.span_id,parent.span_id if parent else None,started,ended,status,dict(attributes or {}),error))
def current_trace_context():return _CTX.get()
def inject_trace_headers(headers=None,context=None):
 result=dict(headers or {});active=context or _CTX.get()
 if active:result.update(active.headers())
 return result
class MetricKind(str,Enum):COUNTER="counter";GAUGE="gauge";HISTOGRAM="histogram"
@dataclass(frozen=True)
class MetricPoint:name:str;kind:MetricKind;value:float;attributes:Mapping[str,str];timestamp_ns:int
class MetricRegistry:
 def __init__(self,prefix="pealang",max_series=2000,clock=time.time_ns):
  if not re.match(r"^[a-z][a-z0-9_]*$",prefix):raise ValueError("metric prefix must be lower snake_case")
  self.prefix=prefix;self.max_series=max_series;self.clock=clock;self._points=[];self._series=set()
 def record(self,name,value,kind=MetricKind.COUNTER,attributes=None):
  if not re.match(r"^[a-z][a-z0-9_]*$",name):raise ValueError("metric name must be lower snake_case")
  attrs={str(k):str(v) for k,v in sorted((attributes or {}).items())};full=f"{self.prefix}_{name}";series=(full,tuple(attrs.items()))
  if series not in self._series and len(self._series)>=self.max_series:raise RuntimeError("metric series limit exceeded")
  self._series.add(series);point=MetricPoint(full,kind,float(value),attrs,self.clock());self._points.append(point);return point
 def snapshot(self):return [{**asdict(x),"kind":x.kind.value} for x in self._points]
class CheckState(str,Enum):PASS="pass";FAIL="fail"
@dataclass(frozen=True)
class CheckResult:name:str;state:CheckState;detail:str;latency_ms:float;critical:bool=True
@dataclass(frozen=True)
class ServiceStatus:
 status:str;checks:tuple[CheckResult,...];generated_at:float
 @property
 def healthy(self):return self.status=="healthy"
class HealthRegistry:
 def __init__(self,clock=time.monotonic):self.clock=clock;self._live={};self._ready={}
 def add_liveness(self,name,probe,critical=True):self._live[name]=(probe,critical)
 def add_readiness(self,name,probe,critical=True):self._ready[name]=(probe,critical)
 def _run(self,checks):
  out=[]
  for name,(probe,critical) in sorted(checks.items()):
   start=self.clock()
   try:
    if probe() is False:raise RuntimeError("probe returned false")
    r=CheckResult(name,CheckState.PASS,"ok",(self.clock()-start)*1000,critical)
   except Exception as exc:r=CheckResult(name,CheckState.FAIL,f"{exc.__class__.__name__}: {exc}",(self.clock()-start)*1000,critical)
   out.append(r)
  failed=any(x.critical and x.state is CheckState.FAIL for x in out);return ServiceStatus("unhealthy" if failed else "healthy",tuple(out),time.time())
 def liveness(self):return self._run(self._live)
 def readiness(self):return self._run(self._ready)
def _redact(value,key=""):
 if any(x in key.lower() for x in _SECRETS):return "[REDACTED]"
 if isinstance(value,Mapping):return {str(k):_redact(v,str(k)) for k,v in value.items()}
 if isinstance(value,(list,tuple)):return [_redact(v) for v in value]
 text=str(value);return text if len(text)<=1024 else text[:1024]+"...[TRUNCATED]"
class DiagnosticBundleBuilder:
 def __init__(self,max_file_bytes=1_000_000,max_bundle_bytes=10_000_000):self.max_file_bytes=max_file_bytes;self.max_bundle_bytes=max_bundle_bytes;self._entries={}
 def add_json(self,name,value):return self.add_bytes(name if name.endswith('.json') else name+'.json',json.dumps(_redact(value),indent=2,sort_keys=True,default=str).encode())
 def add_bytes(self,name,payload):
  if Path(name).name!=name or not name or len(payload)>self.max_file_bytes:raise ValueError("unsafe diagnostic entry or entry exceeds limit")
  if sum(map(len,self._entries.values()))+len(payload)>self.max_bundle_bytes:raise ValueError("diagnostic bundle exceeds limit")
  self._entries[name]=payload;return self
 def add_runtime_summary(self,version):return self.add_json("runtime",{"pealang_version":version,"python":platform.python_version(),"platform":platform.platform()})
 def build(self,target):
  path=Path(target);path.parent.mkdir(parents=True,exist_ok=True);manifest={n:{"bytes":len(d),"sha256":hashlib.sha256(d).hexdigest()} for n,d in sorted(self._entries.items())};entries=dict(self._entries);entries["manifest.json"]=json.dumps(manifest,indent=2,sort_keys=True).encode()
  with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED) as z:
   for n,d in sorted(entries.items()):z.writestr(n,d)
  return path



