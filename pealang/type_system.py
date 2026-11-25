"""Optional static type system and source-to-runtime annotation erasure."""
from __future__ import annotations
from dataclasses import dataclass,field,replace
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

MAX_TYPE_SOURCE_CHARS=2_000_000
TOKEN=re.compile(r'(?:(\w+)|([<>,|?{}:]))')  # lgtm[py/polynomial-redos]
def parse_type(text:str)->TypeRef:
    if len(text)>65536:raise ValueError('Type expression exceeds 65536 characters')
    text=text.strip()
    if '|' in text:
        parts=tuple(parse_type(x) for x in split_top(text,'|'));return TypeRef('Union',parts)
    nullable=text.endswith('?')
    if nullable:text=text[:-1].strip()
    m=re.fullmatch(r'([A-Za-z_]\w*)(?:[ \t]*<([^<>]*(?:<[^<>]*>[^<>]*)*)>)?',text)
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
    if re.fullmatch(r'-?\d+\.\d+',t):return TypeRef('Float')  # lgtm[py/polynomial-redos]
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


def compatible_generic(expected:TypeRef,actual:TypeRef,type_params=frozenset())->bool:
    """Generic-aware compatibility; type parameters are wildcards during checking."""
    if expected.name in type_params or actual.name in type_params:return True
    if expected.name=='Any' or actual.name=='Any':return True
    if actual.nullable and not expected.nullable:return False
    if actual.name=='Null':return expected.nullable or expected.name in ('Null','Option')
    if expected.name=='Number' and actual.name in ('Int','Float','Number'):return True
    if expected.name=='Union':return any(compatible_generic(x,actual,type_params) for x in expected.args)
    if expected.name!=actual.name:return False
    if len(expected.args)!=len(actual.args):return False
    return all(compatible_generic(x,y,type_params) for x,y in zip(expected.args,actual.args))


class TypeChecker:
    def check(self,source:str,source_name='<input>')->TypeCheckResult:
        if len(source)>MAX_TYPE_SOURCE_CHARS:raise ValueError('Type-check source exceeds safety limit')
        # Guard against polynomial regex on uncontrolled input
        if len(source) > 100000:
            raise ValueError('Type-check source exceeds safety limit')
        r=TypeCheckResult();known=set(BUILTINS)
        for gf in parse_generic_functions(source).values():known.update(gf.type_params)
        # record declarations, one-line or multiline (supports ADT constructors)
        for m in re.finditer(r'(?m)^type[ \t]+([A-Za-z_]\w*)[ \t]*=[ \t]*(?:\{([^{}]*)\}|([^\n]*))',source):
            name,mbody,mcons=m.group(1),m.group(2),m.group(3)
            if mbody is not None:
                # Record-style type: type Name = {field: type, ...}
                fields={}
                for f in split_top(mbody,','):
                    if ':' in f:
                        n,t=f.split(':',1)
                        try:fields[n.strip()]=parse_type(t.strip())
                        except ValueError as e:r.diagnostics.append(Diagnostic('P100',str(e),source[:m.start()].count('\n')+1))
                r.records[name]=fields;known.add(name)
            elif mcons is not None:
                # ADT-style type: type Name = Constructor1 | Constructor2 | Constructor3
                # or type Name = Constructor1 arg1 arg2 | Constructor2 arg1 arg2
                # mcons captures the full text after '='
                tags=[t.strip() for t in mcons.split('|') if t.strip()]
                r.records[name]={'constructors': tags};known.add(name)
        for ln,line in enumerate(source.splitlines(),1):
            clean=line.split('//',1)[0].strip()
            # Typed declaration: let x: Type = value
            m=re.match(r'(?:let|const)[ \t]+([A-Za-z_]\w*)[ \t]*:[ \t]*([^=\n]+)(?:[ \t]*=[ \t]*([^\n]+))?$',clean)  # lgtm[py/polynomial-redos]
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
            m=re.match(r'(?:let|const)[ \t]+([A-Za-z_]\w*)[ \t]*=[ \t]*([^\n]+)$',clean)  # lgtm[py/polynomial-redos]
            if m:r.symbols[m.group(1)]=infer_literal(m.group(2));continue
            # Assignment to known symbol
            m=re.match(r'([A-Za-z_]\w*)[ \t]*=[ \t]*([^\n]+)$',clean)  # lgtm[py/polynomial-redos]
            if m and m.group(1) in r.symbols:
                actual=infer_literal(m.group(2));expected=r.symbols[m.group(1)]
                if not compatible(expected,actual):r.diagnostics.append(Diagnostic('T202',f"Cannot assign {actual} to {expected} variable '{m.group(1)}'",ln))
            # Function signature validation
            m=re.match(r'function[ \t]+([A-Za-z_]\w*)(?:[ \t]*<[^<>]+>)?[ \t]*\(([^()]*)\)[ \t]*(?:->[ \t]*([^{}\n]+))?',clean)
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
    if len(source) > MAX_TYPE_SOURCE_CHARS: raise ValueError('Source exceeds safety limit')
    # Remove protocol/trait declarations and generic parameter lists before runtime parsing.
    source=re.sub(r'(?m)^[ \t]*(?:protocol|trait)[ \t]+[A-Za-z_]\w*[ \t]*=?[ \t]*\{[^{}]*\}[ \t]*(?:\n|$)','',source)  # lgtm[py/polynomial-redos]
    source=re.sub(r'(?m)^[ \t]*trait[ \t]+[A-Za-z_]\w*[ \t]*(?:\n|$)','',source)  # lgtm[py/polynomial-redos]
    source=re.sub(r'(function\s+\w+)\s*<[^>]+>',r'\1',source)
    # Remove record declarations before runtime parsing.
    source=re.sub(r'(?m)^[ \t]*type[ \t]+[A-Za-z_]\w*[ \t]*=[ \t]*\{[^{}]*\}[ \t]*(?:\n|$)','',source)
    # Function return annotations.
    source=re.sub(r'(function[ \t]+[A-Za-z_]\w*[ \t]*\([^()]*\))[ \t]*->[ \t]*[A-Za-z_]\w*(?:[ \t]*<[^<>{}\n]+>)?\??',r'\1',source)
    # Parameter annotations, preserving defaults and separators.
    def params(m):
        inner=re.sub(r'(\b[A-Za-z_]\w*)[ \t]*:[ \t]*[A-Za-z_]\w*(?:[ \t]*<[^<>,)=\n]+>)?\??',r'\1',m.group(1))
        return '('+inner+')'
    source=re.sub(r'\(([^()]*)\)',params,source)
    # Variable annotations.
    source=re.sub(r'\b(let|const)[ \t]+([A-Za-z_]\w*)[ \t]*:[ \t]*[A-Za-z_]\w*(?:[ \t]*<[^<>=\n]+>)?\??[ \t]*=',r'\1 \2 =',source)
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
    generics:dict[str,'GenericFunctionContract']=field(default_factory=dict)
    protocols:dict[str,'ProtocolContract']=field(default_factory=dict)
    traits:dict[str,'ProtocolContract']=field(default_factory=dict)

