
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional
from .lexer import Lexer
from .parser import parse_source
from .ast_nodes import *
from .errors import PeaError

@dataclass(frozen=True)
class Location:
    source: str
    line: int
    col: int
    kind: str
    name: str
    def to_dict(self): return asdict(self)

KEYWORDS = sorted({"let","const","print","if","else","while","for","in","function","return","true","false","null","and","or","not","break","continue","import","assert","parallel","try","catch","finally","throw","export","as"})

def diagnostics(source, source_name='<input>'):
    try:
        parse_source(source, source_name)
        return []
    except PeaError as ex:
        return [{'severity':'error','message':ex.message,'source':ex.source_name,
                 'line':ex.span.line if ex.span else 1,'col':ex.span.col if ex.span else 1,
                 'category':getattr(ex,'category','syntax')}]

def symbols(source, source_name='<input>'):
    program=parse_source(source, source_name); out=[]
    def add(name,node,kind):
        if name: out.append(Location(source_name,node.span.line if node.span else 1,node.span.col if node.span else 1,kind,name))
    def walk_stmt(st):
        if isinstance(st,VarDecl): add(st.name,st,'constant' if st.constant else 'variable')
        elif isinstance(st,FunctionStmt):
            add(st.name,st,'function')
            for x in st.body: walk_stmt(x)
        elif isinstance(st,ForStmt):
            add(st.name,st,'variable')
            for x in st.body: walk_stmt(x)
        elif isinstance(st,IfStmt):
            for x in st.then_body: walk_stmt(x)
            for x in (st.else_body or []): walk_stmt(x)
        elif isinstance(st,WhileStmt):
            for x in st.body: walk_stmt(x)
        elif isinstance(st,TryStmt):
            if st.catch_name: add(st.catch_name,st,'variable')
            for seq in (st.try_body,st.catch_body or [],st.finally_body or []):
                for x in seq: walk_stmt(x)
    for st in program.statements: walk_stmt(st)
    return [x.to_dict() for x in out]

def definition(source, name, source_name='<input>'):
    candidates=[x for x in symbols(source,source_name) if x['name']==name]
    return candidates[0] if candidates else None

def completions(source='', prefix=''):
    names=set(KEYWORDS)
    try: names.update(x['name'] for x in symbols(source))
    except PeaError: pass
    return sorted(x for x in names if x.startswith(prefix))

def hover(source, name, source_name='<input>'):
    hit=definition(source,name,source_name)
    return None if hit is None else {'name':name,'kind':hit['kind'],'location':hit}
