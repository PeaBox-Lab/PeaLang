from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from .parser import parse_source
from .interpreter import Interpreter
from .errors import PeaError

class DebugPause(BaseException): pass

@dataclass
class Breakpoint:
    line:int
    condition:str|None=None
    hit_condition:str|None=None
    log_message:str|None=None
    enabled:bool=True
    hit_count:int=0
    source:str|None=None

class DebugSession:
    """Synchronous debugger core used by the CLI and DAP adapter.

    v0.16 adds conditional/hit-count breakpoints, captured function frames,
    per-frame scopes, imported-source tracking, exception stops, and stable
    DAP-oriented stop/termination records.
    """
    def __init__(self,source,source_name='<debug>',output=None,base_dir=None):
        self.source=source; self.source_name=str(source_name)
        self.program=parse_source(source,self.source_name)
        self.breakpoints={}; self.mode='pause'; self.events=[]; self._paused=None
        self.exception_breakpoints=set(); self.terminated=False; self.last_exception=None
        self._frames=[]; self._scope_refs={}; self._next_ref=10
        self.sources={self.source_name:source}
        self.vm=Interpreter(output=output,base_dir=base_dir,debug_hook=self._hook)

    def add_breakpoint(self,line,condition=None,hit_condition=None,log_message=None,source=None):
        source=str(source or self.source_name)
        b=Breakpoint(int(line),condition,hit_condition,log_message,True,0,source)
        self.breakpoints[(source,b.line)]=b
        return asdict(b)

    def clear_breakpoints(self,source=None):
        if source is None:self.breakpoints.clear()
        else:
            source=str(source)
            self.breakpoints={k:v for k,v in self.breakpoints.items() if k[0]!=source}

    def remove_breakpoint(self,line,source=None):
        return self.breakpoints.pop((str(source or self.source_name),int(line)),None) is not None

    def set_exception_breakpoints(self,filters):self.exception_breakpoints=set(filters or [])

    def _builtins(self):
        return {'range','len','str','number','int','type','upper','lower','split','join','append','keys','values','read','write','exists','sqrt','round','sleep','file','path','json','csv','env','datetime','regex','http','process','task','workflow','ai','tool','agent','skill'}

    def _user_vars(self,env=None):
        values=(env or self.vm.env).snapshot()
        return {k:v for k,v in values.items() if k not in self._builtins()}

    def _capture_frames(self,node,source,line):
        frames=[]
        stack=list(getattr(self.vm,'call_stack',[]))
        for idx,frame in enumerate(reversed(stack),start=1):
            frames.append({'id':idx,'name':frame.get('name','<function>'),'source':frame.get('source',source),'line':frame.get('line',line),'locals':dict(frame.get('locals',{}))})
        frames.append({'id':len(frames)+1,'name':'<module>','source':source,'line':line,'locals':self._user_vars()})
        self._frames=frames
        self._scope_refs={};self._next_ref=10

    def _eval_condition(self,text):
        if not text:return True
        try:return bool(self.evaluate(text))
        except Exception:return False

    def _hit_matches(self,expr,count):
        if not expr:return True
        text=str(expr).strip()
        try:
            if text.startswith('>='):return count>=int(text[2:])
            if text.startswith('=='):return count==int(text[2:])
            if text.startswith('%'):return count%int(text[1:])==0
            return count==int(text)
        except (ValueError,ZeroDivisionError):return False

    def variables(self,scope='locals',frame_id=1):
        if scope=='globals':return self._user_vars(self.vm.global_env)
        if self.terminated:return self._user_vars()
        for frame in self._frames:
            if frame['id']==frame_id:return dict(frame.get('locals',{}))
        return self._user_vars()

    def stack(self):
        if self._frames:return [{k:v for k,v in f.items() if k!='locals'} for f in self._frames]
        return [{'id':1,'name':'<module>','source':self.source_name,'line':1}]

    def evaluate(self,expression,frame_id=None):
        old=self.vm.env
        try:
            if frame_id:
                frame=next((x for x in self._frames if x['id']==frame_id),None)
                if frame:
                    from .environment import Env
                    env=Env(self.vm.global_env)
                    for k,v in frame.get('locals',{}).items():
                        if k not in env.values:env.define(k,v)
                    self.vm.env=env
            return self.vm.eval(parse_source('print '+expression,self.source_name).statements[0].value)
        finally:self.vm.env=old

    def _hook(self,vm,node):
        source=str(vm.source_name);line=node.span.line if node.span else 1
        bp=self.breakpoints.get((source,line)) or self.breakpoints.get((self.source_name,line))
        stop=self.mode in ('step_in','step_over')
        reason='step'
        if bp and bp.enabled:
            bp.hit_count+=1
            if self._eval_condition(bp.condition) and self._hit_matches(bp.hit_condition,bp.hit_count):
                if bp.log_message:
                    vm.output(bp.log_message)
                else:stop=True;reason='breakpoint'
        if stop:
            self._paused=node;self._capture_frames(node,source,line)
            event={'reason':reason,'line':line,'source':source,'statement':type(node).__name__,'variables':self._user_vars(),'hitBreakpointIds':[line] if reason=='breakpoint' else []}
            self.events.append(event);raise DebugPause()

    def _execute(self):
        try:
            self.vm.run(self.program,self.source_name);self.terminated=True
            return {'reason':'end','terminated':True,'variables':self._user_vars()}
        except DebugPause:return self.events[-1]
        except PeaError as ex:
            self.last_exception=ex;self.terminated=True
            event={'reason':'exception','text':str(ex),'source':ex.source_name,'line':ex.span.line if ex.span else 1}
            self.events.append(event)
            if self.exception_breakpoints:return event
            raise

    def start(self):self.mode='continue';return self._execute()

    def continue_run(self):
        if self._paused:
            node=self._paused;self._paused=None;self.vm.debug_hook=None
            try:self.vm.exec_stmt(node)
            finally:self.vm.debug_hook=self._hook
        self.mode='continue';return self._execute_remaining()

    def step_in(self):return self._resume_step('step_in')
    def step_over(self):return self._resume_step('step_over')
    def step_out(self):return self.continue_run()

    def _resume_step(self,mode):
        if self._paused:
            node=self._paused;self._paused=None;self.vm.debug_hook=None
            try:self.vm.exec_stmt(node)
            finally:self.vm.debug_hook=self._hook
        self.mode=mode;return self._execute_remaining()

    def _execute_remaining(self):
        line=self.events[-1]['line'] if self.events else 0
        pending=[x for x in self.program.statements if (x.span.line if x.span else 1)>line]
        try:
            for node in pending:self.vm.exec_stmt(node)
            self.terminated=True;return {'reason':'end','terminated':True,'variables':self._user_vars()}
        except DebugPause:return self.events[-1]
        except PeaError as ex:
            self.last_exception=ex;self.terminated=True
            event={'reason':'exception','text':str(ex),'source':ex.source_name,'line':ex.span.line if ex.span else 1};self.events.append(event)
            if self.exception_breakpoints:return event
            raise