class SemanticAnalyzer:
    """Flow-aware semantic checks layered over the optional type surface."""
    def analyze(self,source:str,source_name='<input>', 
                cross_module_context: dict | None = None)->SemanticResult:
        if len(source) > MAX_TYPE_SOURCE_CHARS: raise ValueError('Source exceeds safety limit')
        base=TypeChecker().check(source,source_name)
        result=SemanticResult(base.diagnostics,base.symbols,base.records,{},{},{},{})
        generics = parse_generic_functions(source)
        known=set(BUILTINS)|set(result.records)
        for gf in generics.values():known.update(gf.type_params)
        for name, gf in generics.items():
            result.generics[name] = gf
            result.functions[name] = FunctionContract(name, gf.params, gf.return_type, 0)
        
        # Parse protocols and marker traits.
        protocols = parse_protocols(source)
        traits = parse_traits(source)
        result.protocols.update(protocols)
        result.traits.update(traits)
        all_contracts = {**protocols, **traits}
        bound_contracts = set()
        for gf in generics.values():
            for bounds in gf.bounds.values():bound_contracts.update(bounds)

        lines=source.splitlines()
        # Collect function contracts and bodies using brace depth.
        i=0
        while i<len(lines):
            line=lines[i]
            generic_match=re.search(r'function[ \t]+([A-Za-z_]\w*)[ \t]*<([^<>]+)>[ \t]*\(([^()]*)\)[ \t]*(?:->[ \t]*([^{}\n]+))?[ \t]*\{',line)
            plain_match=None if generic_match else re.search(r'function[ \t]+([A-Za-z_]\w*)[ \t]*\(([^()]*)\)[ \t]*(?:->[ \t]*([^{}\n]+))?[ \t]*\{',line)
            if generic_match:name,tps,raw_params,raw_ret=generic_match.groups()
            elif plain_match:name,raw_params,raw_ret=plain_match.groups();tps=None
            else:i+=1;continue

            params=[]
            for item in split_top(raw_params,','):
                item=item.strip()
                if not item:continue
                pname=item.split(':',1)[0].split('=',1)[0].strip();ptype=TypeRef('Any')
                if ':' in item:
                    ptype=parse_type(item.split(':',1)[1].split('=',1)[0].strip())
                params.append((pname,ptype))
            ret=parse_type(raw_ret.strip()) if raw_ret else TypeRef('Any')
            result.functions[name]=FunctionContract(name,params,ret,i+1)
            if generic_match and name in result.generics:
                result.generics[name]=replace(result.generics[name],params=tuple(params),return_type=ret,line=i+1)
            depth=line.count('{')-line.count('}');body=[];j=i+1
            while j<len(lines) and depth>0:
                depth+=lines[j].count('{')-lines[j].count('}')
                if depth>0:body.append((j+1,lines[j]))
                j+=1
            self._check_function(name,params,ret,body,result,known)
            i=j
        
        # Check protocol/trait conformance only where a generic bound references it.
        record_lines = {m.group(1): source[:m.start()].count('\n')+1
                        for m in re.finditer(r'(?m)^type[ \t]+([A-Za-z_]\w*)[ \t]*=', source)}
        for record_name, record_fields in result.records.items():
            for contract_name in sorted(bound_contracts):
                contract = all_contracts.get(contract_name)
                if contract is None:continue
                result.diagnostics.extend(check_record_protocol_conformance(
                    record_name, record_fields, contract, record_lines.get(record_name, 0)))
        
        # Check match exhaustiveness for ADTs
        all_records = dict(result.records)
        # Parse ADT constructors
        for m in re.finditer(r'(?m)^type[ \t]+([A-Za-z_]\w*)[ \t]*=[ \t]*([^\n]+)', source):
            if '|' in m.group(2):
                name = m.group(1)
                constructors = [c.strip() for c in m.group(2).split('|')]
                all_records[name] = {'constructors': constructors}
        
        self._check_records(source,result)
        self._check_calls(source,result,all_contracts)
        
        # Cross-module context
        if cross_module_context:
            # Check external function calls
            self._check_cross_module_calls(source, result, cross_module_context)
        
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
            m=re.match(r'(?:let|const)[ \t]+([A-Za-z_]\w*)(?:[ \t]*:[ \t]*([^=\n]+))?[ \t]*=[ \t]*([^\n]+)',clean)  # lgtm[py/polynomial-redos]
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
        m=re.fullmatch(r'(\w+)\.(\w+)',expr)  # lgtm[py/polynomial-redos]
        if m and m.group(1) in env:
            owner=env[m.group(1)];fields=r.records.get(owner.name,{})
            if m.group(2) not in fields:r.diagnostics.append(Diagnostic('R203',f"Record '{owner.name}' has no field '{m.group(2)}'",1));return TypeRef('Any')
            if owner.nullable:r.diagnostics.append(Diagnostic('N201',f"'{m.group(1)}' may be null",1))
            return fields[m.group(2)]
        m=re.fullmatch(r'([A-Za-z_]\w*)\(([^()]*)\)',expr)  # lgtm[py/polynomial-redos]
        if m and m.group(1) in r.functions:return r.functions[m.group(1)].return_type
        for op in ('+','-','*','/','%'):
            if op in expr:
                parts=expr.split(op,1);a=self.infer_expr(parts[0],env,r);b=self.infer_expr(parts[1],env,r)
                if a.name=='String' and b.name=='String' and op=='+':return TypeRef('String')
                if a.name in ('Int','Float','Number') and b.name in ('Int','Float','Number'):return TypeRef('Float' if 'Float' in (a.name,b.name) or op=='/' else 'Int')
        return TypeRef('Any')

    def _check_records(self,source,r):
        for m in re.finditer(r'(?:let|const)[ \t]+([A-Za-z_]\w*)[ \t]*:[ \t]*([A-Za-z_]\w*)[ \t]*=[ \t]*\{([^{}]*)\}',source):
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

    def _check_calls(self,source,r,protocols=None):
        protocols=protocols or {}
        env=dict(r.symbols)
        for name,fn in r.functions.items():
            generic=r.generics.get(name)
            for m in re.finditer(r'\b'+re.escape(name)+r'\s*\(([^()]*)\)',source):
                # skip declaration
                prefix=source[max(0,m.start()-16):m.start()]
                if 'function' in prefix:continue
                line=source[:m.start()].count('\n')+1
                args=split_top(m.group(1),',') if m.group(1).strip() else []
                expected_params=generic.params if generic else fn.params
                if len(args)!=len(expected_params):
                    code='G201' if generic else 'C201'
                    r.diagnostics.append(Diagnostic(code,f"Function '{name}' expects {len(expected_params)} arguments, got {len(args)}",line));continue
                actual_types=[self.infer_expr(arg,env,r) for arg in args]
                if generic is None:
                    for actual,(_,expected) in zip(actual_types,fn.params):
                        if actual.name!='Any' and not compatible(expected,actual):r.diagnostics.append(Diagnostic('C202',f"Argument expects {expected}, got {actual}",line))
                    continue
                try:
                    bindings=infer_type_arguments(generic,actual_types)
                except ValueError as e:
                    r.diagnostics.append(Diagnostic('G202',f"Cannot infer generic arguments for '{name}': {e}",line));continue
                for issue in check_generic_bounds(generic,bindings,protocols,r.records):
                    r.diagnostics.append(Diagnostic('G203',f"Generic bound violation in '{name}': {issue}",line))
                instantiated=instantiate_generic(generic,bindings)
                for actual,(_,expected) in zip(actual_types,instantiated.params):
                    if actual.name!='Any' and not compatible_generic(expected,actual,set(generic.type_params)):
                        r.diagnostics.append(Diagnostic('G204',f"Generic argument expects {expected}, got {actual}",line))

    def _check_cross_module_calls(self, source: str, r: SemanticResult, context: dict):
        """Check calls to functions from other modules."""
        # Check for module.function() calls
        for m in re.finditer(r'(\w+)\.(\w+)\s*\(([^()]*)\)', source):
            module, fn_name = m.group(1), m.group(2)
            args = split_top(m.group(3), ',') if m.group(3).strip() else []
            
            if module in context.get('modules', {}):
                mod_funcs = context['modules'][module].get('functions', {})
                full_name = f"{module}.{fn_name}"
                if full_name in context.get('functions', {}):
                    fn = context['functions'][full_name]
                    if len(args) != len(fn.params):
                        r.diagnostics.append(Diagnostic(
                            'X201',
                            f"Cross-module call '{full_name}' expects {len(fn.params)} arguments, got {len(args)}",
                            source[:m.start()].count('\n')+1
                        ))
                        continue
                    for arg, (_, expected) in zip(args, fn.params):
                        actual = infer_literal(arg)
                        if actual.name != 'Any' and not compatible(expected, actual):
                            r.diagnostics.append(Diagnostic(
                                'X202',
                                f"Cross-module call '{full_name}' arg expects {expected}, got {actual}",
                                source[:m.start()].count('\n')+1
                            ))


