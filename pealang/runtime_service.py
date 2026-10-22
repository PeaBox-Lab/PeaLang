"""Transport-neutral PeaLang runtime sidecar core for Java and other hosts."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib,json,time,uuid
from .compiler import compile_source_to_bytecode
from .bytecode import BytecodeModule
from .vm_embedding import VMRuntime
from .embedding import RuntimeOptions,to_pea
from .type_system import SemanticAnalyzer
@dataclass
class ServiceError:
 code:str;message:str;request_id:str
@dataclass
class RuntimeResponse:
 ok:bool;request_id:str;result:object=None;error:dict|None=None;elapsed_ms:float=0
class RuntimeService:
 def __init__(self,options=None,cache_size=128):self.options=options or RuntimeOptions();self.cache_size=cache_size;self.cache={};self.modules={};self.started=time.time()
 def _id(self):return uuid.uuid4().hex
 def _key(self,source):return hashlib.sha256(source.encode()).hexdigest()
 def health(self):return {'status':'UP','service':'pealang-runtime','version':'0.29.0','uptime_seconds':round(time.time()-self.started,3),'cached_scripts':len(self.cache),'loaded_modules':len(self.modules)}
 def readiness(self):return {'status':'READY','vm':True,'compiler':True,'semantic_analyzer':True}
 def compile(self,source,source_name='<remote>'):
  rid=self._id();start=time.perf_counter()
  try:
   sem=SemanticAnalyzer().analyze(source,source_name);errors=[str(x) for x in sem.diagnostics if x.severity=='error']
   if errors:return RuntimeResponse(False,rid,error=asdict(ServiceError('SEMANTIC_ERROR','; '.join(errors[:20]),rid)),elapsed_ms=(time.perf_counter()-start)*1000)
   key=self._key(source);module=self.cache.get(key)
   if module is None:
    module=compile_source_to_bytecode(source,source_name)
    if len(self.cache)>=self.cache_size:self.cache.pop(next(iter(self.cache)))
    self.cache[key]=module
   return RuntimeResponse(True,rid,{'cache_key':key,'bytecode':module.to_dict()},elapsed_ms=(time.perf_counter()-start)*1000)
  except Exception as e:return RuntimeResponse(False,rid,error=asdict(ServiceError('COMPILE_ERROR',str(e),rid)),elapsed_ms=(time.perf_counter()-start)*1000)
 def load(self,name,source,source_name='<remote>'):
  r=self.compile(source,source_name)
  if not r.ok:return r
  module=BytecodeModule.from_dict(r.result['bytecode']);runtime=VMRuntime(self.options);loaded=runtime.load_bytecode(module);self.modules[name]=(runtime,loaded)
  r.result={'module':name,'cache_key':r.result['cache_key'],'exports':sorted(loaded.exports)};return r
 def invoke(self,module,function,args=None):
  rid=self._id();start=time.perf_counter()
  try:
   if module not in self.modules:raise KeyError(f"Unknown module '{module}'")
   _,loaded=self.modules[module];value=loaded.call(function,*[to_pea(x) for x in (args or [])]);return RuntimeResponse(True,rid,to_pea(value),elapsed_ms=(time.perf_counter()-start)*1000)
  except Exception as e:return RuntimeResponse(False,rid,error=asdict(ServiceError('EXECUTION_ERROR',str(e),rid)),elapsed_ms=(time.perf_counter()-start)*1000)
 def handle(self,request):
  op=request.get('operation')
  if op=='health':return self.health()
  if op=='ready':return self.readiness()
  if op=='compile':return asdict(self.compile(request['source'],request.get('source_name','<remote>')))
  if op=='load':return asdict(self.load(request['name'],request['source'],request.get('source_name','<remote>')))
  if op=='invoke':return asdict(self.invoke(request['module'],request['function'],request.get('args',[])))
  rid=self._id();return asdict(RuntimeResponse(False,rid,error=asdict(ServiceError('BAD_REQUEST',f'Unknown operation: {op}',rid))))
