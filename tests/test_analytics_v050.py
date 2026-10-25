from pealang.data import DataFrame
from pealang.analytics import *
def sample():return DataFrame([{'g':'A','x':1,'y':2},{'g':'A','x':2,'y':4},{'g':'B','x':3,'y':6},{'g':'B','x':100,'y':200},{'g':'B','x':None,'y':None}])
def test_scalars():assert mean([1,2,3])==2 and median([1,2,3,4])==2.5 and mode([2,1,2])==2
def test_dispersion():assert round(variance([1,2,3]),2)==1 and stddev([1,2,3])==1
def test_cov_corr():assert correlation([1,2,3],[2,4,6])==1
def test_describe():
 d=sample().describe();x=[r for r in d.to_dicts() if r['column']=='x'][0];assert x['count']==4 and x['missing']==1 and x['max']==100
def test_frequency():assert sample().frequencies('g').to_dicts()[0]['count']==3
def test_crosstab():assert sample().crosstab('g','x').row_count==2
def test_rank():assert sample().rank('x').to_dicts()[0]['rank']==1
def test_cumulative():assert DataFrame([{'x':1},{'x':2}]).cumulative('x').to_dicts()[-1]['cum_sum_x']==3
def test_rolling():assert DataFrame([{'x':1},{'x':3}]).rolling('x',2).to_dicts()[-1]['rolling_mean_x']==2
def test_outlier():assert sample().outliers_iqr('x').to_dicts()==[{'g':'B','x':100,'y':200}]
def test_profile():
 p=DataFrame([{'x':1},{'x':1},{'x':None}]).profile();assert p['duplicate_rows']==1 and p['missing_cells']==1
def test_corr_matrix():assert sample().correlation_matrix(['x','y']).to_dicts()[0]['y']==1
def test_quantile_bounds():
 try:quantile([1],2);assert False
 except ValueError:assert True

