


"""Jupyter kernel protocol foundation and rich display helpers for PeaLang v0.72."""
from __future__ import annotations
from dataclasses import dataclass
from html import escape
from typing import Any,Callable
import json
from .data import DataFrame

@dataclass
class RichResult:
    data:dict[str,Any]
    metadata:dict[str,Any]
    execution_count:int|None=None

class RichDisplay:
    @staticmethod
    def dataframe(frame:DataFrame,limit=100):
        rows=frame.to_dicts() if hasattr(frame,"to_dicts") else frame.rows(); cols=list(frame.columns); shown=rows[:limit]
        head="".join(f"<th>{escape(str(c))}</th>" for c in cols)
        body="".join("<tr>"+"".join(f"<td>{escape(str(r.get(c,'')))}</td>" for c in cols)+"</tr>" for r in shown)
        html=f'<table class="pealang-dataframe"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'
        text="\n".join("\t".join(str(r.get(c,"")) for c in cols) for r in shown)
        return RichResult({"text/plain":text,"text/html":html,"application/vnd.pealang.dataframe+json":{"columns":cols,"rows":shown,"row_count":len(rows)}},{})
    @staticmethod
    def value(value):
        if isinstance(value,DataFrame): return RichDisplay.dataframe(value)
        return RichResult({"text/plain":repr(value),"application/json":value if isinstance(value,(dict,list,str,int,float,bool,type(None))) else str(value)},{})

class PeaKernel:
    implementation="pealang"; implementation_version="0.72.0"; language="pealang"
    language_info={"name":"pealang","mimetype":"text/x-pealang","file_extension":".pea"}
    def __init__(self,executor:Callable[[str],Any]|None=None): self.executor=executor; self.execution_count=0
    @property
    def kernel_info(self): return {"implementation":self.implementation,"implementation_version":self.implementation_version,"language_info":self.language_info,"banner":"PeaLang 0.72"}
    def execute(self,code,silent=False):
        self.execution_count+=1
        if self.executor is None: return {"status":"error","ename":"RuntimeError","evalue":"no kernel executor configured","execution_count":self.execution_count}
        try:
            value=self.executor(code); rich=RichDisplay.value(value)
            return {"status":"ok","execution_count":self.execution_count,"payload":[],"user_expressions":{},"display_data":None if silent else rich.data,"metadata":rich.metadata}
        except Exception as exc: return {"status":"error","ename":exc.__class__.__name__,"evalue":str(exc),"execution_count":self.execution_count}

def kernelspec():
    return {"argv":["python","-m","pealang.jupyter_kernel","-f","{connection_file}"],"display_name":"PeaLang","language":"pealang"}



