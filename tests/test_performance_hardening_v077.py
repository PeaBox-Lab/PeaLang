from pealang.performance_hardening import PerformanceBudget,PerformanceProbe,PerformanceGate,BoundedLRUCache

def test_performance_probe_and_gate():
    probe=PerformanceProbe(warmup=0,iterations=3);sample=probe.run(lambda:sum(range(100)))
    assert sample.iterations==3 and sample.mean_ms>=0 and sample.peak_memory_mb>=0
    assert PerformanceGate().evaluate(sample,PerformanceBudget(max_mean_ms=500,max_p95_ms=500,max_peak_memory_mb=32))['gate']=='PASS'

def test_performance_gate_can_fail():
    sample=PerformanceProbe(warmup=0,iterations=1).run(lambda:None)
    assert PerformanceGate().evaluate(sample,PerformanceBudget(max_mean_ms=-1))['gate']=='FAIL'

def test_bounded_lru_cache_evicts_and_tracks_hits():
    cache=BoundedLRUCache(2);calls=[]
    assert cache.get('a',lambda:calls.append('a') or 1)==1
    assert cache.get('a',lambda:2)==1
    cache.get('b',lambda:2);cache.get('c',lambda:3)
    stats=cache.stats();assert stats['entries']==2 and stats['hits']==1 and stats['misses']==3