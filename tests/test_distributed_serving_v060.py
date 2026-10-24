import time
from pealang.distributed_serving import *
def test_distributed_rate():
 b=MemoryBackend();r=DistributedRateLimiter(b,1);assert r.check('a')==0
 try:r.check('a');assert False
 except RuntimeError:assert True
def test_shared_state():
 s=SharedDeploymentState(MemoryBackend());s.publish({'champion_version':'1','challenger_version':'2','challenger_percent':100});assert s.route('x')=='2'
def test_latency():
 s=latency_summary([1,2,3,4]);assert s.p50==2.5 and s.p99>3
def test_load_gate():
 r=load_test(lambda i:i,20,4,{'max_error_rate':0,'max_p95_ms':100});assert r['gate_passed'] and r['completed']==20
def test_kubernetes():
 docs=kubernetes_manifests(KubernetesConfig(name='demo',config_map='cfg',secret_name='sec'));assert [d['kind'] for d in docs]==['Deployment','Service','HorizontalPodAutoscaler','ServiceMonitor'];c=docs[0]['spec']['template']['spec']['containers'][0];assert c['readinessProbe'] and len(c['envFrom'])==2
def test_write_manifests(tmp_path):assert len(write_kubernetes_manifests(tmp_path))==4
def test_otel_noop():
 with OpenTelemetryHooks(tracer=None).span('x'):pass
