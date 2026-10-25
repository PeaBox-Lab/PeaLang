

"""Declarative dashboard model and safe React renderer for PeaLang v0.71."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import json, re

_ALLOWED={"metric","table","line","bar","area","pie","text","filter"}
@dataclass(frozen=True)
class DashboardComponent:
    kind:str; title:str; source:str|None=None; x:str|None=None; y:str|None=None; value:str|None=None; options:dict[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if self.kind not in _ALLOWED: raise ValueError(f"Unsupported component kind: {self.kind}")

@dataclass
class Dashboard:
    title:str
    components:list[DashboardComponent]=field(default_factory=list)
    theme:str="light"
    def add(self,kind,title,**kwargs): self.components.append(DashboardComponent(kind,title,**kwargs)); return self
    def to_dict(self): return {"title":self.title,"theme":self.theme,"components":[asdict(c) for c in self.components]}

def dashboard_from_dict(spec):
    dash=Dashboard(spec["title"],theme=spec.get("theme","light"))
    for item in spec.get("components",[]): dash.add(**item)
    return dash

def render_react(dashboard:Dashboard,component_name="PeaDashboard"):
    if not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*",component_name): raise ValueError("Invalid React component name")
    spec=json.dumps(dashboard.to_dict(),ensure_ascii=False).replace("</","<\\/")
    return f'''import React from "react";\n\nconst spec = {spec};\n\nexport default function {component_name}({{ data = {{}} }}) {{\n  return (\n    <main className={{`pea-dashboard pea-theme-${{spec.theme}}`}}>\n      <h1>{{spec.title}}</h1>\n      <section className="pea-grid">\n        {{spec.components.map((c, i) => (\n          <article className={{`pea-card pea-${{c.kind}}`}} key={{`${{c.title}}-${{i}}`}}>\n            <h2>{{c.title}}</h2>\n            <pre>{{JSON.stringify(c.source ? data[c.source] : c.options, null, 2)}}</pre>\n          </article>\n        ))}}\n      </section>\n    </main>\n  );\n}}\n'''


# v0.72 interactive dashboard controls and bindings
@dataclass(frozen=True)
class DashboardFilter:
    name:str
    field:str
    kind:str="select"
    default:Any=None
    options:tuple[Any,...]=()
    def __post_init__(self):
        if self.kind not in {"select","multi","text","number","date","range"}: raise ValueError(f"Unsupported filter kind: {self.kind}")

@dataclass
class DashboardState:
    filters:dict[str,Any]=field(default_factory=dict)
    selections:dict[str,Any]=field(default_factory=dict)
    page:int=1
    page_size:int=50
    def set_filter(self,name,value): self.filters[name]=value; return self
    def select(self,component,value): self.selections[component]=value; return self

@dataclass(frozen=True)
class DataBinding:
    source:str
    x:str|None=None
    y:str|None=None
    series:str|None=None
    columns:tuple[str,...]=()

def apply_dashboard_filters(rows,filters,state):
    out=list(rows)
    for f in filters:
        value=state.filters.get(f.name,f.default)
        if value is None or value=="": continue
        if f.kind=="multi":
            allowed=set(value if isinstance(value,(list,tuple,set)) else [value]); out=[r for r in out if r.get(f.field) in allowed]
        elif f.kind=="range":
            lo,hi=value; out=[r for r in out if r.get(f.field) is not None and (lo is None or r.get(f.field)>=lo) and (hi is None or r.get(f.field)<=hi)]
        elif f.kind=="text": out=[r for r in out if str(value).lower() in str(r.get(f.field,"")).lower()]
        else: out=[r for r in out if r.get(f.field)==value]
    return out


