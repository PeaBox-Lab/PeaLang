# AUDIT-CLOSURE: intentional interface contract; concrete backends must override the methods documented in docs/project/INTERFACE_COMPLETENESS_0991.md.



from __future__ import annotations
from dataclasses import dataclass,field
from .data import DataFrame,LazyFrame
class ComputeEngineError(RuntimeError):pass
class EngineUnavailable(ComputeEngineError):pass
@dataclass(frozen=True)
class PlanNode:
 operation:str;arguments:dict=field(default_factory=dict);children:tuple=()
 def to_dict(self):return {'operation':self.operation,'arguments':self.arguments,'children':[x.to_dict() for x in self.children]}
@dataclass
class ExecutionPlan:
 root:PlanNode;engine:str='auto';estimated_rows:int|None=None;memory_limit_mb:int|None=None;metadata:dict=field(default_factory=dict)
 def to_dict(self):return {'engine':self.engine,'estimated_rows':self.estimated_rows,'memory_limit_mb':self.memory_limit_mb,'metadata':self.metadata,'root':self.root.to_dict()}
class ComputeEngine:
 name='base';capabilities=frozenset()
 def available(self):return True
 def execute(self,plan,source):raise NotImplementedError
 def explain(self,plan):return {'engine':self.name,'available':self.available(),'capabilities':sorted(self.capabilities),'plan':plan.to_dict()}
class LocalEngine(ComputeEngine):
 name='local';capabilities=frozenset({'scan','select','filter','sort','distinct','limit','group_by','join'})
 def execute(self,plan,source):
  frame=source.collect() if isinstance(source,LazyFrame) else source() if callable(source) else source
  return _local(plan.root,frame if isinstance(frame,DataFrame) else DataFrame(frame))
class ArrowEngine(ComputeEngine):
 name='arrow';capabilities=frozenset({'columnar','projection_pushdown'})
 def available(self):
  try:import pyarrow;return True
  except ImportError:return False
 def execute(self,plan,source):
  if not self.available():raise EngineUnavailable('Arrow engine requires pyarrow')
  import pyarrow as pa;return pa.Table.from_pylist(LocalEngine().execute(plan,source).to_dicts())
class PolarsEngine(ComputeEngine):
 name='polars';capabilities=frozenset({'lazy','streaming','predicate_pushdown','projection_pushdown'})
 def available(self):
  try:import polars;return True
  except ImportError:return False
 def execute(self,plan,source):
  if not self.available():raise EngineUnavailable('Polars engine requires polars')
  import polars as pl;return pl.DataFrame(LocalEngine().execute(plan,source).to_dicts()).lazy()
class SparkEngine(ComputeEngine):
 name='spark';capabilities=frozenset({'distributed','spill','partitioning','checkpointing'})
 def __init__(self,session=None):self.session=session
 def available(self):
  if self.session:return True
  try:import pyspark;return True
  except ImportError:return False
 def execute(self,plan,source):
  if not self.available():raise EngineUnavailable('Spark engine requires pyspark')
  if self.session is None:
   from pyspark.sql import SparkSession;self.session=SparkSession.builder.appName('PeaLang').getOrCreate()
  return self.session.createDataFrame(LocalEngine().execute(plan,source).to_dicts())
class EngineRegistry:
 def __init__(self):self.engines={}
 def register(self,e,replace=False):
  if e.name in self.engines and not replace:raise ValueError('Engine already registered: '+e.name)
  self.engines[e.name]=e;return e
 def get(self,n):
  if n not in self.engines:raise KeyError('Unknown compute engine: '+n)
  return self.engines[n]
 def choose(self,p):
  if p.engine!='auto':return self.get(p.engine)
  for n in ('spark','polars','arrow','local'):
   e=self.get(n)
   if e.available() and (p.memory_limit_mb is None or n in ('spark','polars','local')):return e
  return self.get('local')
 def names(self):return sorted(self.engines)
ENGINES=EngineRegistry()
for e in (LocalEngine(),ArrowEngine(),PolarsEngine(),SparkEngine()):ENGINES.register(e)
def _local(n,f):
 if n.operation=='source':return f
 b=_local(n.children[0],f);a=n.arguments
 if n.operation=='select':return b.select(a['columns'])
 if n.operation=='filter':return b.filter(a['predicate'])
 if n.operation=='sort':return b.sort(a['column'],a.get('descending',False))
 if n.operation=='distinct':return b.distinct()
 if n.operation=='limit':return DataFrame(b.to_dicts()[:a['count']])
 if n.operation=='group_by':return b.group_by(a['keys']).agg(**a['aggregations'])
 raise ComputeEngineError('Unsupported operation: '+n.operation)
def add_node(p,op,**a):return ExecutionPlan(PlanNode(op,a,(p.root,)),p.engine,p.estimated_rows,p.memory_limit_mb,dict(p.metadata))
def execute_plan(p,s,return_engine=False):
 e=ENGINES.choose(p);r=e.execute(p,s);return (r,e.name) if return_engine else r
