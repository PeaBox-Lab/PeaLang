

from pealang.performance_hardening import *
def stat(name,mean=10,p95=12,p99=14,tp=100,mem=10):return BenchmarkStats(name,10,mean,mean,p95,p99,tp,mem)
def test_benchmark_suite_percentiles_and_throughput():
 r=BenchmarkSuite(warmup=0,iterations=4).add('sum',lambda:sum(range(100))).run()['sum'];assert r.iterations==4 and r.p50_ms>=0 and r.p99_ms>=r.p50_ms and r.throughput_per_sec>0
def test_regression_gate_passes_and_fails():
 b={'vm':stat('vm')};assert PerformanceRegressionGate().compare({'vm':stat('vm',10.5,12.5,14.5,98,10.5)},b)['gate']=='PASS'
 assert PerformanceRegressionGate().compare({'vm':stat('vm',20,24,28,50,20)},b)['gate']=='FAIL'
def test_hot_path_profiler():
 p=HotPathProfiler()
 with p.track('compiler.parse'):sum(range(100))
 s=p.snapshot()['compiler.parse'];assert s['calls']==1 and s['total_ms']>=0
def test_instrumented_cache_evictions():
 c=InstrumentedLRUCache(2);c.get('a',lambda:1);c.get('a',lambda:2);c.get('b',lambda:2);c.get('c',lambda:3);s=c.stats();assert s['hits']==1 and s['misses']==3 and s['loads']==3 and s['evictions']==1
def test_memory_pressure_and_baseline_roundtrip(tmp_path):
 probe=MemoryPressureProbe(rounds=2);r=probe.run(lambda:[x for x in range(1000)]);assert r.rounds==2 and r.peak_memory_mb>=0
 path=tmp_path/'baseline.json';save_benchmark_baseline(path,'0.83.0a1',{'vm':stat('vm')});loaded=load_benchmark_baseline(path);assert loaded['vm'].p95_ms==12


