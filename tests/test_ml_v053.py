


from pealang.data import DataFrame
from pealang.ml import *
def test_split_seed():
 a,b=DataFrame([{'x':i} for i in range(10)]).ml_split(2,True,1);assert a.row_count==8 and b.row_count==2
def test_standard():
 d=StandardScaler().fit_transform(DataFrame([{'x':1},{'x':3}]),['x']);assert round(d.to_dicts()[0]['x'],3)==-1
def test_minmax():assert MinMaxScaler().fit(DataFrame([{'x':1},{'x':3}]),['x']).transform(DataFrame([{'x':2}])).to_dicts()[0]['x']==.5
def test_impute():assert DataFrame([{'x':1},{'x':None},{'x':3}]).impute(['x']).to_dicts()[1]['x']==2
def test_onehot():assert DataFrame([{'g':'a'},{'g':'b'}]).one_hot_encode(['g']).to_dicts()[0]['g_a']==1
def test_linear():
 d=DataFrame([{'x':0,'y':1},{'x':1,'y':3},{'x':2,'y':5}]);m=LinearRegression().fit(d,['x'],'y',3000,.05);assert abs(m.predict_rows(DataFrame([{'x':3}]))[0]-7)<.1
def test_logistic():
 d=DataFrame([{'x':-2,'y':0},{'x':-1,'y':0},{'x':1,'y':1},{'x':2,'y':1}]);m=LogisticRegression().fit(d,['x'],'y',1000,.1);assert [r['prediction'] for r in m.predict(d).to_dicts()]==[0,0,1,1]
def test_reg_metrics():assert regression_metrics([1,2],[1,2])['r2']==1
def test_class_metrics():assert classification_metrics([0,1],[0,1])['accuracy']==1
def test_kfold():assert len(kfold_indices(10,5))==5 and all(len(t)==2 for _,t in kfold_indices(10,5))
def test_serialization(tmp_path):
 m=LinearRegression([2],1,['x']);p=tmp_path/'m.json';save_model(m,p);assert load_model(p).predict_rows(DataFrame([{'x':3}]))==[7]
def test_pipeline():assert Pipeline([(StandardScaler(),(['x'],))]).fit_transform(DataFrame([{'x':1},{'x':3}])).row_count==2



