from __future__ import annotations
import statistics,time
from .compiler import compile_source_to_bytecode
from .vm import VirtualMachine
def benchmark_source(source,iterations=20,source_name='<benchmark>'):
 module=compile_source_to_bytecode(source,source_name);samples=[]
 for _ in range(iterations):
  start=time.perf_counter();VirtualMachine(output=lambda x:None).run(module);samples.append((time.perf_counter()-start)*1000)
 return {'iterations':iterations,'min_ms':min(samples),'median_ms':statistics.median(samples),'mean_ms':statistics.mean(samples),'max_ms':max(samples)}