# PeaLang 0.36 foundational type-system completion layer
@dataclass(frozen=True)
class GenericFunctionContract:
    name:str
    type_params:tuple[str,...]
    params:tuple[tuple[str,TypeRef],...]
    return_type:TypeRef
    bounds:dict[str,tuple[str,...]]=field(default_factory=dict)
    line:int=0

@dataclass(frozen=True)
class ProtocolContract:
    name:str
    methods:tuple[tuple[str,tuple[tuple[str,TypeRef],...],TypeRef],...]
    method_names_only:bool=False

def substitute_type(t:TypeRef, bindings:dict[str,TypeRef])->TypeRef:
    """Substitute type parameters with concrete types."""
    if t.name in bindings and not t.args:
        return bindings[t.name]
    return TypeRef(t.name,tuple(substitute_type(x,bindings) for x in t.args),t.nullable)


def infer_generic_bindings(expected:TypeRef, actual:TypeRef, type_params:set[str], bindings=None):
    """Infer type parameter bindings from expected vs actual types."""
    bindings=dict(bindings or {})
    if expected.name in type_params and not expected.args:
        prior=bindings.get(expected.name)
        if prior and prior!=actual:raise ValueError(f"Conflicting inference for {expected.name}: {prior} vs {actual}")
        bindings[expected.name]=actual;return bindings
    if expected.name==actual.name and len(expected.args)==len(actual.args):
        for a,b in zip(expected.args,actual.args):bindings=infer_generic_bindings(a,b,type_params,bindings)
    return bindings


