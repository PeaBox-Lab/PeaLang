



"""Dataset and column lineage for PeaLang v0.71."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from typing import Any, Iterable
import json

@dataclass(frozen=True)
class DatasetRef:
    name: str
    namespace: str = "default"
    kind: str = "dataset"
    metadata: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)
    @property
    def id(self): return f"{self.namespace}.{self.name}"

@dataclass(frozen=True)
class ColumnRef:
    dataset: DatasetRef
    name: str
    data_type: str | None = None
    @property
    def id(self): return f"{self.dataset.id}.{self.name}"

@dataclass(frozen=True)
class LineageEdge:
    source: str
    target: str
    operation: str = "derive"
    expression: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)

class LineageGraph:
    def __init__(self): self.datasets={}; self.columns={}; self.edges=[]
    def add_dataset(self,dataset:DatasetRef): self.datasets[dataset.id]=dataset; return dataset
    def add_column(self,column:ColumnRef): self.add_dataset(column.dataset); self.columns[column.id]=column; return column
    def connect(self,source:DatasetRef|ColumnRef|str,target:DatasetRef|ColumnRef|str,operation="derive",expression=None,metadata=None):
        sid=source.id if hasattr(source,"id") else str(source); tid=target.id if hasattr(target,"id") else str(target)
        self.edges.append(LineageEdge(sid,tid,operation,expression,metadata or {})); return self
    def upstream(self,node:str,transitive=True): return self._walk(node,reverse=True,transitive=transitive)
    def downstream(self,node:str,transitive=True): return self._walk(node,reverse=False,transitive=transitive)
    def _walk(self,node,reverse,transitive):
        links=defaultdict(list)
        for edge in self.edges:
            a,b=(edge.target,edge.source) if reverse else (edge.source,edge.target); links[a].append(b)
        found=[]; seen={node}; q=deque([node])
        while q:
            cur=q.popleft()
            for nxt in links[cur]:
                if nxt not in seen:
                    seen.add(nxt); found.append(nxt)
                    if transitive: q.append(nxt)
        return found
    def impact(self,node:str): return {"node":node,"downstream":self.downstream(node),"count":len(self.downstream(node))}
    def validate(self):
        nodes=set(self.datasets)|set(self.columns); missing=sorted({x for e in self.edges for x in (e.source,e.target) if x not in nodes})
        return {"valid":not missing,"missing_nodes":missing,"edge_count":len(self.edges)}
    def to_dict(self):
        return {"datasets":[{"id":k,**asdict(v)} for k,v in self.datasets.items()],"columns":[{"id":k,"dataset":v.dataset.id,"name":v.name,"data_type":v.data_type} for k,v in self.columns.items()],"edges":[asdict(e) for e in self.edges]}
    def to_json(self,indent=2): return json.dumps(self.to_dict(),indent=indent,default=str)




