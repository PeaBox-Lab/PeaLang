



"""Deterministic runtime resource accounting for PeaLang 0.37."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import sys,time
class ResourceLimitExceeded(RuntimeError):
 def __init__(self,resource,limit,observed):super().__init__(f"{resource} limit exceeded: {observed} > {limit}");self.resource,self.limit,self.observed=resource,limit,observed
@dataclass(frozen=True)
class ResourceLimits:
 max_execution_ms:int=1000
 max_instructions:int=100_000
 max_memory_bytes:int=16*1024*1024
 max_recursion_depth:int=100
 max_stack_depth:int=1024
 max_collection_items:int=100_000
 max_output_bytes:int=1024*1024
 max_http_requests:int=32
 max_file_read_bytes:int=8*1024*1024
@dataclass
class ResourceUsage:
 instructions:int=0
 memory_bytes:int=0
 recursion_depth:int=0
 stack_depth:int=0
 collection_items:int=0
 output_bytes:int=0
 http_requests:int=0
 file_read_bytes:int=0
 elapsed_ms:float=0.0
class ResourceBudget:
 def __init__(self,limits=None):self.limits=limits or ResourceLimits();self.usage=ResourceUsage();self.started=time.perf_counter()
 def _take(self,name,amount,limit_name):
  value=getattr(self.usage,name)+int(amount);setattr(self.usage,name,value);limit=getattr(self.limits,limit_name)
  if value>limit:raise ResourceLimitExceeded(name,limit,value)
  return value
 def instruction(self,n=1):return self._take('instructions',n,'max_instructions')
 def memory(self,n):return self._take('memory_bytes',n,'max_memory_bytes')
 def collection(self,n):return self._take('collection_items',n,'max_collection_items')
 def output(self,value):return self._take('output_bytes',len(str(value).encode('utf-8')),'max_output_bytes')
 def http_request(self):return self._take('http_requests',1,'max_http_requests')
 def file_read(self,n):return self._take('file_read_bytes',n,'max_file_read_bytes')
 def set_recursion(self,n):self.usage.recursion_depth=n;self._check_peak('recursion_depth',n,'max_recursion_depth')
 def set_stack(self,n):self.usage.stack_depth=n;self._check_peak('stack_depth',n,'max_stack_depth')
 def _check_peak(self,name,value,limit_name):
  limit=getattr(self.limits,limit_name)
  if value>limit:raise ResourceLimitExceeded(name,limit,value)
 def deadline(self):
  self.usage.elapsed_ms=(time.perf_counter()-self.started)*1000
  if self.usage.elapsed_ms>self.limits.max_execution_ms:raise ResourceLimitExceeded('execution_ms',self.limits.max_execution_ms,round(self.usage.elapsed_ms,3))
 def snapshot(self):self.usage.elapsed_ms=(time.perf_counter()-self.started)*1000;return {'limits':asdict(self.limits),'usage':asdict(self.usage)}
def estimated_size(value,seen=None):
 seen=seen or set();oid=id(value)
 if oid in seen:return 0
 seen.add(oid);size=sys.getsizeof(value)
 if isinstance(value,dict):size+=sum(estimated_size(k,seen)+estimated_size(v,seen) for k,v in value.items())
 elif isinstance(value,(list,tuple,set,frozenset)):size+=sum(estimated_size(x,seen) for x in value)
 return size