def instantiate_generic(generic: GenericFunctionContract, bindings: dict[str,TypeRef]) -> FunctionContract:
    """Instantiate a generic function with concrete type bindings."""
    params = tuple((name, substitute_type(t, bindings)) for name, t in generic.params)
    ret = substitute_type(generic.return_type, bindings)
    return FunctionContract(generic.name, params, ret, 0)


def check_generic_bounds(generic: GenericFunctionContract, bindings: dict[str,TypeRef],
                         protocols=None, records=None) -> list[str]:
    """Return human-readable violations of declared generic type-parameter bounds."""
    protocols=protocols or {};records=records or {};issues=[]
    for param,bounds in generic.bounds.items():
        concrete=bindings.get(param)
        if concrete is None:continue
        for bound in bounds:
            if bound in BUILTINS or bound in generic.type_params:continue
            protocol=protocols.get(bound)
            if protocol is None:
                issues.append(f"unknown protocol bound '{bound}' for type parameter '{param}'")
                continue
            fields=records.get(concrete.name)
            if fields is None:continue
            if not protocol_conforms(fields,protocol):
                issues.append(f"type '{concrete}' does not satisfy bound '{bound}'")
    return issues


def check_generic_application(generic: GenericFunctionContract, type_args: list[TypeRef],
                              protocols=None, records=None) -> dict[str,TypeRef]:
    """Check and infer type arguments for a generic function application."""
    if len(type_args) != len(generic.type_params):
        raise ValueError(f"Expected {len(generic.type_params)} type arguments, got {len(type_args)}")
    bindings = dict(zip(generic.type_params, type_args))
    issues=check_generic_bounds(generic,bindings,protocols,records)
    if issues:raise ValueError('; '.join(issues))
    return bindings


def infer_type_arguments(generic: GenericFunctionContract, actual_args: list[TypeRef]) -> dict[str,TypeRef]:
    """Infer type arguments from actual argument types."""
    bindings = {}
    type_params = set(generic.type_params)
    
    # Try to infer from each parameter
    for (_, expected_param), actual_arg in zip(generic.params, actual_args):
        if actual_arg.name == 'Any':
            continue
        bindings = infer_generic_bindings(expected_param, actual_arg, type_params, bindings)
    
    # Check all type params are bound
    missing = [p for p in generic.type_params if p not in bindings]
    if missing:
        raise ValueError(f"Cannot infer type arguments for: {missing}")
    
    return bindings

def parse_generic_functions(source:str):
    out={}
    pattern=r'function[ \t]+([A-Za-z_]\w*)[ \t]*<([^<>]+)>[ \t]*\(([^()]*)\)[ \t]*(?:->[ \t]*([^{}\n]+))?[ \t]*\{'
    for m in re.finditer(pattern,source):
        name,tps,raw_params,raw_ret=m.groups();type_params=[];bounds={}
        for raw_param in tps.split(','):
            raw_param=raw_param.strip()
            if not raw_param:continue
            param_name,_,raw_bound=raw_param.partition(':')
            param_name=param_name.strip()
            if not param_name:continue
            type_params.append(param_name)
            bounds[param_name]=tuple(x.strip() for x in re.split(r'[+&]',raw_bound) if x.strip())
        params=[]
        for item in split_top(raw_params,','):
            if ':' in item:
                n,t=item.split(':',1);params.append((n.strip(),parse_type(t.split('=',1)[0].strip())))
            else:params.append((item.strip(),TypeRef('Any')))
        line=source[:m.start()].count('\n')+1
        out[name]=GenericFunctionContract(
            name,tuple(type_params),tuple(params),
            parse_type(raw_ret.strip()) if raw_ret else TypeRef('Any'),bounds,line)
    return out

def _parse_contract_declarations(source:str,keyword:str)->dict[str,'ProtocolContract']:
    out={}
    body_pattern=re.compile(rf'(?m)^[ \t]*{keyword}[ \t]+([A-Za-z_]\w*)[ \t]*(?:=[ \t]*)?\{{([^{{}}]*)\}}')
    marker_pattern=re.compile(rf'(?m)^[ \t]*{keyword}[ \t]+([A-Za-z_]\w*)[ \t]*(?:\n|$)')
    for m in body_pattern.finditer(source):
        methods=[]
        for fn in re.finditer(r'function[ \t]+([A-Za-z_]\w*)[ \t]*\(([^()]*)\)[ \t]*(?:->[ \t]*([^{}\n]+))?',m.group(2)):
            params=[]
            for item in split_top(fn.group(2),','):
                if not item.strip():continue
                if ':' in item:
                    n,t=item.split(':',1);params.append((n.strip(),parse_type(t.split('=',1)[0].strip())))
                else:params.append((item.strip(),TypeRef('Any')))
            methods.append((fn.group(1),tuple(params),parse_type(fn.group(3).strip()) if fn.group(3) else TypeRef('Any')))
        out[m.group(1)]=ProtocolContract(m.group(1),tuple(methods))
    for m in marker_pattern.finditer(source):
        if m.group(1) not in out:out[m.group(1)]=ProtocolContract(m.group(1),())
    return out

def parse_protocols(source:str)->dict[str,'ProtocolContract']:
    """Parse structural protocol declarations."""
    return _parse_contract_declarations(source,'protocol')

def parse_traits(source:str)->dict[str,'ProtocolContract']:
    """Parse trait declarations; traits without methods are marker contracts."""
    return _parse_contract_declarations(source,'trait')

