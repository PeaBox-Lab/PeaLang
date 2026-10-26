


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


# PeaLang 0.43 DataFrame Engine
from collections import defaultdict

@dataclass(frozen=True)
class Expr:
    op:str
    args:tuple=()
    def eval(self,row):
        vals=[a.eval(row) if isinstance(a,Expr) else a for a in self.args]
        if self.op=='col': return row.get(vals[0])
        if self.op=='lit': return vals[0]
        if self.op=='add': return vals[0]+vals[1]
        if self.op=='sub': return vals[0]-vals[1]
        if self.op=='mul': return vals[0]*vals[1]
        if self.op=='div': return vals[0]/vals[1]
        if self.op=='eq': return vals[0]==vals[1]
        if self.op=='gt': return vals[0]>vals[1]
        if self.op=='lt': return vals[0]<vals[1]
        if self.op=='and': return bool(vals[0]) and bool(vals[1])
        if self.op=='or': return bool(vals[0]) or bool(vals[1])
        if self.op=='coalesce': return next((v for v in vals if v is not None),None)
        raise ValueError('Unknown expression: '+self.op)
    def _b(self,op,x):return Expr(op,(self,x if isinstance(x,Expr) else lit(x)))
    def __add__(self,x):return self._b('add',x)
    def __sub__(self,x):return self._b('sub',x)
    def __mul__(self,x):return self._b('mul',x)
    def __truediv__(self,x):return self._b('div',x)
    def __eq__(self,x):return self._b('eq',x)
    def __gt__(self,x):return self._b('gt',x)
    def __lt__(self,x):return self._b('lt',x)

def col(name):return Expr('col',(str(name),))
def lit(value):return Expr('lit',(value,))
def coalesce(*values):return Expr('coalesce',tuple(v if isinstance(v,Expr) else lit(v) for v in values))

def _key(row,keys):return tuple(row.get(k) for k in keys)
def _df_join(self,other,on,how='inner',left_on=None,right_on=None,suffix='_right'):
    left=list(left_on or ([on] if isinstance(on,str) else on));right=list(right_on or left)
    index=defaultdict(list)
    for r in other._rows:index[_key(r,right)].append(r)
    out=[]; matched=set()
    for l in self._rows:
        hits=index.get(_key(l,left),[])
        if hits:
            for r in hits:
                merged=dict(l)
                for k,v in r.items():
                    if k in right and k in left:continue
                    merged[k if k not in merged else k+suffix]=v
                out.append(merged);matched.add(id(r))
        elif how in ('left','outer'):out.append(dict(l))
    if how in ('right','outer'):
        for r in other._rows:
            if id(r) not in matched:out.append(dict(r))
    return DataFrame(out)
def _df_group_by(self,keys):return GroupedDataFrame(self,[keys] if isinstance(keys,str) else list(keys))
class GroupedDataFrame:
    def __init__(self,df,keys):self.df,self.keys=df,keys
    def agg(self,**aggs):
        groups=defaultdict(list)
        for r in self.df._rows:groups[_key(r,self.keys)].append(r)
        out=[]
        for key,rows in groups.items():
            item=dict(zip(self.keys,key))
            for name,spec in aggs.items():
                op,column=(spec if isinstance(spec,tuple) else (spec,name)); vals=[r.get(column) for r in rows if r.get(column) is not None]
                if op=='count':value=len(vals)
                elif op=='sum':value=sum(vals)
                elif op=='min':value=min(vals) if vals else None
                elif op=='max':value=max(vals) if vals else None
                elif op in ('avg','mean'):value=sum(vals)/len(vals) if vals else None
                elif op=='first':value=vals[0] if vals else None
                elif op=='last':value=vals[-1] if vals else None
                else:raise ValueError('Unknown aggregation: '+str(op))
                item[name]=value
            out.append(item)
        return DataFrame(out)
def _df_fill_null(self,value=None,**mapping):
    mp=dict(mapping);return DataFrame([{k:(mp.get(k,value) if v is None else v) for k,v in r.items()} for r in self._rows])
def _df_drop_null(self,columns=None):
    cols=list(columns or self.columns);return DataFrame([r for r in self._rows if all(r.get(k) is not None for k in cols)])
def _df_pivot(self,index,columns,values,agg='first'):
    groups=defaultdict(list)
    for r in self._rows:groups[r.get(index)].append(r)
    out=[]
    for idx,rows in groups.items():
        item={index:idx}
        for r in rows:
            k=str(r.get(columns));v=r.get(values)
            if k not in item or agg=='last':item[k]=v
            elif agg=='sum':item[k]=(item[k] or 0)+(v or 0)
        out.append(item)
    return DataFrame(out)
def _df_unpivot(self,id_columns,value_columns=None,variable_name='variable',value_name='value'):
    ids=[id_columns] if isinstance(id_columns,str) else list(id_columns); vals=list(value_columns or [c for c in self.columns if c not in ids]);out=[]
    for r in self._rows:
        base={k:r.get(k) for k in ids}
        for c in vals:out.append({**base,variable_name:c,value_name:r.get(c)})
    return DataFrame(out)
def _df_with_expr(self,name,expr):return self.with_column(name,lambda r:expr.eval(r) if isinstance(expr,Expr) else expr)
def _df_filter_expr(self,expr):return self.filter(lambda r:bool(expr.eval(r)))
def _df_window(self,partition_by=None,order_by=None,row_number='row_number'):
    parts=defaultdict(list);keys=[] if partition_by is None else ([partition_by] if isinstance(partition_by,str) else list(partition_by))
    for r in self._rows:parts[_key(r,keys)].append(dict(r))
    out=[]
    for rows in parts.values():
        if order_by:rows.sort(key=lambda r:(r.get(order_by) is None,r.get(order_by)))
        for i,r in enumerate(rows,1):r[row_number]=i;out.append(r)
    return DataFrame(out)
DataFrame.join=_df_join;DataFrame.group_by=_df_group_by;DataFrame.fill_null=_df_fill_null;DataFrame.drop_null=_df_drop_null
DataFrame.pivot=_df_pivot;DataFrame.unpivot=_df_unpivot;DataFrame.with_expr=_df_with_expr;DataFrame.filter_expr=_df_filter_expr;DataFrame.window=_df_window

def _lazy_op(self,name,fn):return LazyFrame(lambda:fn(self.collect()),self.plan+[name])
LazyFrame.join=lambda self,other,**kw:_lazy_op(self,'join',lambda d:d.join(other.collect() if isinstance(other,LazyFrame) else other,**kw))
LazyFrame.group_by=lambda self,keys:LazyGroupedFrame(self,keys)
LazyFrame.sort=lambda self,c,descending=False:_lazy_op(self,'sort',lambda d:d.sort(c,descending))
LazyFrame.distinct=lambda self:_lazy_op(self,'distinct',lambda d:d.distinct())
LazyFrame.with_expr=lambda self,n,e:_lazy_op(self,'with_expr',lambda d:d.with_expr(n,e))
LazyFrame.filter_expr=lambda self,e:_lazy_op(self,'filter_expr',lambda d:d.filter_expr(e))
LazyFrame.optimize=lambda self:self
class LazyGroupedFrame:
    def __init__(self,frame,keys):self.frame,self.keys=frame,keys
    def agg(self,**aggs):return _lazy_op(self.frame,'group_by/agg',lambda d:d.group_by(self.keys).agg(**aggs))



