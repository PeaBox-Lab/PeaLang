


from pealang.data import DataFrame
from pealang.ml import StandardScaler,LinearRegression,ProductionPipeline,save_model
from pealang.mlops_portable import *
def frame():return DataFrame([{'x':0,'y':1},{'x':1,'y':3},{'x':2,'y':5}])
def test_pipeline_roundtrip(tmp_path):
 p=ProductionPipeline([(StandardScaler(),(['x'],))],LinearRegression()).fit(frame(),['x'],'y',epochs=1000,learning_rate=.05);save_pipeline(p,tmp_path/'p.json');q,d=load_pipeline(tmp_path/'p.json');assert q.predict(DataFrame([{'x':3}])).row_count==1 and d['format']==PIPELINE_FORMAT
def test_sqlite_store(tmp_path):
 s=SQLiteMonitoringStore(tmp_path/'m.db');s.record('m','drift',.2);s.record('m','drift',.4);assert round(s.summary('m','drift')['mean'],2)==.3
def test_policy_file(tmp_path):
 p=tmp_path/'p.json';p.write_text('{"rules":[{"metric":"drift","threshold":0.2,"severity":"critical"}]}');assert load_alert_policy(p)[0].severity=='critical'
def test_deployment_manifest():assert deployment_manifest('m','1','b')['kind']=='ModelDeployment'
def test_cli_monitor(tmp_path):assert cli(['monitor',str(tmp_path/'m.db'),'m','drift','.3'])==0
def test_cli_bundle_verify(tmp_path):
 m=tmp_path/'model.json';save_model(LinearRegression([2],1,['x']),m);bundle=tmp_path/'bundle';assert cli(['bundle',str(m),str(bundle),'--model-id','m'])==0 and cli(['verify',str(bundle)])==0
def test_cli_registry(tmp_path):
 r=tmp_path/'r.json';b=tmp_path/'b';b.mkdir();assert cli(['register',str(r),'m','1',str(b)])==0 and cli(['promote',str(r),'m','1','approved','--approver','raj'])==0



