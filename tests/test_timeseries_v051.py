from datetime import datetime
from pealang.data import DataFrame
from pealang.timeseries import *
from pealang.timeseries import _bucket
def test_parse():assert parse_datetime('2026-10-23').year==2026
def test_parts():assert DataFrame([{'d':'2026-10-23'}]).date_parts('d').to_dicts()[0]['d_month']==10
def test_resample():
 d=DataFrame([{'d':'2026-10-01','x':1},{'d':'2026-10-02','x':2},{'d':'2026-11-01','x':3}]);assert d.resample('d','month','x','sum').to_dicts()[0]['sum_x']==3
def test_lag_lead():
 d=DataFrame([{'x':1},{'x':2}]);assert d.lag('x').to_dicts()[1]['lag_x']==1 and d.lead('x').to_dicts()[0]['lead_x']==2
def test_diff_pct():
 d=DataFrame([{'x':10},{'x':15}]);assert d.difference('x').to_dicts()[1]['diff_x']==5 and d.pct_change('x').to_dicts()[1]['pct_change_x']==.5
def test_expanding():assert DataFrame([{'x':1},{'x':3}]).expanding('x').to_dicts()[-1]['expanding_mean_x']==2
def test_ewm():assert DataFrame([{'x':1},{'x':3}]).ewm('x',alpha=.5).to_dicts()[-1]['ewm_x']==2
def test_interpolate():assert DataFrame([{'x':1},{'x':None},{'x':3}]).interpolate('x').to_dicts()[1]['x']==2
def test_grouped_describe():
 d=DataFrame([{'g':'a','x':1},{'g':'a','x':3},{'g':'b','x':4}]);assert d.grouped_describe('g',['x']).row_count==2
def test_grouped_rolling():
 d=DataFrame([{'g':'a','x':1},{'g':'b','x':10},{'g':'a','x':3}]);assert d.grouped_rolling('g','x',2).to_dicts()[-1]['group_rolling_mean_x']==2
def test_bad_frequency():
 try:_bucket(datetime.now(),'bad');assert False
 except ValueError:assert True
def test_bad_ewm():
 try:DataFrame([{'x':1}]).ewm('x',alpha=0);assert False
 except ValueError:assert True

