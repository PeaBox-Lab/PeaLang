from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json,math,os,time
from .ast_nodes import *
from .environment import Env
from .errors import PeaError
from .parser import parse_source
class ReturnSignal(Exception):
    def __init__(self,v):self.value=v
class BreakSignal(Exception):pass
class ContinueSignal(Exception):pass
@dataclass
class UserFunction:params:list[str];body:list[Stmt];closure:Env
class Interpreter:
    def __init__(self,output=None,base_dir=None):
        self.output=output or print;self.global_env=Env();self.env=self.global_env;self.base_dir=Path(base_dir or '.').resolve();self.source_name='<input>';self.imported=set()
        builtins={'range':lambda *a:list(range(*map(int,a))),'len':len,'str':lambda x:self.stringify(x),'number':lambda x:float(x),'int':lambda x:int(float(x)),'type':lambda x:type(x).__name__,'upper':lambda x:str(x).upper(),'lower':lambda x:str(x).lower(),'split':lambda x,s=None:str(x).split(s),'join':lambda s,x:str(s).join(map(str,x)),'append':self._append,'keys':lambda d:list(d.keys()),'values':lambda d:list(d.values()),'json':lambda x:json.dumps(x,indent=2),'read':lambda p:Path(p).read_text(encoding='utf-8'),'write':self._write,'exists':os.path.exists,'sqrt':math.sqrt,'round':round,'sleep':time.sleep}
        for k,v in builtins.items():self.global_env.define(k,v,True)
    def _append(self,a,v):a.append(v);return a
    def _write(self,p,c):Path(p).write_text(str(c),encoding='utf-8');return p
    def stringify(self,v):
        if v is None:return 'null'
        if v is True:return 'true'
        if v is False:return 'false'
        if isinstance(v,float) and v.is_integer():return str(int(v))
        if isinstance(v,(list,dict)):return json.dumps(v,ensure_ascii=False)
        return str(v)
    def run(self,program,source_name='<input>'):
        old=self.source_name;self.source_name=source_name
        try:
            result=None
            for stmt in program.statements:result=self.exec_stmt(stmt)
            return result
        finally:self.source_name=old
    def exec_block(self,body,env=None):
        old=self.env;self.env=env or Env(old)
        try:
            r=None
            for s in body:r=self.exec_stmt(s)
            return r
        finally:self.env=old
    def exec_stmt(self,s):
        try:
            if isinstance(s,VarDecl):self.env.define(s.name,self.eval(s.value),s.constant);return None
            if isinstance(s,Assign):
                val=self.eval(s.value)
                if s.op!='=':val=self.apply(s.op[0],self.read_target(s.target),val,s)
                return self.write_target(s.target,val,s)
            if isinstance(s,PrintStmt):self.output(self.stringify(self.eval(s.value)));return None
            if isinstance(s,ExprStmt):return self.eval(s.value)
            if isinstance(s,IfStmt):return self.exec_block(s.then_body if self.truth(self.eval(s.condition)) else (s.else_body or []))
            if isinstance(s,WhileStmt):
                while self.truth(self.eval(s.condition)):
                    try:self.exec_block(s.body)
                    except ContinueSignal:continue
                    except BreakSignal:break
                return None
            if isinstance(s,ForStmt):
                for v in self.eval(s.iterable):
                    e=Env(self.env);e.define(s.name,v)
                    try:self.exec_block(s.body,e)
                    except ContinueSignal:continue
                    except BreakSignal:break
                return None
            if isinstance(s,FunctionStmt):self.env.define(s.name,UserFunction(s.params,s.body,self.env),True);return None
            if isinstance(s,ReturnStmt):raise ReturnSignal(self.eval(s.value) if s.value else None)
            if isinstance(s,BreakStmt):raise BreakSignal()
            if isinstance(s,ContinueStmt):raise ContinueSignal()
            if isinstance(s,ImportStmt):return self.import_file(s.path,s)
            raise PeaError(f'Unknown statement {type(s).__name__}',s.span,self.source_name)
        except (PeaError,ReturnSignal,BreakSignal,ContinueSignal):raise
        except Exception as ex:raise PeaError(str(ex),s.span,self.source_name) from ex
    def import_file(self,name,node):
        path=(self.base_dir/name).resolve()
        if path.suffix!='.pea':path=path.with_suffix('.pea')
        if path in self.imported:return None
        if not path.is_file():raise PeaError(f"Module not found: {name}",node.span,self.source_name)
        self.imported.add(path);src=path.read_text(encoding='utf-8');oldbase=self.base_dir;self.base_dir=path.parent
        try:return self.run(parse_source(src,str(path)),str(path))
        finally:self.base_dir=oldbase
    def read_target(self,t):return self.eval(t)
    def write_target(self,t,v,node):
        if isinstance(t,Variable):return self.env.set(t.name,v,t.span,self.source_name)
        if isinstance(t,Index):
            target=self.eval(t.target);key=self.eval(t.index);target[key]=v;return v
        if isinstance(t,Property):
            target=self.eval(t.target)
            if isinstance(target,dict):target[t.name]=v;return v
            setattr(target,t.name,v);return v
        raise PeaError('Invalid assignment target',getattr(t,'span',node.span),self.source_name)
    def truth(self,v):return bool(v)
    def apply(self,op,a,b,node=None):
        try:
            return {'+':lambda:a+b,'-':lambda:a-b,'*':lambda:a*b,'/':lambda:a/b,'%':lambda:a%b,'==':lambda:a==b,'!=':lambda:a!=b,'<':lambda:a<b,'<=':lambda:a<=b,'>':lambda:a>b,'>=':lambda:a>=b}[op]()
        except KeyError:raise PeaError(f'Unknown operator {op}',getattr(node,'span',None),self.source_name)
        except Exception as ex:raise PeaError(str(ex),getattr(node,'span',None),self.source_name) from ex
    def eval(self,e):
        if isinstance(e,Literal):return e.value
        if isinstance(e,Variable):return self.env.get(e.name,e.span,self.source_name)
        if isinstance(e,ListExpr):return [self.eval(x) for x in e.items]
        if isinstance(e,DictExpr):return {self.eval(k):self.eval(v) for k,v in e.pairs}
        if isinstance(e,InterpolatedString):return ''.join(x if isinstance(x,str) else self.stringify(self.eval(x)) for x in e.parts)
        if isinstance(e,Unary):
            v=self.eval(e.value);return -v if e.op=='-' else not self.truth(v)
        if isinstance(e,Binary):
            if e.op=='and':
                left=self.eval(e.left);return self.eval(e.right) if self.truth(left) else False
            if e.op=='or':
                left=self.eval(e.left);return left if self.truth(left) else self.eval(e.right)
            return self.apply(e.op,self.eval(e.left),self.eval(e.right),e)
        if isinstance(e,Index):
            try:return self.eval(e.target)[self.eval(e.index)]
            except Exception as ex:raise PeaError(str(ex),e.span,self.source_name) from ex
        if isinstance(e,Property):
            target=self.eval(e.target)
            try:return target[e.name] if isinstance(target,dict) else getattr(target,e.name)
            except (KeyError,AttributeError) as ex:raise PeaError(f"Property '{e.name}' not found",e.span,self.source_name) from ex
        if isinstance(e,Call):
            f=self.eval(e.callee);args=[self.eval(x) for x in e.args]
            if isinstance(f,UserFunction):
                if len(args)!=len(f.params):raise PeaError(f'Expected {len(f.params)} arguments, got {len(args)}',e.span,self.source_name)
                env=Env(f.closure)
                for n,v in zip(f.params,args):env.define(n,v)
                try:return self.exec_block(f.body,env)
                except ReturnSignal as r:return r.value
            if callable(f):
                try:return f(*args)
                except Exception as ex:raise PeaError(str(ex),e.span,self.source_name) from ex
            raise PeaError('Value is not callable',e.span,self.source_name)
        raise PeaError(f'Unknown expression {type(e).__name__}',getattr(e,'span',None),self.source_name)
