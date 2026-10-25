


import json
from pealang.data import DataFrame
from pealang.ml import StandardScaler,LinearRegression,ProductionPipeline
from pealang.mlops_portable import save_pipeline,deployment_manifest,serving_cli
from pealang.mlops_secure import DeploymentPlan
from pealang.serving import *
def pipeline(tmp_path,name='p.json'):
 p=ProductionPipeline([(StandardScaler(),(['x'],))],LinearRegression()).fit(DataFrame([{'x':0,'y':1},{'x':1,'y':3},{'x':2,'y':5}]),['x'],'y',epochs=1000,learning_rate=.05);path=tmp_path/name;save_pipeline(p,path);return path
def test_runtime_predict(tmp_path):
 r=PipelineRuntime({'1':pipeline(tmp_path)},config=ServingConfig(audit_db=str(tmp_path/'a.db'),monitoring_db=str(tmp_path/'m.db')));out=r.predict([{'x':3}]);assert out['model_version']=='1' and r.audit.count()==1
def test_auth(tmp_path):
 r=PipelineRuntime({'1':pipeline(tmp_path)},config=ServingConfig(api_keys={'k'},audit_db=str(tmp_path/'a.db'),monitoring_db=str(tmp_path/'m.db')))
 try:r.predict([{'x':1}]);assert False
 except AuthError:assert True
 assert r.predict([{'x':1}],api_key='k')['predictions']
def test_limits(tmp_path):
 r=PipelineRuntime({'1':pipeline(tmp_path)},config=ServingConfig(max_records=1,audit_db=str(tmp_path/'a.db'),monitoring_db=str(tmp_path/'m.db')))
 try:r.predict([{'x':1},{'x':2}]);assert False
 except RequestLimitError:assert True
def test_canary(tmp_path):
 a=pipeline(tmp_path,'a.json');b=pipeline(tmp_path,'b.json');plan=DeploymentPlan('m','1','2',100,'1');r=PipelineRuntime({'1':a,'2':b},plan,ServingConfig(audit_db=str(tmp_path/'a.db'),monitoring_db=str(tmp_path/'m.db')));assert r.predict([{'x':1}])['model_version']=='2'
def test_metrics(tmp_path):
 r=PipelineRuntime({'1':pipeline(tmp_path)},config=ServingConfig(audit_db=str(tmp_path/'a.db'),monitoring_db=str(tmp_path/'m.db')));r.predict([{'x':1}]);assert 'pealang_inference_requests_total 1' in r.prometheus()
def test_deploy_check(tmp_path):
 p=pipeline(tmp_path);m=deployment_manifest('m','1',p);assert deploy_check(m,p)['valid']
def test_execute_and_cli(tmp_path):
 p=pipeline(tmp_path);m=deployment_manifest('m','1',p);mp=tmp_path/'d.json';mp.write_text(json.dumps(m));assert execute_deployment(mp)['pipeline_path']==str(p) and serving_cli(['deploy-check',str(mp),str(p)])==0 and serving_cli(['execute',str(mp)])==0



