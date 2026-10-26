



from pealang.data import DataFrame
from pealang.ml import *
def reg():return DataFrame([{'x':0,'y':1},{'x':1,'y':3},{'x':2,'y':5},{'x':3,'y':7},{'x':4,'y':9},{'x':5,'y':11}])
def test_label_encoder():
 e=LabelEncoder();assert e.fit_transform(['b','a'])==[1,0] and e.inverse_transform([0,1])==['a','b']
def test_stratified():
 d=DataFrame([{'y':0},{'y':0},{'y':1},{'y':1}]);a,b=d.stratified_split('y',.5,1);assert b.row_count==2 and {r['y'] for r in b.to_dicts()}=={0,1}
def test_prob_metrics():assert roc_auc([0,1],[.1,.9])==1 and log_loss([0,1],[.1,.9])<.2
def test_ridge():assert abs(RidgeRegression().fit(reg(),['x'],'y',2000,.03,.001).predict_rows(DataFrame([{'x':6}]))[0]-13)<.3
def test_lasso():assert abs(LassoRegression().fit(reg(),['x'],'y',2000,.03,.001).predict_rows(DataFrame([{'x':6}]))[0]-13)<.3
def test_multiclass():
 d=DataFrame([{'x':-2,'y':'a'},{'x':-1,'y':'a'},{'x':1,'y':'b'},{'x':2,'y':'b'}]);m=MulticlassLogisticRegression().fit(d,['x'],'y',500,.1);assert [r['prediction'] for r in m.predict(d).to_dicts()]==['a','a','b','b']
def test_cv():assert len(cross_validate(LinearRegression,reg(),['x'],'y',3,fit_options={'epochs':500,'learning_rate':.03}))==3
def test_grid():
 g=grid_search(RidgeRegression,reg(),['x'],'y',{'epochs':[500],'learning_rate':[.03],'alpha':[.001,.01]},splits=2);assert 'alpha' in g['best_params']
def test_coefficients():assert coefficient_report(LinearRegression([2],1,['x'])).to_dicts()[0]['feature']=='x'
def test_schema_validation():
 m=LinearRegression([2],1,['x']);assert validate_prediction_schema(m,DataFrame([{'x':1}]))
 try:validate_prediction_schema(m,DataFrame([{'z':1}]));assert False
 except ValueError:assert True
def test_model_card_manifest():
 m=LinearRegression([2],1,['x']);assert model_card(m,'demo')['name']=='demo' and len(reproducibility_manifest(reg(),['x'],'y')['dataset_sha256'])==64
def test_pipeline():
 p=ProductionPipeline([(StandardScaler(),(['x'],))],LinearRegression()).fit(reg(),['x'],'y',epochs=1000,learning_rate=.05);assert p.predict(DataFrame([{'x':6}])).row_count==1




