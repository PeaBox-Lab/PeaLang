
import time
from types import SimpleNamespace
from pealang.serving_resilience import *
class Runtime:
 def __init__(self):self.pipelines={'1':1};self.metadata={};self.plan=None
 def predict(self,records,key=None,**auth):return {'model_version':'1','predictions':records,'latency_ms':1}
def test_rate_limit():
 now=[0];r=SlidingWindowRateLimiter(1,60,lambda:now[0]);r.check('a')
 try:r.check('a');assert False
 except RateLimitExceeded:assert True
 now[0]=61;assert r.check('a')==0
def test_resilient_predict():
 r=ResilientRuntime(Runtime(),ResilienceConfig(10,2,1));out=r.predict([{'x':1}],client_id='c');assert out['correlation_id'] and r.health()['status']=='healthy'
def test_timeout():
 class Slow(Runtime):
  def predict(self,*a,**k):time.sleep(.1);return super().predict(*a,**k)
 r=ResilientRuntime(Slow(),ResilienceConfig(10,1,.01))
 try:r.predict([{}]);assert False
 except ServingTimeout:assert r.health()['status']=='degraded'
def test_logger(tmp_path):
 l=StructuredLogger(tmp_path/'x.jsonl');l.log('x',a=1);assert '"event": "x"' in (tmp_path/'x.jsonl').read_text()
def test_env(monkeypatch):
 monkeypatch.setenv('PEALANG_SERVE_RATE_LIMIT','7');assert ResilienceConfig.from_env().requests_per_minute==7
def test_switch_and_rollback():
 rt=Runtime();r=ResilientRuntime(rt);r.switch_plan(DeploymentPlan('m','2',None,0,'1'));alert=SimpleNamespace(status='open',severity='critical');assert r.rollback_on_alerts([alert]) and rt.plan.champion_version=='1'
def test_trace():
 t=TraceHooks();x=t.start('predict');assert t.end(x)['ended']>=x['started']
def test_reload(tmp_path):
 from pealang.data import DataFrame
 from pealang.ml import StandardScaler,LinearRegression,ProductionPipeline
 from pealang.mlops_portable import save_pipeline
 p=ProductionPipeline([(StandardScaler(),(['x'],))],LinearRegression()).fit(DataFrame([{'x':0,'y':1},{'x':1,'y':3}]),['x'],'y',epochs=300,learning_rate=.05);path=tmp_path/'p.json';save_pipeline(p,path);rt=Runtime();r=ResilientRuntime(rt);assert r.reload('2',path)=='2'

