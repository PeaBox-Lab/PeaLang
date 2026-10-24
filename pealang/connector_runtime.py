
from __future__ import annotations
from dataclasses import dataclass,field
from typing import Any
import time
from .connectors import ConnectorConfig
class TokenProvider:
 def token(self):raise NotImplementedError
class StaticTokenProvider(TokenProvider):
 def __init__(self,value):self.value=value
 def token(self):return self.value
class CallableTokenProvider(TokenProvider):
 def __init__(self,fn):self.fn=fn
 def token(self):return self.fn()
class CachedTokenProvider(TokenProvider):
 def __init__(self,provider,ttl=300,clock=time.time):self.provider,self.ttl,self.clock=provider,float(ttl),clock;self.value=None;self.expires=0
 def token(self):
  now=self.clock()
  if self.value is None or now>=self.expires:self.value=self.provider.token();self.expires=now+self.ttl
  return self.value
 def invalidate(self):self.value=None;self.expires=0
@dataclass
class ConnectorProfile:
 name:str;kind:str;endpoint:str;timeout:float=30;retries:int=2;backoff:float=.25;max_pages:int=100;headers:dict[str,str]=field(default_factory=dict);options:dict[str,Any]=field(default_factory=dict)
 def config(self):return ConnectorConfig(self.endpoint,dict(self.headers),self.timeout,self.retries,self.backoff,True,self.max_pages)
@dataclass
class HealthResult:name:str;healthy:bool;latency_ms:float;detail:str=''
def health_check(name,probe,clock=time.perf_counter):
 start=clock()
 try:probe();return HealthResult(name,True,(clock()-start)*1000,'ok')
 except Exception as exc:return HealthResult(name,False,(clock()-start)*1000,str(exc))
@dataclass(frozen=True)
class CertificationMatrix:required:tuple[str,...]=('connect','read');optional:tuple[str,...]=('write','paginate','dataframe','health')
def certify_matrix(connector,matrix=CertificationMatrix()):
 checks={x:hasattr(connector,x) for x in matrix.required+matrix.optional};return {'passed':all(checks[x] for x in matrix.required),'checks':checks}
