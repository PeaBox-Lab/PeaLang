



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
    # Remove protocol declarations and generic parameter lists before runtime parsing.
    source=re.sub(r'(?ms)^\s*protocol\s+\w+\s*=*\s*\{.*?\}\s*','',source)
    source=re.sub(r'(function\s+\w+)\s*<[^>]+>',r'\1',source)
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

@dataclass
class FunctionContract:
    name:str
    params:list[tuple[str,TypeRef]]
    return_type:TypeRef
    line:int

@dataclass
class SemanticResult(TypeCheckResult):
    functions:dict[str,FunctionContract]=field(default_factory=dict)

class SemanticAnalyzer:
    """Flow-aware semantic checks layered over the optional type surface."""
    def analyze(self,source:str,source_name='<input>')->SemanticResult:
        base=TypeChecker().check(source,source_name)
        result=SemanticResult(base.diagnostics,base.symbols,base.records,{})
        known=set(BUILTINS)|set(result.records)
        lines=source.splitlines()
        # Collect function contracts and bodies using brace depth.
        i=0
        while i<len(lines):
            line=lines[i];m=re.search(r'function\s+(\w+)\s*\((.*?)\)\s*(?:->\s*([^\{]+))?\s*\{',line)
            if not m:i+=1;continue
            name,raw_params,raw_ret=m.groups();params=[]
            for item in split_top(raw_params,','):
                item=item.strip()
                if not item:continue
                pname=item.split(':',1)[0].split('=',1)[0].strip();ptype=TypeRef('Any')
                if ':' in item:
                    ptype=parse_type(item.split(':',1)[1].split('=',1)[0].strip())
                params.append((pname,ptype))
            ret=parse_type(raw_ret.strip()) if raw_ret else TypeRef('Any')
            result.functions[name]=FunctionContract(name,params,ret,i+1)
            depth=line.count('{')-line.count('}');body=[];j=i+1
            while j<len(lines) and depth>0:
                depth+=lines[j].count('{')-lines[j].count('}')
                if depth>0:body.append((j+1,lines[j]))
                j+=1
            self._check_function(name,params,ret,body,result,known)
            i=j
        self._check_records(source,result)
        self._check_calls(source,result)
        return result

    def _check_function(self,name,params,ret,body,r,known):
        env=dict(r.symbols);env.update(params);has_return=False;terminated=False
        for line,text in body:
            clean=text.strip()
            if terminated and clean and clean!='}':r.diagnostics.append(Diagnostic('F401','Unreachable code',line,severity='warning'))
            if clean.startswith('return'):
                has_return=True;expr=clean[6:].strip();actual=self.infer_expr(expr,env,r)
                if ret.name!='Any' and not compatible(ret,actual):r.diagnostics.append(Diagnostic('F201',f"Function '{name}' returns {actual}, expected {ret}",line))
                terminated=True;continue
            if clean.startswith('throw '):terminated=True;continue
            m=re.match(r'(?:let|const)\s+(\w+)(?:\s*:\s*([^=]+))?\s*=\s*(.+)',clean)
            if m:
                n,t,e=m.groups();actual=self.infer_expr(e,env,r);env[n]=parse_type(t.strip()) if t else actual
            m=re.match(r'if\s+(\w+)\s*!=\s*null',clean)
            if m and m.group(1) in env:
                t=env[m.group(1)];env[m.group(1)]=TypeRef(t.name,t.args,False)
        if ret.name not in ('Any','Null') and not ret.nullable and not has_return:r.diagnostics.append(Diagnostic('F202',f"Function '{name}' may not return {ret} on every path",r.functions[name].line))

    def infer_expr(self,expr,env,r):
        expr=expr.strip().rstrip('}')
        lit=infer_literal(expr)
        if lit.name!='Any':return lit
        if expr in env:return env[expr]
        m=re.fullmatch(r'(\w+)\.(\w+)',expr)
        if m and m.group(1) in env:
            owner=env[m.group(1)];fields=r.records.get(owner.name,{})
            if m.group(2) not in fields:r.diagnostics.append(Diagnostic('R203',f"Record '{owner.name}' has no field '{m.group(2)}'",1));return TypeRef('Any')
            if owner.nullable:r.diagnostics.append(Diagnostic('N201',f"'{m.group(1)}' may be null",1))
            return fields[m.group(2)]
        m=re.fullmatch(r'(\w+)\((.*)\)',expr)
        if m and m.group(1) in r.functions:return r.functions[m.group(1)].return_type
        for op in ('+','-','*','/','%'):
            if op in expr:
                parts=expr.split(op,1);a=self.infer_expr(parts[0],env,r);b=self.infer_expr(parts[1],env,r)
                if a.name=='String' and b.name=='String' and op=='+':return TypeRef('String')
                if a.name in ('Int','Float','Number') and b.name in ('Int','Float','Number'):return TypeRef('Float' if 'Float' in (a.name,b.name) or op=='/' else 'Int')
        return TypeRef('Any')

    def _check_records(self,source,r):
        for m in re.finditer(r'(?:let|const)\s+(\w+)\s*:\s*(\w+)\s*=\s*\{([^}]*)\}',source,re.S):
            var,record,body=m.groups()
            if record not in r.records:continue
            fields={}
            for pair in split_top(body,','):
                if ':' in pair:
                    k,v=pair.split(':',1);fields[k.strip().strip('"\'')]=infer_literal(v.strip())
            expected=r.records[record]
            for name,t in expected.items():
                if name not in fields:r.diagnostics.append(Diagnostic('R201',f"Missing field '{name}' for record '{record}'",source[:m.start()].count('\n')+1))
                elif not compatible(t,fields[name]):r.diagnostics.append(Diagnostic('R202',f"Field '{name}' expects {t}, got {fields[name]}",source[:m.start()].count('\n')+1))
            for name in fields:
                if name not in expected:r.diagnostics.append(Diagnostic('R203',f"Unknown field '{name}' for record '{record}'",source[:m.start()].count('\n')+1))

    def _check_calls(self,source,r):
        function_ranges=[m.span() for m in re.finditer(r'function\s+\w+\s*\(',source)]
        for name,fn in r.functions.items():
            for m in re.finditer(r'\b'+re.escape(name)+r'\s*\(([^()]*)\)',source):
                # skip declaration
                prefix=source[max(0,m.start()-12):m.start()]
                if 'function' in prefix:continue
                args=split_top(m.group(1),',') if m.group(1).strip() else []
                if len(args)!=len(fn.params):r.diagnostics.append(Diagnostic('C201',f"Function '{name}' expects {len(fn.params)} arguments, got {len(args)}",source[:m.start()].count('\n')+1));continue
                for arg,(_,expected) in zip(args,fn.params):
                    actual=infer_literal(arg)
                    if actual.name!='Any' and not compatible(expected,actual):r.diagnostics.append(Diagnostic('C202',f"Argument expects {expected}, got {actual}",source[:m.start()].count('\n')+1))


