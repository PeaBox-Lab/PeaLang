



from pealang.data import DataFrame
from pealang.ml import LinearRegression,LogisticRegression,prediction_schema
from pealang.mlops import *
def model():return LinearRegression([2],1,['x'])
def test_bundle(tmp_path):
 m=create_model_bundle(model(),tmp_path/'b',model_id='m');loaded,meta=load_model_bundle(tmp_path/'b');assert meta['model_id']=='m' and loaded.predict_rows(DataFrame([{'x':2}]))==[5]
def test_bundle_integrity(tmp_path):
 create_model_bundle(model(),tmp_path/'b');(tmp_path/'b'/'model.json').write_text('{}')
 try:load_model_bundle(tmp_path/'b');assert False
 except ValueError:assert True
def test_batch():assert batch_predict(model(),DataFrame([{'x':1},{'x':2}]),1).row_count==2
def test_audit():
 p,a=audited_predict(model(),DataFrame([{'x':1}]),'m','1');assert p.to_dicts()[0]['prediction']==3 and len(a.to_dicts()[0]['input_hash'])==64
def test_psi():assert population_stability_index([1,2,3,4],[10,11,12,13])>0
def test_cat_drift():assert categorical_drift(['a','a'],['b','b'])==1
def test_fairness():
 r=group_fairness([1,0,1,0],[1,0,0,0],['a','a','b','b']);assert 'demographic_parity_difference' in r
def test_threshold():assert optimize_threshold([0,1],[.1,.9])['score']==1
def test_calibrator():
 c=PlattCalibrator().fit([-2,-1,1,2],[0,0,1,1],200,.1);p=c.transform([-2,2]);assert p[0]<p[1]
def test_registry(tmp_path):
 r=ModelRegistry(tmp_path/'registry.json');r.register('m','1','bundle');r.transition('m','1','production','raj');assert r.production('m').approved_by=='raj'
def test_compatibility():assert not compatibility_report(prediction_schema(model()),DataFrame([{'z':1}]))['compatible']
def test_benchmark():assert inference_benchmark(model(),DataFrame([{'x':1}]),2)['rows']==2