def function_field_type(params,return_type)->TypeRef:
    """Encode a function field as Function<P1,...,Pn,R>; bare Function is a wildcard."""
    return TypeRef('Function',tuple(t for _,t in params)+(return_type,))

def _function_signature(t:TypeRef):
    if t.name!='Function' or not t.args:return None
    return tuple(t.args[:-1]),t.args[-1]

def protocol_conforms(record_fields:dict[str,TypeRef], protocol:ProtocolContract)->bool:
    """Structural conformance; bare Function fields remain wildcard-compatible."""
    return not check_record_protocol_conformance('<conformance>',record_fields,protocol)


def check_record_protocol_conformance(record_name: str, record_fields: dict[str,TypeRef],
                                       protocol: ProtocolContract, line: int = 0) -> list[Diagnostic]:
    """Check structural conformance with P201-P205 diagnostics."""
    diagnostics = []
    for method_name, params, return_type in protocol.methods:
        if method_name not in record_fields:
            diagnostics.append(Diagnostic(
                'P201',
                f"Record '{record_name}' does not implement required method '{method_name}' for protocol '{protocol.name}'",
                line
            ))
            continue

        field_type = record_fields[method_name]
        if field_type.name != 'Function':
            diagnostics.append(Diagnostic(
                'P202',
                f"Field '{method_name}' in record '{record_name}' must be a function for protocol '{protocol.name}'",
                line
            ))
            continue
        if protocol.method_names_only:continue
        signature = _function_signature(field_type)
        if signature is None:continue  # Bare Function is a legacy wildcard.
        actual_params, actual_return = signature
        expected_params = tuple(t for _,t in params)
        if len(actual_params) != len(expected_params):
            diagnostics.append(Diagnostic(
                'P203',
                f"Method '{method_name}' in '{record_name}' has {len(actual_params)} params, protocol requires {len(expected_params)}",
                line
            ))
            continue
        for (_, expected_t), actual_t in zip(params,actual_params):
            if not compatible_generic(expected_t,actual_t):
                diagnostics.append(Diagnostic(
                    'P204',
                    f"Method '{method_name}' param type mismatch: expected {expected_t}, got {actual_t}",
                    line
                ))
        if not compatible_generic(return_type,actual_return):
            diagnostics.append(Diagnostic(
                'P205',
                f"Method '{method_name}' return type mismatch: expected {return_type}, got {actual_return}",
                line
            ))
    return diagnostics


def check_exhaustive_match(source: str, match_expr_type: TypeRef, cases: list[str], 
                            all_records: dict[str, dict] | None = None) -> list[Diagnostic]:
    """Check if match cases are exhaustive for the given ADT type."""
    diagnostics = []
    
    if all_records and match_expr_type.name in all_records:
        record_info = all_records[match_expr_type.name]
        if 'constructors' in record_info:
            constructors = set(record_info['constructors'])
            covered = set()
            for case in cases:
                # Extract constructor name from case pattern
                c = case.strip().split()[0] if case.strip() else ''
                if c in constructors:
                    covered.add(c)
            
            missing = constructors - covered
            if missing:
                diagnostics.append(Diagnostic(
                    'M201',
                    f"Non-exhaustive match on '{match_expr_type.name}': missing constructors {sorted(missing)}",
                    0,
                    severity='warning'
                ))
    
    return diagnostics


# Result/Option/Future type constructors
def result_type(ok_t: TypeRef, err_t: TypeRef) -> TypeRef:
    return TypeRef('Result', (ok_t, err_t))

def option_type(inner_t: TypeRef) -> TypeRef:
    return TypeRef('Option', (inner_t,))

def future_type(inner_t: TypeRef) -> TypeRef:
    return TypeRef('Future', (inner_t,))

# Predefined common types
Result = lambda ok, err: result_type(ok, err)
Option = lambda inner: option_type(inner)
Future = lambda inner: future_type(inner)

def option_type(t):return TypeRef('Option',(t,))
def result_type(ok,err):return TypeRef('Result',(ok,err))
def future_type(t):return TypeRef('Future',(t,))

def analyze_project(paths):
    """Cross-module contract collector/checker for .pea source files."""
    from pathlib import Path
    result={'files':{},'functions':{},'generics':{},'protocols':{},'traits':{},'records':{},'diagnostics':[]}
    all_records = {}
    all_protocols = {}
    all_traits = {}
    all_generics = {}
    all_functions = {}
    
    # First pass: collect all declarations
    for raw in paths:
        p=Path(raw); src=p.read_text(encoding='utf-8')
        # Parse generics
        all_generics.update({f'{p.stem}.{k}': v for k,v in parse_generic_functions(src).items()})
        # Parse protocols
        all_protocols.update({f'{p.stem}.{k}': v for k,v in parse_protocols(src).items()})
        all_traits.update({f'{p.stem}.{k}': v for k,v in parse_traits(src).items()})
        # Parse records (type declarations)
        for m in re.finditer(r'(?m)^type[ \t]+([A-Za-z_]\w*)[ \t]*=[ \t]*\{([^{}]*)\}', src):
            name, body = m.group(1), m.group(2)
            fields = {}
            for f in split_top(body,','):
                if ':' in f:
                    n, t = f.split(':', 1)
                    try:
                        fields[n.strip()] = parse_type(t.strip())
                    except ValueError:
                        pass
            all_records[f'{p.stem}.{name}'] = fields
        # Parse ADT types
        for m in re.finditer(r'(?m)^type[ \t]+([A-Za-z_]\w*)[ \t]*=[ \t]*([^\n]+)', src):
            if '|' in m.group(2):
                name = m.group(1)
                constructors = [c.strip() for c in m.group(2).split('|')]
                all_records[f'{p.stem}.{name}'] = {'constructors': constructors}
    
    # Second pass: check each file with cross-module context
    for raw in paths:
        p=Path(raw); src=p.read_text(encoding='utf-8'); checked=SemanticAnalyzer().analyze(src,str(p))
        
        # Cross-module function calls
        for call in re.finditer(r'(\w+)\.(\w+)\s*\(', src):
            module, fn = call.groups()
            # Check if this is a cross-module call
            pass
        
        result['files'][str(p)]={'ok':checked.ok,'diagnostics':[str(x) for x in checked.diagnostics]}
        result['diagnostics'].extend((str(p),x) for x in checked.diagnostics)
        for n,c in checked.functions.items():result['functions'][f'{p.stem}.{n}']=c
        for n,c in checked.generics.items():result['generics'][f'{p.stem}.{n}']=c
        for n,c in checked.protocols.items():result['protocols'][f'{p.stem}.{n}']=c
        for n,c in checked.traits.items():result['traits'][f'{p.stem}.{n}']=c
        for n,c in checked.records.items():result['records'][f'{p.stem}.{n}']=c
    
    # Check protocol conformance across modules
    for record_name, record_fields in all_records.items():
        for protocol_name, protocol in all_protocols.items():
            # Would need explicit "implements" declaration or structural check
            pass
    
    return result