# PeaLang 0.36 foundational type-system completion layer
@dataclass(frozen=True)
class GenericFunctionContract:
    name:str
    type_params:tuple[str,...]
    params:tuple[tuple[str,TypeRef],...]
    return_type:TypeRef

@dataclass(frozen=True)
class ProtocolContract:
    name:str
    methods:tuple[tuple[str,tuple[tuple[str,TypeRef],...],TypeRef],...]

def substitute_type(t:TypeRef, bindings:dict[str,TypeRef])->TypeRef:
    if t.name in bindings and not t.args:return bindings[t.name]
    return TypeRef(t.name,tuple(substitute_type(x,bindings) for x in t.args),t.nullable)

def infer_generic_bindings(expected:TypeRef, actual:TypeRef, type_params:set[str], bindings=None):
    bindings=dict(bindings or {})
    if expected.name in type_params and not expected.args:
        prior=bindings.get(expected.name)
        if prior and prior!=actual:raise ValueError(f"Conflicting inference for {expected.name}: {prior} vs {actual}")
        bindings[expected.name]=actual;return bindings
    if expected.name==actual.name and len(expected.args)==len(actual.args):
        for a,b in zip(expected.args,actual.args):bindings=infer_generic_bindings(a,b,type_params,bindings)
    return bindings

def parse_generic_functions(source:str):
    out={}
    pattern=r'function\s+(\w+)\s*<([^>]+)>\s*\((.*?)\)\s*(?:->\s*([^\{]+))?\s*\{'
    for m in re.finditer(pattern,source,re.S):
        name,tps,raw_params,raw_ret=m.groups(); type_params=tuple(x.strip() for x in tps.split(',') if x.strip());params=[]
        for item in split_top(raw_params,','):
            if ':' in item:
                n,t=item.split(':',1);params.append((n.strip(),parse_type(t.split('=',1)[0].strip())))
            else:params.append((item.strip(),TypeRef('Any')))
        out[name]=GenericFunctionContract(name,type_params,tuple(params),parse_type(raw_ret.strip()) if raw_ret else TypeRef('Any'))
    return out

def parse_protocols(source:str):
    out={}
    for m in re.finditer(r'protocol\s+(\w+)\s*\{(.*?)\}',source,re.S):
        methods=[]
        for fn in re.finditer(r'function\s+(\w+)\s*\((.*?)\)\s*(?:->\s*([^\n\{]+))?',m.group(2)):
            params=[]
            for item in split_top(fn.group(2),','):
                if not item.strip():continue
                if ':' in item:
                    n,t=item.split(':',1);params.append((n.strip(),parse_type(t.strip())))
                else:params.append((item.strip(),TypeRef('Any')))
            methods.append((fn.group(1),tuple(params),parse_type(fn.group(3).strip()) if fn.group(3) else TypeRef('Any')))
        out[m.group(1)]=ProtocolContract(m.group(1),tuple(methods))
    return out

def protocol_conforms(record_fields:dict[str,TypeRef], protocol:ProtocolContract)->bool:
    # 0.36 structural protocol surface: method-shaped fields must be Function.
    return all(name in record_fields and record_fields[name].name=='Function' for name,_,_ in protocol.methods)

def option_type(t):return TypeRef('Option',(t,))
def result_type(ok,err):return TypeRef('Result',(ok,err))
def future_type(t):return TypeRef('Future',(t,))

def analyze_project(paths):
    """Cross-module contract collector/checker for .pea source files."""
    from pathlib import Path
    result={'files':{},'functions':{},'records':{},'diagnostics':[]}
    for raw in paths:
        p=Path(raw); src=p.read_text(encoding='utf-8'); checked=SemanticAnalyzer().analyze(src,str(p))
        result['files'][str(p)]={'ok':checked.ok,'diagnostics':[str(x) for x in checked.diagnostics]}
        result['diagnostics'].extend((str(p),x) for x in checked.diagnostics)
        for n,c in checked.functions.items():result['functions'][f'{p.stem}.{n}']=c
        for n,c in checked.records.items():result['records'][f'{p.stem}.{n}']=c
    return result




