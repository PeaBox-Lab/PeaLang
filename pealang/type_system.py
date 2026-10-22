"""Optional static type system and source-to-runtime annotation erasure."""
from __future__ import annotations
from dataclasses import dataclass,field
import re
from typing import Any

BUILTINS={'Any','Never','Null','Bool','Int','Float','Number','String','List','Map','Set','Tuple','Result','Option','Future','Function'}
@dataclass(frozen=True)
class TypeRef:
    name:str
    args:tuple['TypeRef',...]=()
    nullable:bool=False
    def __str__(self):
        base=self.name+(f"<{', '.join(map(str,self.args))}>" if self.args else '')
        return base+('?' if self.nullable else '')
@dataclass(frozen=True)
class Diagnostic:
    code:str;message:str;line:int;column:int=1;severity:str='error'
    def __str__(self):return f'{self.severity} {self.code} {self.line}:{self.column} {self.message}'
@dataclass
class TypeCheckResult:
    diagnostics:list[Diagnostic]=field(default_factory=list)
    symbols:dict[str,TypeRef]=field(default_factory=dict)
    records:dict[str,dict[str,TypeRef]]=field(default_factory=dict)
    @property
    def ok(self):return not any(x.severity=='error' for x in self.diagnostics)

TOKEN=re.compile(r'\s*(?:(\w+)|([<>,|?{}:]))')
def parse_type(text:str)->TypeRef:
    text=text.strip()
    if '|' in text:
        parts=tuple(parse_type(x) for x in split_top(text,'|'));return TypeRef('Union',parts)
    nullable=text.endswith('?')
    if nullable:text=text[:-1].strip()
    m=re.fullmatch(r'([A-Za-z_]\w*)\s*(?:<(.*)>)?',text)
    if not m:raise ValueError(f'Invalid type: {text}')
    args=tuple(parse_type(x) for x in split_top(m.group(2),',')) if m.group(2) else ()
    return TypeRef(m.group(1),args,nullable)
def split_top(text,sep):
    out=[];start=depth=0
    for i,ch in enumerate(text):
        depth+= ch=='<';depth-= ch=='>'
        if ch==sep and depth==0:out.append(text[start:i].strip());start=i+1
    out.append(text[start:].strip());return [x for x in out if x]
def infer_literal(text:str)->TypeRef:
    t=text.strip()
    if t=='null':return TypeRef('Null')
    if t in ('true','false'):return TypeRef('Bool')
    if re.fullmatch(r'-?\d+',t):return TypeRef('Int')
    if re.fullmatch(r'-?\d+\.\d+',t):return TypeRef('Float')
    if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):return TypeRef('String')
    if t.startswith('['):return TypeRef('List',(TypeRef('Any'),))
    if t.startswith('{'):return TypeRef('Map',(TypeRef('String'),TypeRef('Any')))
    return TypeRef('Any')
def compatible(expected:TypeRef,actual:TypeRef)->bool:
    if expected.name=='Any' or actual.name=='Any':return True
    if actual.name=='Null':return expected.nullable or expected.name in ('Null','Option')
    if expected.name=='Number' and actual.name in ('Int','Float','Number'):return True
    if expected.name=='Union':return any(compatible(x,actual) for x in expected.args)
    return expected.name==actual.name

class TypeChecker:
    def check(self,source:str,source_name='<input>')->TypeCheckResult:
        r=TypeCheckResult();known=set(BUILTINS)
        # record declarations, one-line or multiline
        for m in re.finditer(r'type\s+(\w+)\s*=\s*\{(.*?)\}',source,re.S):
            name,body=m.group(1),m.group(2);fields={}
            for f in body.split(','):
                if ':' in f:
                    n,t=f.split(':',1)
                    try:fields[n.strip()]=parse_type(t.strip())
                    except ValueError as e:r.diagnostics.append(Diagnostic('P100',str(e),source[:m.start()].count('\n')+1))
            r.records[name]=fields;known.add(name)
        for ln,line in enumerate(source.splitlines(),1):
            clean=line.split('//',1)[0].strip()
            # Typed declaration: let x: Type = value
            m=re.match(r'(?:let|const)\s+(\w+)\s*:\s*([^=]+?)(?:\s*=\s*(.+))?$',clean)
            if m:
                name,raw,value=m.groups()
                try:t=parse_type(raw.strip());r.symbols[name]=t
                except ValueError as e:r.diagnostics.append(Diagnostic('P100',str(e),ln));continue
                self._validate_type(t,known,r,ln)
                if value:
                    actual=infer_literal(value)
                    if not (t.name in r.records and actual.name=='Map') and not compatible(t,actual):r.diagnostics.append(Diagnostic('T201',f"Cannot assign {actual} to {t} variable '{name}'",ln))
                continue
            # Untyped declaration
            m=re.match(r'(?:let|const)\s+(\w+)\s*=\s*(.+)$',clean)
            if m:r.symbols[m.group(1)]=infer_literal(m.group(2));continue
            # Assignment to known symbol
            m=re.match(r'(\w+)\s*=\s*(.+)$',clean)
            if m and m.group(1) in r.symbols:
                actual=infer_literal(m.group(2));expected=r.symbols[m.group(1)]
                if not compatible(expected,actual):r.diagnostics.append(Diagnostic('T202',f"Cannot assign {actual} to {expected} variable '{m.group(1)}'",ln))
            # Function signature validation
            m=re.match(r'function\s+(\w+)\s*\((.*?)\)\s*(?:->\s*([^\{]+))?',clean)
            if m:
                for p in split_top(m.group(2),','):
                    if ':' in p:
                        _,raw=p.split(':',1);raw=raw.split('=',1)[0].strip()
                        try:self._validate_type(parse_type(raw),known,r,ln)
                        except ValueError as e:r.diagnostics.append(Diagnostic('P100',str(e),ln))
                if m.group(3):
                    try:self._validate_type(parse_type(m.group(3).strip()),known,r,ln)
                    except ValueError as e:r.diagnostics.append(Diagnostic('P100',str(e),ln))
        return r
    def _validate_type(self,t,known,r,line):
        if t.name=='Union':
            for x in t.args:self._validate_type(x,known,r,line)
        elif t.name not in known:r.diagnostics.append(Diagnostic('T101',f"Unknown type '{t.name}'",line))
        for x in t.args:self._validate_type(x,known,r,line)

def erase_types(source:str)->str:
    # Remove record declarations before runtime parsing.
    source=re.sub(r'(?ms)^\s*type\s+\w+\s*=\s*\{.*?\}\s*','',source)
    # Function return annotations.
    source=re.sub(r'(function\s+\w+\s*\([^)]*\))\s*->\s*[A-Za-z_]\w*(?:\s*<[^>{}]+>)?\??',r'\1',source)
    # Parameter annotations, preserving defaults and separators.
    def params(m):
        inner=re.sub(r'(\b\w+)\s*:\s*[A-Za-z_]\w*(?:\s*<[^,)=]+>)?\??',r'\1',m.group(1))
        return '('+inner+')'
    source=re.sub(r'\(([^()]*)\)',params,source)
    # Variable annotations.
    source=re.sub(r'\b(let|const)\s+(\w+)\s*:\s*[A-Za-z_]\w*(?:\s*<[^=\n]+>)?\??\s*=',r'\1 \2 =',source)
    return source
