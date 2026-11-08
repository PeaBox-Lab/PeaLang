from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json,math,os,time
from concurrent.futures import ThreadPoolExecutor
from .ast_nodes import *
from .environment import Env
from .errors import PeaError
from .parser import parse_source

CURRENT_INTERPRETER = None

def set_current_interpreter(interp):
    global CURRENT_INTERPRETER
    CURRENT_INTERPRETER = interp
from .stdlib import build_standard_library
from .ai import build_ai_namespace
from .skills import SkillRegistry
from .project import load_manifest, resolve_module
from .agents import ToolRegistry,AgentRuntime
class ReturnSignal(Exception):
    def __init__(self,v):self.value=v
class BreakSignal(Exception):pass
class ContinueSignal(Exception):pass
@dataclass
class UserFunction:params:list;body:list[Stmt];closure:Env
class Interpreter:
    def __init__(self,output=None,base_dir=None,allow_process=False,project_root=None,dependencies=None,debug_hook=None,permissions=None):
        self.output=output or print;self.debug_hook=debug_hook;self.call_stack=[];self.global_env=Env();self.env=self.global_env;self.module_exports=None;self.base_dir=Path(base_dir or '.').resolve();self.source_name='<input>';self.imported=set();self.project_root=Path(project_root).resolve() if project_root else self.base_dir;self.dependencies=dependencies or {}
        def _enumerate(iterable,start=0): return [[i,v] for i,v in enumerate(iterable,int(start))]
        def _zip(*args): return [list(x) for x in zip(*args)]
        def _sorted(iterable,key=None,reverse=False):
            if key is None: return sorted(iterable,reverse=reverse)
            return sorted(iterable,key=lambda x: self.invoke_user_function(key,[x]) if isinstance(key,UserFunction) else key(x),reverse=reverse)
        def _reversed(iterable): return list(reversed(list(iterable)))
        def _map(fn,iterable): return [self.invoke_user_function(fn,[x]) if isinstance(fn,UserFunction) else fn(x) for x in iterable]
        def _filter(fn,iterable): return [x for x in iterable if (self.invoke_user_function(fn,[x]) if isinstance(fn,UserFunction) else fn(x))]
        def _any(iterable): return any(iterable)
        def _all(iterable): return all(iterable)
        def _get(obj,key,default=None):
            try:
                if isinstance(obj,dict): return obj.get(key,default)
                return obj[key]
            except Exception: return default
        def _has(obj,key):
            try: return key in obj
            except Exception: return False
        def _merge(*objs):
            r={}
            for o in objs:
                if isinstance(o,dict): r.update(o)
            return r
        def _pop(obj,key=None):
            try:
                if isinstance(obj,list): return obj.pop() if key is None else obj.pop(int(key))
                if isinstance(obj,dict): return obj.pop(key,None)
            except Exception: return None
        def _push(obj,val): 
            if isinstance(obj,list): obj.append(val); return obj
            return obj
        def _slice(obj,start=None,end=None,step=None): return obj[start:end:step]
        def _contains(obj,val):
            try: return val in obj
            except Exception: return False
        def _safe(fn,default=None):
            try:
                if isinstance(fn,UserFunction): return self.invoke_user_function(fn,[])
                return fn()
            except Exception: return default
        builtins={'range':lambda *a:list(range(*map(int,a))),'len':len,'str':lambda x:self.stringify(x),'bool':bool,'number':lambda x:float(x),'int':lambda x:int(float(x)),'float':lambda x:float(x),'type':lambda x:type(x).__name__,'upper':lambda x:str(x).upper(),'lower':lambda x:str(x).lower(),'trim':lambda x:str(x).strip(),'split':lambda x,s=None:str(x).split(s),'join':lambda s,x:str(s).join(map(str,x)),'replace':lambda s,a,b:str(s).replace(str(a),str(b)),'starts_with':lambda s,p:str(s).startswith(str(p)),'ends_with':lambda s,p:str(s).endswith(str(p)),'contains':_contains,'append':self._append,'push':_push,'pop':_pop,'get':_get,'has':_has,'merge':_merge,'slice':_slice,'keys':lambda d:list(d.keys()) if isinstance(d,dict) else list(range(len(d))),'values':lambda d:list(d.values()) if isinstance(d,dict) else list(d),'items':lambda d:[[k,v] for k,v in d.items()] if isinstance(d,dict) else _enumerate(d),'read':lambda p:Path(p).read_text(encoding='utf-8'),'write':self._write,'exists':os.path.exists,'sqrt':math.sqrt,'abs':abs,'round':round,'min':min,'max':max,'sum':lambda x,start=0:sum(x,start),'sleep':time.sleep,'enumerate':_enumerate,'zip':_zip,'sorted':_sorted,'reversed':_reversed,'map':_map,'filter':_filter,'any':_any,'all':_all,'list':lambda x=None:list(x) if x is not None else [],'dict':lambda x=None:dict(x) if x is not None else {},'json_parse':lambda s:json.loads(s),'json_dump':lambda x,indent=None:json.dumps(x,indent=indent,ensure_ascii=False,default=str),'safe':_safe,'now_ms':lambda:int(time.time()*1000)}
        for k,v in builtins.items():self.global_env.define(k,v,True)
        for k,v in build_standard_library(allow_process=allow_process,permissions=permissions).items():self.global_env.define(k,v,True)
        ai_ns,self.ai_service=build_ai_namespace();self.global_env.define('ai',ai_ns,True)
        from .web import build_web_namespace
        from .analysis import build_analysis_namespace
        from .interop import build_interop_namespace
        from .ux import build_ux_namespace
        self.web_namespace=build_web_namespace(self);self.global_env.define('web',self.web_namespace,True)
        self.analysis_namespace=build_analysis_namespace();self.global_env.define('analysis',self.analysis_namespace,True)
        self.interop_namespace=build_interop_namespace();self.global_env.define('interop',self.interop_namespace,True)
        self.ux_namespace=build_ux_namespace();self.global_env.define('ux',self.ux_namespace,True)
        self.tool_registry=ToolRegistry(self.invoke_user_function);self.agent_runtime=AgentRuntime(self.ai_service,self.tool_registry);self.global_env.define('tool',{'register':self.tool_registry.register,'list':self.tool_registry.list,'describe':self.tool_registry.describe,'call':self.tool_registry.call},True);self.global_env.define('agent',{'define':self.agent_runtime.define,'run':self.agent_runtime.run,'tool':self.agent_runtime.tool},True)
        self.skill_registry=SkillRegistry(self.base_dir);self.global_env.define('skill',{'load':self.skill_registry.load,'list':self.skill_registry.list,'get':self.skill_registry.get,'render':self.skill_registry.render},True)
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
            from .web import set_current_interpreter as set_web_current
            set_web_current(self)
            set_current_interpreter(self)
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
        if self.debug_hook:self.debug_hook(self,s)
        try:
            if isinstance(s,VarDecl):self.env.define(s.name,self.eval(s.value),s.constant);return None
            if isinstance(s,DestructureDecl):
                value=self.eval(s.value);self.bind_pattern(s.pattern,value,self.env,s.constant);return None
            if isinstance(s,MatchStmt):
                value=self.eval(s.value)
                for case in s.cases:
                    env=Env(self.env)
                    if not self.match_pattern(case.pattern,value,env):continue
                    if case.guard is not None:
                        old=self.env;self.env=env
                        try:
                            if not self.truth(self.eval(case.guard)):continue
                        finally:self.env=old
                    old=self.env;self.env=env
                    try:return self.exec_block(case.body,env)
                    finally:self.env=old
                return None
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
                    e=Env(self.env)
                    if getattr(s,'pattern',None):self.bind_pattern(s.pattern,v,e)
                    else:e.define(s.name,v)
                    try:self.exec_block(s.body,e)
                    except ContinueSignal:continue
                    except BreakSignal:break
                return None
            if isinstance(s,FunctionStmt):self.env.define(s.name,UserFunction(s.params,s.body,self.env),True);return None
            if isinstance(s,ReturnStmt):raise ReturnSignal(self.eval(s.value) if s.value else None)
            if isinstance(s,BreakStmt):raise BreakSignal()
            if isinstance(s,ContinueStmt):raise ContinueSignal()
            if isinstance(s,ImportStmt):return self.import_file(s.path,s,s.alias)
            if isinstance(s,ExportStmt):
                if self.module_exports is None:raise PeaError('export is only valid inside an imported module',s.span,self.source_name)
                self.module_exports.add(s.name);return None
            if isinstance(s,AssertStmt):
                if not self.truth(self.eval(s.condition)):
                    message=self.stringify(self.eval(s.message)) if s.message else 'Assertion failed'
                    raise PeaError(message,s.span,self.source_name)
                return None
            if isinstance(s,ThrowStmt):raise PeaError(self.stringify(self.eval(s.value)),s.span,self.source_name)
            if isinstance(s,TryStmt):
                try:return self.exec_block(s.try_body)
                except PeaError as ex:
                    if s.catch_body is None:raise
                    catchenv=Env(self.env)
                    if s.catch_name:catchenv.define(s.catch_name,{'message':ex.message,'source':ex.source_name,'line':ex.span.line if ex.span else None,'column':ex.span.col if ex.span else None},True)
                    return self.exec_block(s.catch_body,catchenv)
                finally:
                    if s.finally_body is not None:self.exec_block(s.finally_body)
            raise PeaError(f'Unknown statement {type(s).__name__}',s.span,self.source_name)
        except (PeaError,ReturnSignal,BreakSignal,ContinueSignal):raise
        except Exception as ex:raise PeaError(str(ex),s.span,self.source_name) from ex
    def import_file(self,name,node,alias=None):
        path=resolve_module(name,self.base_dir,self.project_root,self.dependencies)
        if not path.is_file():raise PeaError(f"Module not found: {name}",node.span,self.source_name)
        if alias is None:
            if path in self.imported:return None
            self.imported.add(path);src=path.read_text(encoding='utf-8');oldbase=self.base_dir;oldskill=self.skill_registry.base_dir;self.base_dir=path.parent;self.skill_registry.base_dir=path.parent
            try:return self.run(parse_source(src,str(path)),str(path))
            finally:self.base_dir=oldbase;self.skill_registry.base_dir=oldskill
        src=path.read_text(encoding='utf-8');module_env=Env(self.global_env);oldenv=self.env;oldbase=self.base_dir;oldskill=self.skill_registry.base_dir;oldexports=self.module_exports
        self.env=module_env;self.base_dir=path.parent;self.skill_registry.base_dir=path.parent;self.module_exports=set()
        try:
            self.run(parse_source(src,str(path)),str(path));names=self.module_exports;values={n:module_env.values[n] for n in names if n in module_env.values};self.global_env.define(alias,values,True);return values
        finally:self.env=oldenv;self.base_dir=oldbase;self.skill_registry.base_dir=oldskill;self.module_exports=oldexports

    def invoke_user_function(self, f, args):
        required=sum(1 for p in f.params if getattr(p,'default',None) is None)
        if len(args)<required or len(args)>len(f.params):raise PeaError(f'Expected {required} to {len(f.params)} arguments, got {len(args)}')
        env=Env(f.closure);old=self.env;self.env=env
        try:
            for i,p in enumerate(f.params):
                value=args[i] if i<len(args) else self.eval(p.default)
                env.define(p.name,value)
            try:return self.exec_block(f.body,env)
            except ReturnSignal as result:return result.value
        finally:self.env=old

    def match_pattern(self, pattern, value, env):
        from .ast_nodes import WildcardPattern, LiteralPattern, VariablePattern, ListPattern, DictPattern, OrPattern
        if isinstance(pattern, WildcardPattern):
            return True
        if isinstance(pattern, LiteralPattern):
            return value == pattern.value
        if isinstance(pattern, VariablePattern):
            env.define(pattern.name, value, False)
            return True
        if isinstance(pattern, OrPattern):
            for p in pattern.patterns:
                trial = Env(env.parent if hasattr(env,'parent') else self.env)
                # bind into trial then copy? Simpler: try binding in a child env of env's parent
                saved = dict(env.values)
                ok = self.match_pattern(p, value, env)
                if ok:
                    return True
                env.values.clear(); env.values.update(saved)
            return False
        if isinstance(pattern, ListPattern):
            if not isinstance(value, list):
                return False
            if pattern.rest is None:
                if len(value) != len(pattern.elements):
                    return False
            else:
                if len(value) < len(pattern.elements):
                    return False
            for i, p in enumerate(pattern.elements):
                if not self.match_pattern(p, value[i], env):
                    return False
            if pattern.rest is not None:
                env.define(pattern.rest, value[len(pattern.elements):], False)
            return True
        if isinstance(pattern, DictPattern):
            if not isinstance(value, dict):
                return False
            for key, p in pattern.fields:
                if key not in value:
                    return False
                if not self.match_pattern(p, value[key], env):
                    return False
            return True
        return False

    def bind_pattern(self, pattern, value, env, const=False):
        from .ast_nodes import WildcardPattern, LiteralPattern, VariablePattern, ListPattern, DictPattern
        if isinstance(pattern, WildcardPattern):
            return
        if isinstance(pattern, LiteralPattern):
            return
        if isinstance(pattern, VariablePattern):
            env.define(pattern.name, value, const)
            return
        if isinstance(pattern, ListPattern):
            if not isinstance(value, list):
                return
            for i, p in enumerate(pattern.elements):
                if i < len(value):
                    self.bind_pattern(p, value[i], env, const)
            if pattern.rest is not None:
                env.define(pattern.rest, value[len(pattern.elements):], const)
            return
        if isinstance(pattern, DictPattern):
            if not isinstance(value, dict):
                return
            for key, p in pattern.fields:
                self.bind_pattern(p, value.get(key), env, const)
            return

    def run_parallel(self, expressions, node):
        # Parallel blocks are intentionally limited to expressions. Shared PeaLang
        # environment mutation inside the block is not supported in v0.5.0.
        if not expressions:return []
        def evaluate(expr):return self.eval(expr)
        try:
            with ThreadPoolExecutor(max_workers=min(8,len(expressions))) as pool:
                futures=[pool.submit(evaluate,e) for e in expressions]
                return [f.result() for f in futures]
        except PeaError:raise
        except Exception as ex:raise PeaError(str(ex),node.span,self.source_name) from ex

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
            return {'+':lambda:a+b,'-':lambda:a-b,'*':lambda:a*b,'/':lambda:a/b,'%':lambda:a%b,'**':lambda:a**b,'==':lambda:a==b,'!=':lambda:a!=b,'<':lambda:a<b,'<=':lambda:a<=b,'>':lambda:a>b,'>=':lambda:a>=b,'in':lambda:a in b,'not in':lambda:a not in b}[op]()
        except KeyError:raise PeaError(f'Unknown operator {op}',getattr(node,'span',None),self.source_name)
        except Exception as ex:raise PeaError(str(ex),getattr(node,'span',None),self.source_name) from ex
    def eval(self,e):
        if isinstance(e,Literal):return e.value
        if isinstance(e,FunctionExpr):return UserFunction(e.params,e.body,self.env)
        if isinstance(e,ComprehensionExpr):
            result=[]
            for value in self.eval(e.iterable):
                env=Env(self.env)
                if getattr(e,'pattern',None):self.bind_pattern(e.pattern,value,env)
                else:env.define(e.name,value)
                old=self.env;self.env=env
                try:
                    if e.condition is None or self.truth(self.eval(e.condition)):result.append(self.eval(e.value))
                finally:self.env=old
            return result
        if isinstance(e,DictComprehensionExpr):
            result={}
            for value in self.eval(e.iterable):
                env=Env(self.env)
                if getattr(e,'pattern',None):self.bind_pattern(e.pattern,value,env)
                else:env.define(e.name,value)
                old=self.env;self.env=env
                try:
                    if e.condition is None or self.truth(self.eval(e.condition)):result[self.eval(e.key)]=self.eval(e.value)
                finally:self.env=old
            return result
        if isinstance(e,MatchExpr):
            value=self.eval(e.value)
            for case in e.cases:
                env=Env(self.env)
                if not self.match_pattern(case.pattern,value,env):continue
                if case.guard is not None:
                    old=self.env;self.env=env
                    try:
                        if not self.truth(self.eval(case.guard)):continue
                    finally:self.env=old
                old=self.env;self.env=env
                try:
                    if getattr(case,'value',None) is not None:return self.eval(case.value)
                    if case.body:
                        r=None
                        for s in case.body:r=self.exec_stmt(s)
                        return r
                    return None
                finally:self.env=old
            return None
        if isinstance(e,Variable):return self.env.get(e.name,e.span,self.source_name)
        if isinstance(e,ListExpr):return [self.eval(x) for x in e.items]
        if isinstance(e,DictExpr):return {self.eval(k):self.eval(v) for k,v in e.pairs}
        if isinstance(e,InterpolatedString):return ''.join(x if isinstance(x,str) else self.stringify(self.eval(x)) for x in e.parts)
        if isinstance(e,ParallelExpr):return self.run_parallel(e.expressions,e)
        if isinstance(e,Unary):
            v=self.eval(e.value);return -v if e.op=='-' else not self.truth(v)
        if isinstance(e,Binary):
            if e.op=='and':
                left=self.eval(e.left);return self.eval(e.right) if self.truth(left) else False
            if e.op=='or':
                left=self.eval(e.left);return left if self.truth(left) else self.eval(e.right)
            if e.op=='??':
                left=self.eval(e.left);return left if left is not None else self.eval(e.right)
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
            if isinstance(f,UserFunction):return self.invoke_user_function(f,args)
            if callable(f):
                try:return f(*args)
                except PeaError:raise
                except Exception as ex:raise PeaError(str(ex),e.span,self.source_name) from ex
            raise PeaError('Value is not callable',e.span,self.source_name)
        if isinstance(e,OptionalProperty):
            target=self.eval(e.target)
            if target is None:return None
            try:return target[e.name] if isinstance(target,dict) else getattr(target,e.name)
            except (KeyError,AttributeError):return None
        if isinstance(e,OptionalIndex):
            target=self.eval(e.target)
            if target is None:return None
            try:return target[self.eval(e.index)]
            except Exception:return None
        if isinstance(e,OptionalCall):
            callee=self.eval(e.callee)
            if callee is None:return None
            args=[self.eval(x) for x in e.args]
            if isinstance(callee,UserFunction):return self.invoke_user_function(callee,args)
            if callable(callee):
                try:return callee(*args)
                except Exception:return None
            return None
        raise PeaError(f'Unknown expression {type(e).__name__}',getattr(e,'span',None),self.source_name)
