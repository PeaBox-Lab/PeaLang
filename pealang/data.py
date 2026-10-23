"""PeaLang Data Foundation 0.42, dependency-light tabular core."""
from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
from typing import Any,Iterable,Callable
import csv,json
@dataclass(frozen=True)
class DataType:
 name:str
 nullable:bool=True
@dataclass(frozen=True)
class Field:
 name:str
 dtype:DataType
@dataclass(frozen=True)
class Schema:
 fields:tuple[Field,...]
 def names(self):return [x.name for x in self.fields]
 def as_dict(self):return {x.name:x.dtype.name for x in self.fields}
def infer_type(v):
 if v is None:return DataType('Null')
 if isinstance(v,bool):return DataType('Bool')
 if isinstance(v,int):return DataType('Int64')
 if isinstance(v,float):return DataType('Float64')
 if isinstance(v,(bytes,bytearray)):return DataType('Binary')
 if isinstance(v,list):return DataType('List')
 if isinstance(v,dict):return DataType('Struct')
 return DataType('String')
def infer_schema(rows):
 rows=list(rows);names=[]
 for row in rows:
  for k in row:
   if k not in names:names.append(k)
 fields=[]
 for n in names:
  dtype=DataType('Null')
  for row in rows:
   if row.get(n) is not None:dtype=infer_type(row[n]);break
  fields.append(Field(n,dtype))
 return Schema(tuple(fields))
class DataFrame:
 def __init__(self,rows=(),schema=None):self._rows=[dict(x) for x in rows];self.schema=schema or infer_schema(self._rows)
 @property
 def row_count(self):return len(self._rows)
 @property
 def columns(self):return self.schema.names()
 def rows(self):return [dict(x) for x in self._rows]
 def select(self,columns):return DataFrame([{k:row.get(k) for k in columns} for row in self._rows])
 def filter(self,predicate):return DataFrame([row for row in self._rows if predicate(row)],self.schema)
 def with_column(self,name,value):
  return DataFrame([{**row,name:(value(row) if callable(value) else value)} for row in self._rows])
 def drop(self,columns):
  drop=set(columns);return DataFrame([{k:v for k,v in row.items() if k not in drop} for row in self._rows])
 def rename(self,mapping):return DataFrame([{mapping.get(k,k):v for k,v in row.items()} for row in self._rows])
 def sort(self,column,descending=False):return DataFrame(sorted(self._rows,key=lambda x:(x.get(column) is None,x.get(column)),reverse=descending),self.schema)
 def limit(self,n):return DataFrame(self._rows[:int(n)],self.schema)
 def distinct(self):
  out=[];seen=set()
  for row in self._rows:
   key=json.dumps(row,sort_keys=True,default=str)
   if key not in seen:seen.add(key);out.append(row)
  return DataFrame(out,self.schema)
 def collect(self):return self
 def to_dicts(self):return self.rows()
class LazyFrame:
 def __init__(self,loader,plan=None):self.loader=loader;self.plan=list(plan or [])
 def _op(self,name,fn):return LazyFrame(lambda:fn(self.collect()),self.plan+[name])
 def select(self,c):return self._op('select',lambda d:d.select(c))
 def filter(self,f):return self._op('filter',lambda d:d.filter(f))
 def limit(self,n):return self._op('limit',lambda d:d.limit(n))
 def collect(self):
  x=self.loader();return x.collect() if isinstance(x,LazyFrame) else x
 def explain(self):return ' -> '.join(['scan']+self.plan)
@dataclass(frozen=True)
class ConnectorSpec:
 scheme:str;read:Callable;write:Callable|None=None;capabilities:tuple[str,...]=('read',)
class ConnectorRegistry:
 def __init__(self):self._items={}
 def register(self,spec):self._items[spec.scheme]=spec;return self
 def get(self,scheme):
  if scheme not in self._items:raise ValueError(f'Unknown data connector: {scheme}')
  return self._items[scheme]
 def schemes(self):return sorted(self._items)
REGISTRY=ConnectorRegistry()
def _csv_read(path,options):
 with Path(path).open(newline='',encoding=options.get('encoding','utf-8-sig')) as f:return DataFrame(list(csv.DictReader(f)))
def _csv_write(path,data,options):
 rows=data.to_dicts();p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
 names=data.columns
 with p.open('w',newline='',encoding=options.get('encoding','utf-8')) as f:
  w=csv.DictWriter(f,fieldnames=names);w.writeheader();w.writerows(rows)
 return str(p)
def _json_read(path,options):
 value=json.loads(Path(path).read_text(encoding='utf-8'));return DataFrame(value if isinstance(value,list) else [value])
def _json_write(path,data,options):Path(path).write_text(json.dumps(data.to_dicts(),indent=options.get('indent',2),default=str)+'\n');return str(path)
def _jsonl_read(path,options):return DataFrame([json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()])
def _jsonl_write(path,data,options):Path(path).write_text(''.join(json.dumps(x,default=str)+'\n' for x in data.to_dicts()));return str(path)
for spec in [ConnectorSpec('csv',_csv_read,_csv_write,('read','write','scan')),ConnectorSpec('json',_json_read,_json_write,('read','write')),ConnectorSpec('jsonl',_jsonl_read,_jsonl_write,('read','write','scan'))]:REGISTRY.register(spec)
def parse_uri(uri):
 if '://' in uri:return uri.split('://',1)
 p=Path(uri);return p.suffix.lower().lstrip('.'),str(p)
def read(uri,**options):scheme,path=parse_uri(str(uri));return REGISTRY.get(scheme).read(path,options)
def write(data,uri,**options):
 scheme,path=parse_uri(str(uri));spec=REGISTRY.get(scheme)
 if not spec.write:raise ValueError(f'{scheme} is read-only')
 return spec.write(path,data,options)
def scan(uri,**options):return LazyFrame(lambda:read(uri,**options))
def register_connector(scheme,read_fn,write_fn=None,capabilities=('read',)):return REGISTRY.register(ConnectorSpec(scheme,read_fn,write_fn,tuple(capabilities)))