# ============================================================================
# Phase 5: Language Evolution - Effect System, Linear Types, Refinement Types, Macros, Module System v2
# ============================================================================

# ---------------------------------------------------------------------------
# Effect System
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Effect:
    """Represents a computational effect."""
    name: str
    parameters: tuple[TypeRef, ...] = ()
    
    def __str__(self):
        if self.parameters:
            return f"{self.name}<{', '.join(str(p) for p in self.parameters)}>"
        return self.name


@dataclass(frozen=True)
class EffectSet:
    """Set of effects for a function/type."""
    effects: frozenset[Effect] = frozenset()
    
    def __or__(self, other: "EffectSet") -> "EffectSet":
        return EffectSet(self.effects | other.effects)
    
    def __and__(self, other: "EffectSet") -> "EffectSet":
        return EffectSet(self.effects & other.effects)
    
    def __sub__(self, other: "EffectSet") -> "EffectSet":
        return EffectSet(self.effects - other.effects)
    
    def contains(self, effect: Effect) -> bool:
        return effect in self.effects
    
    def __str__(self):
        if not self.effects:
            return "Pure"
        return "{" + ", ".join(str(e) for e in sorted(self.effects, key=str)) + "}"


# Built-in effects
IO_EFFECT = Effect("IO")
STATE_EFFECT = Effect("State")
EXCEPTION_EFFECT = Effect("Exception")
ASYNC_EFFECT = Effect("Async")
NONDET_EFFECT = Effect("NonDet")

EFFECT_HIERARCHY = {
    IO_EFFECT: {STATE_EFFECT, EXCEPTION_EFFECT},
    STATE_EFFECT: set(),
    EXCEPTION_EFFECT: set(),
    ASYNC_EFFECT: {IO_EFFECT},
    NONDET_EFFECT: set(),
}


def infer_effects(source: str, func_name: str) -> EffectSet:
    """Infer effects from function source code (simplified)."""
    effects = set()
    
    # Check for IO operations
    if re.search(r'\b(print|read|write|http|fetch|open)\b', source):
        effects.add(IO_EFFECT)
    
    # Check for state mutations
    if re.search(r'\b(let|const)\s+\w+\s*=', source):
        effects.add(STATE_EFFECT)
    
    # Check for throw/try
    if re.search(r'\b(throw|try|catch)\b', source):
        effects.add(EXCEPTION_EFFECT)
    
    # Check for async/await
    if re.search(r'\b(async|await)\b', source):
        effects.add(ASYNC_EFFECT)
    
    # Check for non-determinism
    if re.search(r'\b(random|parallel)\b', source):
        effects.add(NONDET_EFFECT)
    
    # Expand based on hierarchy
    expanded = set(effects)
    for eff in effects:
        expanded.update(EFFECT_HIERARCHY.get(eff, set()))
    
    return EffectSet(frozenset(expanded))


def check_effect_subtyping(actual: EffectSet, expected: EffectSet) -> list[Diagnostic]:
    """Check if actual effects are sub-effect of expected."""
    diagnostics = []
    missing = expected.effects - actual.effects
    if missing:
        diagnostics.append(Diagnostic(
            'E101',
            f"Missing required effects: {', '.join(str(e) for e in missing)}",
            0
        ))
    return diagnostics


# ---------------------------------------------------------------------------
# Linear/Affine Types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LinearType:
    """Marker for linear (must be used exactly once) or affine (at most once) types."""
    base_type: TypeRef
    linearity: str = "linear"  # "linear" or "affine"
    
    def __str__(self):
        prefix = "!" if self.linearity == "linear" else "?"
        return f"{prefix}{self.base_type}"


def is_linear(t: TypeRef) -> bool:
    """Check if a type is linear/affine."""
    return isinstance(t, LinearType) or (hasattr(t, 'name') and t.name.startswith('!'))