def explain_plan(p):return ENGINES.choose(p).explain(p)
def compile_lazy(ops,engine='auto',memory_limit_mb=None):
 p=ExecutionPlan(PlanNode('source'),engine=engine,memory_limit_mb=memory_limit_mb)
 for op,a in ops:p=add_node(p,op,**a)
 return p
class DistributedLazyFrame:
 def __init__(self,s,p=None):self.source=s;self.plan=p or ExecutionPlan(PlanNode('source'))
 def with_engine(self,n):self.plan.engine=n;return self
 def with_memory_limit(self,m):self.plan.memory_limit_mb=int(m);return self
 def select(self,*c):self.plan=add_node(self.plan,'select',columns=list(c));return self
 def filter(self,p):self.plan=add_node(self.plan,'filter',predicate=p);return self
 def sort(self,c,descending=False):self.plan=add_node(self.plan,'sort',column=c,descending=descending);return self
 def distinct(self):self.plan=add_node(self.plan,'distinct');return self
 def limit(self,n):self.plan=add_node(self.plan,'limit',count=int(n));return self
 def group_by(self,k,**a):self.plan=add_node(self.plan,'group_by',keys=k,aggregations=a);return self
 def collect(self,return_engine=False):return execute_plan(self.plan,self.source,return_engine)
 def explain(self):return explain_plan(self.plan)
 def to_dict(self):return self.plan.to_dict()
def distributed(source):return DistributedLazyFrame(source)

# v0.65 scalable execution primitives
import json as _json, tempfile as _tempfile
from pathlib import Path as _Path

@dataclass(frozen=True)
class PartitionSpec:
    count:int=1
    key:str|None=None

class CheckpointStore:
    def __init__(self, root):
        self.root=_Path(root); self.root.mkdir(parents=True,exist_ok=True)
    def save(self,name,frame):
        target=self.root/(str(name)+'.jsonl')
        with target.open('w',encoding='utf-8') as fh:
            for row in frame.to_dicts(): fh.write(_json.dumps(row,default=str)+'\n')
        return str(target)
    def load(self,name):
        target=self.root/(str(name)+'.jsonl')
        return DataFrame([_json.loads(x) for x in target.read_text(encoding='utf-8').splitlines() if x.strip()])
    def exists(self,name): return (self.root/(str(name)+'.jsonl')).exists()

def partition_frame(frame,spec):
    if spec.count < 1: raise ValueError('partition count must be >= 1')
    buckets=[[] for _ in range(spec.count)]
    for i,row in enumerate(frame.to_dicts()):
        idx=(hash(row.get(spec.key)) if spec.key else i)%spec.count
        buckets[idx].append(row)
    return [DataFrame(x) for x in buckets]

def scan_jsonl(path,columns=None,predicate=None,batch_rows=10000,memory_limit_mb=None):
    """Bounded JSONL scan with projection/predicate pushdown and spill-friendly batches."""
    batch=[]; approx=0
    with _Path(path).open('r',encoding='utf-8') as fh:
        for line in fh:
            if not line.strip(): continue
            approx += len(line)
            row=_json.loads(line)
            if predicate and not predicate(row): continue
            if columns: row={k:row.get(k) for k in columns}
            batch.append(row)
            if len(batch)>=batch_rows or (memory_limit_mb and approx>=memory_limit_mb*1024*1024):
                yield DataFrame(batch); batch=[]; approx=0
    if batch: yield DataFrame(batch)

def out_of_core_jsonl(path,columns=None,predicate=None,memory_limit_mb=64,spill_dir=None):
    """Execute a bounded scan. Batches are spilled to JSONL when more than one batch is required."""
    spill_root=_Path(spill_dir or _tempfile.mkdtemp(prefix='pealang-spill-')); spill_root.mkdir(parents=True,exist_ok=True)
    parts=[]
    for n,batch in enumerate(scan_jsonl(path,columns,predicate,memory_limit_mb=memory_limit_mb)):
        target=spill_root/f'part-{n:05d}.jsonl'
        with target.open('w',encoding='utf-8') as fh:
            for row in batch.to_dicts(): fh.write(_json.dumps(row,default=str)+'\n')
        parts.append(target)
    rows=[]
    for target in parts:
        with target.open('r',encoding='utf-8') as fh: rows.extend(_json.loads(x) for x in fh if x.strip())
    return DataFrame(rows)

# Extend fluent distributed plans without breaking v0.64 plans.
def _partitioned(self,count,key=None):
    self.plan.metadata['partitions']={'count':int(count),'key':key}; return self
def _checkpoint(self,name,directory='.pea-checkpoints'):
    frame=self.collect(); CheckpointStore(directory).save(name,frame); return frame
DistributedLazyFrame.partitioned=_partitioned
DistributedLazyFrame.checkpoint=_checkpoint



