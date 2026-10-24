
from pealang.data import *
def test_schema():
 d=DataFrame([{'id':1,'name':'A'}]);assert d.schema.as_dict()=={'id':'Int64','name':'String'}
def test_dataframe_ops():
 d=DataFrame([{'x':2},{'x':1},{'x':2}]);assert d.filter(lambda r:r['x']>1).row_count==2 and d.select(['x']).columns==['x'] and d.distinct().row_count==2
def test_with_column_sort_limit():
 d=DataFrame([{'x':2},{'x':1}]).with_column('y',lambda r:r['x']*2).sort('x').limit(1);assert d.to_dicts()==[{'x':1,'y':2}]
def test_csv_roundtrip(tmp_path):
 p=tmp_path/'x.csv';write(DataFrame([{'a':'1','b':'x'}]),str(p));assert read(str(p)).to_dicts()[0]['b']=='x'
def test_json_roundtrip(tmp_path):
 p=tmp_path/'x.json';write(DataFrame([{'a':1}]),str(p));assert read(str(p)).to_dicts()==[{'a':1}]
def test_jsonl_roundtrip(tmp_path):
 p=tmp_path/'x.jsonl';write(DataFrame([{'a':1},{'a':2}]),str(p));assert read(str(p)).row_count==2
def test_lazy():
 d=LazyFrame(lambda:DataFrame([{'x':1},{'x':2}])).filter(lambda r:r['x']>1).limit(1);assert d.explain()=='scan -> filter -> limit' and d.collect().row_count==1
def test_custom_connector():
 register_connector('custom',lambda p,o:DataFrame([{'path':p}]));assert read('custom://abc').to_dicts()[0]['path']=='abc'