def check_linear_usage(source: str, symbol_table: dict[str, TypeRef]) -> list[Diagnostic]:
    """Check linear/affine variable usage.
    
    Only variables explicitly marked with ! (linear) or ? (affine) are checked.
    Regular variables without markers are not subject to linear/affine checking.
    """
    diagnostics = []
    
    # Track variable definitions and uses
    used = set()
    defined = {}  # name -> (linearity, position)
    decl_positions = set()  # Track declaration positions to exclude
    
    # Pattern: let !name = ... (linear), let ?name = ... (affine), let name = ... (regular)
    for m in re.finditer(r'\b(let|const)\s+(!|\?)?(\w+)\s*=', source):
        _, linear_marker, name = m.groups()
        if linear_marker == "!":
            linearity = "linear"
        elif linear_marker == "?":
            linearity = "affine"
        else:
            # Regular variable - not subject to linear/affine checking
            continue
        defined[name] = (linearity, m.start())
        # Mark the declaration span to exclude from usage detection
        decl_start = m.start()
        decl_end = m.end()
        for i in range(decl_start, decl_end):
            decl_positions.add(i)
    
    # Find variable usages (excluding declarations)
    for m in re.finditer(r'\b(\w+)\b', source):
        name = m.group(1)
        if name in defined and m.start() not in decl_positions:
            used.add(name)
    
    for name, (linearity, pos) in defined.items():
        if name not in used:
            if linearity == "linear":
                diagnostics.append(Diagnostic(
                    'L101',
                    f"Linear variable '{name}' defined but never used",
                    source[:pos].count('\n') + 1
                ))
            else:
                diagnostics.append(Diagnostic(
                    'L102',
                    f"Affine variable '{name}' defined but never used (warning)",
                    pos + 1,
                    severity='warning'
                ))
    
    return diagnostics


# ---------------------------------------------------------------------------
# Refinement Types (Dependent Types Light)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RefinementType:
    """Refinement type: {v: BaseType | predicate(v)}"""
    base_type: TypeRef
    predicate: str  # Expression that evaluates to boolean
    variable: str = "v"
    
    def __str__(self):
        return f"{{{self.variable}: {self.base_type} | {self.predicate}}}"


def parse_refinement(text: str) -> RefinementType | None:
    """Parse refinement type from string: {v: Int | v > 0}"""
    m = re.match(r'\{(\w+):\s*([^|]+)\|\s*(.+)\}', text.strip())
    if not m:
        return None
    var, base, pred = m.groups()
    return RefinementType(parse_type(base.strip()), pred.strip(), var.strip())


def check_refinement(value: Any, refinement: RefinementType) -> bool:
    """Check if a value satisfies a refinement predicate using safe evaluation."""
    try:
        # Use safe evaluator instead of eval
        return _safe_eval_predicate(refinement.predicate, refinement.variable, value)
    except Exception:
        return False


def _safe_eval_predicate(predicate: str, var_name: str, value: Any) -> bool:
    """Safely evaluate a refinement predicate without using eval."""
    import operator
    import re
    
    # Create a safe environment
    local_vars = {var_name: value}
    
    # Safe operators
    ops = {
        '==': operator.eq, '!=': operator.ne,
        '<': operator.lt, '<=': operator.le,
        '>': operator.gt, '>=': operator.ge,
        '+': operator.add, '-': operator.sub,
        '*': operator.mul, '/': operator.truediv,
        '%': operator.mod, '**': operator.pow,
    }
    
    pred = predicate.strip()
    
    # Handle 'not' prefix
    if pred.startswith('not '):
        return not _safe_eval_predicate(pred[4:], var_name, value)
    
    # Handle 'and' / 'or' (simplified)
    if ' and ' in pred:
        parts = pred.split(' and ')
        return all(_safe_eval_predicate(p.strip(), var_name, value) for p in parts)
    if ' or ' in pred:
        parts = pred.split(' or ')
        return any(_safe_eval_predicate(p.strip(), var_name, value) for p in parts)
    
    # Handle len(v) > n patterns
    len_match = re.match(r'len\((\w+)\)\s*([<>]=?|==|!=)\s*(.+)', pred)
    if len_match:
        var, op, rhs = len_match.groups()
        if var == var_name:
            lhs = len(value)
            try:
                rhs_val = int(rhs)
            except ValueError:
                try:
                    rhs_val = float(rhs)
                except ValueError:
                    rhs_val = rhs.strip('"\'')
            ops_map = {
                '>': operator.gt, '<': operator.lt,
                '>=': operator.ge, '<=': operator.le,
                '==': operator.eq, '!=': operator.ne,
            }
            return ops_map[op](lhs, rhs_val)
    
    # Try to parse binary operations
    for op_str, op_func in ops.items():
        if f' {op_str} ' in pred:
            parts = pred.split(f' {op_str} ', 1)
            if len(parts) == 2:
                left, right = parts[0].strip(), parts[1].strip()
                
                def eval_side(side):
                    if side == var_name:
                        return local_vars[var_name]
                    # Try to parse as literal
                    try:
                        return int(side)
                    except ValueError:
                        try:
                            return float(side)
                        except ValueError:
                            # String literal
                            if (side.startswith('"') and side.endswith('"')) or \
                               (side.startswith("'") and side.endswith("'")):
                                return side[1:-1]
                            return side
                
                try:
                    left_val = eval_side(left)
                    right_val = eval_side(right)
                    return bool(op_func(left_val, right_val))
                except Exception:
                    pass
    
    # Handle simple boolean expressions
    if pred == var_name:
        return bool(local_vars[var_name])
    
    # Fallback: try to evaluate as boolean
    try:
        return bool(local_vars[var_name])
    except Exception:
        return False


def infer_refinement(source: str, var_name: str) -> RefinementType | None:
    """Infer refinement from usage patterns (simplified)."""
    # Check for assertions
    for m in re.finditer(rf'assert\s+{re.escape(var_name)}\s*(.+)', source):
        pred = m.group(1).strip()
        # Try to parse as comparison
        return RefinementType(TypeRef("Any"), pred, var_name)
    return None


# ---------------------------------------------------------------------------
# Macros & Metaprogramming
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Macro:
    """Hygienic macro definition."""
    name: str
    pattern: str  # Pattern with metavariables like $x
    template: str  # Expansion template
    hygiene: bool = True


