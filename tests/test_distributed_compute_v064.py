import pytest
from pealang.data import DataFrame
from pealang.distributed_compute import *
def s():return DataFrame([{'g':'a','x':2},{'g':'a','x':1},{'g':'b','x':3}])
def test_registry():assert set(ENGINES.names())=={'local','arrow','polars','spark'}
def test_pipeline():
 r,e=distributed(s()).with_engine('local').sort('x').limit(2).collect(True);assert e=='local' and [x['x'] for x in r.to_dicts()]==[1,2]
def test_distinct():assert distributed(s()).with_engine('local').select('g').distinct().collect().row_count==2
def test_group():assert distributed(s()).with_engine('local').group_by('g',total=('sum','x')).collect().row_count==2
def test_explain():assert distributed(s()).with_engine('local').explain()['engine']=='local'
def test_missing():
 with pytest.raises(KeyError):ENGINES.get('missing')
