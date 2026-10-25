
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

# PeaLang v0.83 Runtime Performance II
from dataclasses import field
from contextlib import contextmanager
import json,time
from pathlib import Path

@dataclass(frozen=True)
class BenchmarkStats:
    name:str
    iterations:int
    mean_ms:float
    p50_ms:float
    p95_ms:float
    p99_ms:float
    throughput_per_sec:float
    peak_memory_mb:float

class BenchmarkSuite:
    """Run named representative workloads with percentile/throughput evidence."""
    def __init__(self,warmup=1,iterations=10):
        self.warmup=max(0,int(warmup));self.iterations=max(1,int(iterations));self._cases={}
    def add(self,name,fn):
        if not name or name in self._cases:raise ValueError('benchmark name must be unique')
        self._cases[name]=fn;return self
    @staticmethod
    def _pct(values,p):
        ordered=sorted(values);idx=min(len(ordered)-1,max(0,int(round((len(ordered)-1)*p))));return ordered[idx]
    def run(self):
        output={}
        for name,fn in sorted(self._cases.items()):
            sample=PerformanceProbe(self.warmup,self.iterations).run(fn);times=sample.durations_ms
            output[name]=BenchmarkStats(name,len(times),sample.mean_ms,self._pct(times,.50),self._pct(times,.95),self._pct(times,.99),1000.0/sample.mean_ms if sample.mean_ms>0 else float('inf'),sample.peak_memory_mb)
        return output

@dataclass(frozen=True)
class RegressionBudget:
    max_mean_regression_pct:float=10.0
    max_p95_regression_pct:float=15.0
    max_p99_regression_pct:float=20.0
    max_memory_regression_pct:float=15.0
    min_throughput_ratio:float=.90

class PerformanceRegressionGate:
    def compare(self,current,baseline,budget=RegressionBudget()):
        reports={};passed=True
        for name,cur in current.items():
            if name not in baseline:
                reports[name]={'status':'NEW'};continue
            base=baseline[name]
            def delta(a,b):return 0.0 if b==0 and a==0 else float('inf') if b==0 else ((a-b)/b)*100.0
            throughput_ratio=1.0 if base.throughput_per_sec==0 and cur.throughput_per_sec==0 else (cur.throughput_per_sec/base.throughput_per_sec if base.throughput_per_sec else float('inf'))
            metrics={'mean_regression_pct':delta(cur.mean_ms,base.mean_ms),'p95_regression_pct':delta(cur.p95_ms,base.p95_ms),'p99_regression_pct':delta(cur.p99_ms,base.p99_ms),'memory_regression_pct':delta(cur.peak_memory_mb,base.peak_memory_mb),'throughput_ratio':throughput_ratio}
            checks={'mean':metrics['mean_regression_pct']<=budget.max_mean_regression_pct,'p95':metrics['p95_regression_pct']<=budget.max_p95_regression_pct,'p99':metrics['p99_regression_pct']<=budget.max_p99_regression_pct,'memory':metrics['memory_regression_pct']<=budget.max_memory_regression_pct,'throughput':throughput_ratio>=budget.min_throughput_ratio}
            ok=all(checks.values());passed=passed and ok;reports[name]={'status':'PASS' if ok else 'FAIL','metrics':metrics,'checks':checks}
        missing=sorted(set(baseline)-set(current));passed=passed and not missing
        return {'gate':'PASS' if passed else 'FAIL','benchmarks':reports,'missing':missing,'budget':asdict(budget)}

@dataclass
class HotPathStats:
    name:str
    calls:int=0
    total_ms:float=0.0
    max_ms:float=0.0
    @property
    def mean_ms(self):return self.total_ms/max(1,self.calls)

class HotPathProfiler:
    """Low-overhead named timing for compiler/optimizer/runtime hot paths."""
    def __init__(self):self._stats={}
    @contextmanager
    def track(self,name):
        start=perf_counter()
        try:yield
        finally:
            elapsed=(perf_counter()-start)*1000.0;s=self._stats.setdefault(name,HotPathStats(name));s.calls+=1;s.total_ms+=elapsed;s.max_ms=max(s.max_ms,elapsed)
    def snapshot(self):return {k:{'calls':v.calls,'total_ms':v.total_ms,'mean_ms':v.mean_ms,'max_ms':v.max_ms} for k,v in sorted(self._stats.items())}

class InstrumentedLRUCache(BoundedLRUCache):
    def __init__(self,max_entries=128):super().__init__(max_entries);self.evictions=0;self.loads=0
    def get(self,key,factory):
        existed=key in self._data;before=len(self._data)
        if existed:return super().get(key,factory)
        self.loads+=1;value=factory();self.misses+=1;self._data[key]=value
        while len(self._data)>self.max_entries:self._data.popitem(last=False);self.evictions+=1
        return value
    def stats(self):
        result=super().stats();result.update({'loads':self.loads,'evictions':self.evictions});return result

@dataclass(frozen=True)
class MemoryPressureResult:
    rounds:int
    peak_memory_mb:float
    retained_memory_mb:float
    growth_mb:float

class MemoryPressureProbe:
    def __init__(self,rounds=5):self.rounds=max(1,int(rounds))
    def run(self,fn):
        gc.collect();tracemalloc.start();before=tracemalloc.get_traced_memory()[0]
        try:
            for _ in range(self.rounds):fn();gc.collect()
            current,peak=tracemalloc.get_traced_memory()
        finally:tracemalloc.stop()
        return MemoryPressureResult(self.rounds,peak/(1024*1024),current/(1024*1024),max(0,current-before)/(1024*1024))

def save_benchmark_baseline(path,version,results):
    payload={'schema':1,'version':version,'benchmarks':{k:asdict(v) for k,v in sorted(results.items())}};Path(path).write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');return payload

def load_benchmark_baseline(path):
    payload=json.loads(Path(path).read_text());return {k:BenchmarkStats(**v) for k,v in payload.get('benchmarks',{}).items()}