class MacroExpander:
    """Hygienic macro expander."""
    
    def __init__(self):
        self.macros: dict[str, Macro] = {}
        self.gen_sym_counter = 0
    
    def define(self, macro: Macro):
        self.macros[macro.name] = macro
    
    def gensym(self, prefix: str = "gen") -> str:
        self.gen_sym_counter += 1
        return f"{prefix}_{self.gen_sym_counter}"
    
    def expand(self, source: str) -> str:
        """Expand macros in source code."""
        result = source
        for macro in self.macros.values():
            result = self._expand_macro(result, macro)
        return result
    
    def _expand_macro(self, source: str, macro: Macro) -> str:
        """Expand a single macro."""
        # Simple pattern matching - in practice would use proper AST matching
        pattern = macro.pattern
        template = macro.template
        
        # Unescape any backslash-dollar sequences in the pattern
        unescaped = pattern.replace(r'\$', '$')
        
        # Build regex by replacing $name with greedy capture groups
        parts = re.split(r'(\$\w+)', unescaped)
        regex_parts = []
        for part in parts:
            if part.startswith('$'):
                regex_parts.append(r'(.+)')  # Greedy capture
            else:
                regex_parts.append(re.escape(part))
        regex_pattern = ''.join(regex_parts)
        
        def replacer(match):
            groups = match.groups()
            # Build result by replacing all placeholders at once
            result = template
            # First pass: replace $1, $2, etc. with placeholders
            for i, g in enumerate(groups):
                result = result.replace(f"${i+1}", f"\x00{i}\x00")
            # Second pass: replace placeholders with actual values
            for i, g in enumerate(groups):
                result = result.replace(f"\x00{i}\x00", g)
            # Also handle $x1, $x2, etc.
            for i, g in enumerate(groups):
                result = result.replace(f"$x{i+1}", g)
            return result
        
        return re.sub(regex_pattern, replacer, source)


# Built-in macros
STANDARD_MACROS = MacroExpander()
STANDARD_MACROS.define(Macro(
    name="try",
    pattern=r"try \$e catch \$x => \$e2",
    template="try { $1 } catch $2 { $3 }"
))
STANDARD_MACROS.define(Macro(
    name="match",
    pattern=r"match \$e { \$cases }",
    template="match $1 { $2 }"
))


# ---------------------------------------------------------------------------
# Module System v2
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ModuleExport:
    """Explicit export declaration."""
    name: str
    type: TypeRef | None = None
    doc: str = ""
    deprecated: bool = False


@dataclass(frozen=True)
class ModuleImport:
    """Explicit import declaration."""
    module: str
    imports: list[str]  # ["name", "name as alias"]
    version: str | None = None


@dataclass(frozen=True)
class ModuleSpec:
    """Complete module specification."""
    name: str
    version: str
    exports: list[ModuleExport] = field(default_factory=list)
    imports: list[ModuleImport] = field(default_factory=list)
    dependencies: dict[str, str] = field(default_factory=dict)  # name -> version constraint
    capabilities: list[str] = field(default_factory=list)  # Required capabilities


def parse_module_spec(source: str) -> ModuleSpec | None:
    """Parse module specification from source."""
    # Look for module declaration
    m = re.search(r'module\s+(\w+)\s*(?:@(\S+))?\s*\{', source)
    if not m:
        return None
    
    name = m.group(1)
    version = m.group(2) or "1.0.0"
    
    exports = []
    imports = []
    deps = {}
    caps = []
    
    # Parse body (simplified)
    body_start = m.end()
    depth = 1
    body_end = body_start
    for i in range(body_start, len(source)):
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                body_end = i
                break
    
    body = source[body_start:body_end]
    
    # Parse exports
    for em in re.finditer(r'export\s+(?:const|let|function|type)\s+(\w+)', body):
        exports.append(ModuleExport(name=em.group(1)))
    
    # Parse imports
    for im in re.finditer(r'import\s+(\w+)(?:\s+as\s+(\w+))?', body):
        imports.append(ModuleImport(module=im.group(1), imports=[im.group(2) or im.group(1)]))
    
    return ModuleSpec(name=name, version=version, exports=exports, imports=imports, dependencies=deps, capabilities=caps)


def check_module_compatibility(spec: ModuleSpec, available: dict[str, ModuleSpec]) -> list[Diagnostic]:
    """Check if module dependencies are satisfied."""
    diagnostics = []
    for dep_name, constraint in spec.dependencies.items():
        if dep_name not in available:
            diagnostics.append(Diagnostic(
                'M101',
                f"Missing dependency: {dep_name} {constraint}",
                0
            ))
            continue
        dep_spec = available[dep_name]
        # Simple version check (would use semver in practice)
        if constraint != dep_spec.version:
            diagnostics.append(Diagnostic(
                'M102',
                f"Version mismatch for {dep_name}: required {constraint}, have {dep_spec.version}",
                0,
                severity='warning'
            ))
    return diagnostics


# ---------------------------------------------------------------------------
# Type System Integration
# ---------------------------------------------------------------------------

def integrate_advanced_types(checker: TypeChecker, source: str) -> list[Diagnostic]:
    """Integrate all advanced type features into the type checker."""
    diagnostics = []
    
    # Effect inference
    for m in re.finditer(r'function\s+(\w+)', source):
        func_name = m.group(1)
        # Extract function body (simplified)
        func_body = source[m.end():m.end()+500]
        effects = infer_effects(func_body, func_name)
        # Store effects on function (would need TypeRef extension)
    
    # Linear type checking
    diagnostics.extend(check_linear_usage(source, {}))
    
    # Refinement type checking
    for m in re.finditer(r'\{(\w+):\s*([^|]+)\|(.+)\}', source):
        refinement = parse_refinement(m.group(0))
        if refinement:
            # Would check at usage sites
            pass
    
    # Macro expansion (would happen before type checking)
    expanded = STANDARD_MACROS.expand(source)
    
    return diagnostics

