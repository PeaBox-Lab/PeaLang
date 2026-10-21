from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from .ast_nodes import *
from .errors import PeaError
from .lexer import Lexer
from .parser import parse_source

@dataclass
class Diagnostic:
    severity:str; code:str; message:str; line:int=1; col:int=1
    def render(self,path='<input>'): return f'{path}:{self.line}:{self.col}: {self.severity} {self.code}: {self.message}'

KEYWORD_TEXT={'LET':'let','CONST':'const','PRINT':'print','IF':'if','ELSE':'else','WHILE':'while','FOR':'for','IN':'in','FUNCTION':'function','RETURN':'return','TRUE':'true','FALSE':'false','NULL':'null','AND':'and','OR':'or','NOT':'not','BREAK':'break','CONTINUE':'continue','IMPORT':'import','ASSERT':'assert','PARALLEL':'parallel','TRY':'try','CATCH':'catch','FINALLY':'finally','THROW':'throw'}

def format_source(source:str)->str:
    tokens=Lexer(source).tokens();out=[];line='';indent=0
    def emit(text,space=True):
        nonlocal line
        if not line: line='    '*indent+text
        elif space: line+=' '+text
        else: line+=text
    def flush():
        nonlocal line
        if line.strip():out.append(line.rstrip())
        line=''
    prev=None
    for t in tokens:
        k=t.kind
        if k=='EOF':break
        if k in ('NEWLINE',';'):flush();prev=k;continue
        if k=='}':
            flush();indent=max(0,indent-1);emit('}',False);prev=k;continue
        if k=='{':emit('{');flush();indent+=1;prev=k;continue
        if k==',':emit(',',False);prev=k;continue
        if k=='.':emit('.',False);prev=k;continue
        if k in (')',']'):emit(k,False);prev=k;continue
        if k in ('(', '['):
            no_space=prev in ('IDENT',')',']')
            emit(k,not no_space);prev=k;continue
        if k==':':emit(':',False);prev=k;continue
        if k=='STRING':
            text='"'+str(t.value).replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')+'"'
        elif k=='NUMBER':text=str(t.value)
        else:text=KEYWORD_TEXT.get(k,str(t.value))
        no_space=prev in ('(','[','.',':')
        emit(text,not no_space);prev=k
    flush();return '\n'.join(out).strip()+'\n'

def format_file(path,check=False):
    p=Path(path);original=p.read_text(encoding='utf-8');formatted=format_source(original)
    if check:return original==formatted
    p.write_text(formatted,encoding='utf-8');return True

class Checker:
    BUILTINS={'range','len','str','number','int','type','upper','lower','split','join','append','keys','values','json','read','write','exists','sqrt','round','sleep','file','path','csv','env','datetime','regex','http','process','task','workflow','ai','skill','agent','tool'}
    def __init__(self):self.diags=[];self.scopes=[set(self.BUILTINS)];self.used=set();self.declared={}
    def add(self,code,msg,node,severity='warning'):
        span=getattr(node,'span',None);self.diags.append(Diagnostic(severity,code,msg,span.line if span else 1,span.col if span else 1))
    def defined(self,n):return any(n in s for s in reversed(self.scopes))
    def check(self,program):
        for s in program.statements:self.stmt(s)
        for name,node in getattr(self,'declared',{}).items():
            if name not in self.used and not name.startswith('_'):self.add('P104',f"Unused variable '{name}'",node)
        return self.diags
    declared={}
    def declare(self,n,node):
        if n in self.scopes[-1]:self.add('P102',f"Duplicate declaration '{n}'",node,'error')
        self.scopes[-1].add(n);self.declared=dict(getattr(self,'declared',{}));self.declared[n]=node
    def stmt(self,s):
        if isinstance(s,VarDecl):self.expr(s.value);self.declare(s.name,s)
        elif isinstance(s,Assign):self.expr(s.target);self.expr(s.value)
        elif isinstance(s,(PrintStmt,ExprStmt)):self.expr(s.value)
        elif isinstance(s,IfStmt):self.expr(s.condition);self.block(s.then_body);self.block(s.else_body or [])
        elif isinstance(s,WhileStmt):self.expr(s.condition);self.block(s.body)
        elif isinstance(s,ForStmt):self.expr(s.iterable);self.scopes.append({s.name});self.block(s.body,new_scope=False);self.scopes.pop()
        elif isinstance(s,FunctionStmt):
            self.declare(s.name,s);self.scopes.append(set(p.name for p in s.params));[self.expr(p.default) for p in s.params if p.default is not None];self.block(s.body,new_scope=False);self.scopes.pop()
        elif isinstance(s,ReturnStmt) and s.value:self.expr(s.value)
        elif isinstance(s,AssertStmt):self.expr(s.condition);self.expr(s.message)
        elif isinstance(s,ThrowStmt):self.expr(s.value)
        elif isinstance(s,TryStmt):
            self.block(s.try_body);self.scopes.append({s.catch_name} if s.catch_name else set());self.block(s.catch_body or [],new_scope=False);self.scopes.pop();self.block(s.finally_body or [])
    def block(self,body,new_scope=True):
        if new_scope:self.scopes.append(set())
        for s in body:self.stmt(s)
        if new_scope:self.scopes.pop()
    def expr(self,e):
        if e is None:return
        if isinstance(e,Variable):
            self.used.add(e.name)
            if not self.defined(e.name):self.add('P101',f"Undefined variable '{e.name}'",e,'error')
        elif isinstance(e,(Unary,)):self.expr(e.value)
        elif isinstance(e,Binary):self.expr(e.left);self.expr(e.right)
        elif isinstance(e,(Index,)):self.expr(e.target);self.expr(e.index)
        elif isinstance(e,Property):self.expr(e.target)
        elif isinstance(e,Call):self.expr(e.callee);[self.expr(x) for x in e.args]
        elif isinstance(e,ListExpr):[self.expr(x) for x in e.items]
        elif isinstance(e,DictExpr):[(self.expr(k),self.expr(v)) for k,v in e.pairs]
        elif isinstance(e,InterpolatedString):[self.expr(x) for x in e.parts if not isinstance(x,str)]
        elif isinstance(e,ParallelExpr):[self.expr(x) for x in e.expressions]

def check_source(source,source_name='<input>'):
    try:return Checker().check(parse_source(source,source_name))
    except PeaError as e:
        span=e.span;return [Diagnostic('error','P100',e.message,span.line if span else 1,span.col if span else 1)]

def discover_pea(paths:Iterable[str]):
    found=[]
    for raw in paths:
        p=Path(raw)
        if p.is_dir():found.extend(sorted(p.rglob('*.pea')))
        elif p.suffix=='.pea':found.append(p)
    return found

def generate_docs(source,path='<input>'):
    program=parse_source(source,path);lines=[f'# API reference: {Path(path).name}','']
    funcs=[s for s in program.statements if isinstance(s,FunctionStmt)]
    if not funcs:lines.append('No public functions found.')
    for f in funcs:
        if f.name.startswith('_'):continue
        lines += [f'## `{f.name}({", ".join(p.name + ("=?" if p.default is not None else "") for p in f.params)})`','',f'Defined at line {f.span.line if f.span else "?"}.','']
    return '\n'.join(lines).rstrip()+'\n'
