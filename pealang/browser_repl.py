
"""Browser-safe REPL protocol and dataset inspector for PeaLang v0.72."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any,Callable
from .data import DataFrame,infer_schema

@dataclass
class BrowserResult:
    ok:bool
    value:Any=None
    output:list[str]|None=None
    error:str|None=None
    diagnostics:list[dict]|None=None
    def to_dict(self): return asdict(self)

class BrowserREPL:
    """Transport-neutral REPL facade. Host supplies execution callback to keep browser capabilities explicit."""
    def __init__(self,executor:Callable[[str],Any]|None=None,max_source_chars=100_000):
        self.executor=executor; self.max_source_chars=max_source_chars; self.history=[]
    def execute(self,source:str):
        if not isinstance(source,str): return BrowserResult(False,error="source must be text")
        if len(source)>self.max_source_chars: return BrowserResult(False,error="source exceeds browser REPL limit")
        self.history.append(source)
        if self.executor is None: return BrowserResult(False,error="no browser-safe executor configured")
        try:
            value=self.executor(source); return BrowserResult(True,value=value,output=[])
        except Exception as exc: return BrowserResult(False,error=str(exc),diagnostics=[{"type":exc.__class__.__name__,"message":str(exc)}])
    def protocol(self,message):
        if message.get("type")=="execute": return {"type":"result","request_id":message.get("request_id"),**self.execute(message.get("source","")).to_dict()}
        if message.get("type")=="history": return {"type":"history","items":list(self.history)}
        return {"type":"error","error":"unsupported message type"}

class DatasetInspector:
    def inspect(self,data,limit=50,offset=0):
        frame=data if isinstance(data,DataFrame) else DataFrame(data)
        rows=frame.to_dicts() if hasattr(frame,"to_dicts") else frame.rows()
        sample=rows[offset:offset+limit]
        return {"row_count":len(rows),"column_count":len(frame.columns),"columns":list(frame.columns),"schema":frame.schema.as_dict(),"offset":offset,"limit":limit,"rows":sample}
    def column_profile(self,data,column):
        frame=data if isinstance(data,DataFrame) else DataFrame(data); rows=frame.to_dicts() if hasattr(frame,"to_dicts") else frame.rows(); vals=[r.get(column) for r in rows]; nonnull=[v for v in vals if v is not None]
        return {"column":column,"count":len(vals),"null_count":len(vals)-len(nonnull),"distinct_count":len({repr(v) for v in nonnull}),"sample":nonnull[:10]}

