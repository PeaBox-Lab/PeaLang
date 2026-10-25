"""PeaLang v0.77 runtime performance and memory hardening helpers."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from time import perf_counter
from typing import Callable,Any
import tracemalloc,statistics,gc

@dataclass(frozen=True)
class PerformanceBudget:
    max_mean_ms:float|None=None
    max_p95_ms:float|None=None
    max_peak_memory_mb:float|None=None

@dataclass(frozen=True)
class PerformanceSample:
    durations_ms:tuple[float,...]
    mean_ms:float
    p95_ms:float
    peak_memory_mb:float
    iterations:int

class PerformanceProbe:
    def __init__(self,warmup=1,iterations=5):self.warmup=max(0,int(warmup));self.iterations=max(1,int(iterations))
    def run(self,fn:Callable[[],Any]):
        for _ in range(self.warmup):fn()
        gc.collect();tracemalloc.start();times=[]
        try:
            for _ in range(self.iterations):
                start=perf_counter();fn();times.append((perf_counter()-start)*1000.0)
            _,peak=tracemalloc.get_traced_memory()
        finally:tracemalloc.stop()
        ordered=sorted(times);p95=ordered[min(len(ordered)-1,max(0,int((len(ordered)-1)*.95)))]
        return PerformanceSample(tuple(times),statistics.fmean(times),p95,peak/(1024*1024),len(times))

class PerformanceGate:
    def evaluate(self,sample:PerformanceSample,budget:PerformanceBudget):
        checks={
            'mean_ms':budget.max_mean_ms is None or sample.mean_ms<=budget.max_mean_ms,
            'p95_ms':budget.max_p95_ms is None or sample.p95_ms<=budget.max_p95_ms,
            'peak_memory_mb':budget.max_peak_memory_mb is None or sample.peak_memory_mb<=budget.max_peak_memory_mb,
        }
        return {'gate':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'sample':asdict(sample),'budget':asdict(budget)}

class BoundedLRUCache:
    """Small dependency-free LRU cache for repeated runtime/compiler artifacts."""
    def __init__(self,max_entries=128):
        from collections import OrderedDict
        self.max_entries=max(1,int(max_entries));self._data=OrderedDict();self.hits=0;self.misses=0
    def get(self,key,factory:Callable[[],Any]):
        if key in self._data:
            self.hits+=1;value=self._data.pop(key);self._data[key]=value;return value
        self.misses+=1;value=factory();self._data[key]=value
        while len(self._data)>self.max_entries:self._data.popitem(last=False)
        return value
    def clear(self):self._data.clear()
    def stats(self):return {'entries':len(self._data),'max_entries':self.max_entries,'hits':self.hits,'misses':self.misses,'hit_rate':self.hits/max(1,self.hits+self.misses)}