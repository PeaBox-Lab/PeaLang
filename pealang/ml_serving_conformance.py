

from dataclasses import dataclass
from enum import Enum
import hashlib,math
class ModelFormat(str,Enum):ONNX="onnx";PYTORCH="pytorch";PEALANG="pealang"
@dataclass(frozen=True)
class ModelContract:format:ModelFormat;input_schema:dict;output_schema:dict;rtol:float=1e-5;atol:float=1e-8
class ModelCompatibilityMatrix:
 def __init__(self):self.rows={}
 def register(self,n,c):self.rows[n]=c;return self
 def supports(self,n,f):return n in self.rows and self.rows[n].format==ModelFormat(f)
@dataclass(frozen=True)
class InferenceFixture:name:str;inputs:object;expected:object
class DeterministicInferenceSuite:
 def run(self,predict,c,fs):return [{"name":f.name,"status":"PASS" if predict(f.inputs)==f.expected else "FAIL"} for f in fs]
class OverloadController:
 def __init__(self,n):self.max_inflight=max(1,n);self.inflight=0;self.rejected=0
 def acquire(self):
  if self.inflight>=self.max_inflight:self.rejected+=1;return False
  self.inflight+=1;return True
 def release(self):self.inflight=max(0,self.inflight-1)
class ModelSlot:
 def __init__(self,v,m):self.version=v;self.model=m;self.previous=None
 def reload(self,v,m,healthcheck=lambda m:True):
  if not healthcheck(m):return False
  self.previous=(self.version,self.model);self.version,self.model=v,m;return True
 def rollback(self):
  if not self.previous:return False
  self.version,self.model=self.previous;self.previous=None;return True
class CanaryRouter:
 def __init__(self,p=0):self.percent=max(0,min(100,p))
 def route(self,k):return "canary" if int(hashlib.sha256(str(k).encode()).hexdigest()[:8],16)%100<self.percent else "stable"
def serving_certification_gate(rs,o,r,b):
 c={"inference":all(x["status"]=="PASS" for x in rs),"overload":bool(o),"reload":bool(r),"rollback":bool(b)};return {"gate":"PASS" if all(c.values()) else "FAIL","checks":c}


