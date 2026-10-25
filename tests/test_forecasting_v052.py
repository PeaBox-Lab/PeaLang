

from pealang.data import DataFrame
from pealang.forecasting import *
def test_metrics():
 assert mae([1,2],[1,4])==1 and mse([1,2],[1,4])==2 and round(rmse([1,2],[1,4]),6)==round(2**.5,6) and mape([1,2],[1,4])==50
def test_split():
 a,b=DataFrame([{'x':i} for i in range(10)]).train_test_split(.2);assert a.row_count==8 and b.row_count==2
def test_linear():
 f=linear_trend([1,2,3],2);assert f['forecast'][0]['forecast']==4 and f['slope']==1
def test_ma_forecast():assert moving_average_forecast([1,2,3],1,2)[0]['forecast']==2.5
def test_exp():assert exponential_smoothing([1,3],2,.5)['forecast'][0]['forecast']==2
def test_decompose():assert len(seasonal_decompose([1,2,1,2,1,2],2)['seasonal'])==6
def test_grouped():
 d=DataFrame([{'g':'a','x':1},{'g':'a','x':2},{'g':'b','x':3},{'g':'b','x':4}]);assert d.grouped_forecast('g','x',1).row_count==2
def test_chart():assert DataFrame([{'d':1,'x':2}]).chart_series('d','x')['y']==[2]
def test_eval():assert set(evaluate([1],[2]))=={'mae','mse','rmse','mape'}
def test_numpy_mean():assert numpy_accelerated_mean([1,3])==2
def test_benchmark():assert benchmark_forecast([1,2,3],2).points==6
def test_bad_alpha():
 try:exponential_smoothing([1],1,0);assert False
 except ValueError:assert True
def test_bad_season():
 try:seasonal_decompose([1,2],2);assert False
 except ValueError:assert True


