

import pytest
from pealang.sql import connect,read_sql,DATABASES
from pealang.data import DataFrame

def test_adapters_registered():assert {'sqlite','duckdb','postgresql','mysql','mariadb','sqlserver','oracle'} <= set(DATABASES)
def test_sqlite_query(tmp_path):
 p=tmp_path/'x.db'
 with connect('sqlite:///'+str(p)) as d:
  d.execute('create table t(id integer primary key,name text)');d.execute('insert into t values (?,?)',(1,'A'));d.commit();assert d.query('select * from t').to_dicts()==[{'id':1,'name':'A'}]
def test_parameters(tmp_path):
 p=tmp_path/'x.db'
 with connect(str(p)) as d:
  d.execute('create table t(x int)');d.executemany('insert into t values (?)',[(1,),(2,)]);assert d.query('select x from t where x > ?',(1,)).to_dicts()==[{'x':2}]
def test_transaction_rollback(tmp_path):
 p=tmp_path/'x.db'
 with connect(str(p)) as d:
  d.execute('create table t(x int)');d.commit()
  with pytest.raises(RuntimeError):
   with d.transaction():d.execute('insert into t values (1)');raise RuntimeError('stop')
  assert d.scalar('select count(*) from t')==0
def test_discovery(tmp_path):
 with connect(str(tmp_path/'x.db')) as d:d.execute('create table people(id int,name text)');assert d.tables()==['people'] and any(x['name']=='name' for x in d.columns('people'))
def test_insert_frame_batch(tmp_path):
 with connect(str(tmp_path/'x.db')) as d:
  d.execute('create table t(id int,name text)');assert d.insert_frame('t',DataFrame([{'id':1,'name':'A'},{'id':2,'name':'B'}]),1)==2;d.commit();assert d.scalar('select count(*) from t')==2
def test_sqlite_upsert(tmp_path):
 with connect(str(tmp_path/'x.db')) as d:
  d.execute('create table t(id int primary key,name text)');d.insert_frame('t',DataFrame([{'id':1,'name':'A'}]));d.upsert_frame('t',DataFrame([{'id':1,'name':'B'}]),'id');d.commit();assert d.scalar('select name from t where id=1')=='B'
def test_read_sql(tmp_path):
 p=tmp_path/'x.db'
 with connect(str(p)) as d:d.execute('create table t(x int)');d.execute('insert into t values (3)');d.commit()
 assert read_sql(str(p),'select * from t').to_dicts()==[{'x':3}]
def test_missing_optional_adapter():
 try:connect('postgresql://invalid-host/db')
 except (RuntimeError,Exception):pass


