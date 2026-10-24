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
