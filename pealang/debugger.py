

from __future__ import annotations
from dataclasses import dataclass,asdict
from .parser import parse_source
from .interpreter import Interpreter
from .environment import Env
class DebugPause(Exception): pass
@dataclass
class Breakpoint: line:int; condition:str|None=None; enabled:bool=True; hit_count:int=0
class DebugSession:
 def __init__(self,source,source_name='<debug>',output=None,base_dir=None):
  self.source=source;self.source_name=source_name;self.program=parse_source(source,source_name);self.breakpoints={};self.mode='pause';self.events=[];self._paused=None
  self.vm=Interpreter(output=output,base_dir=base_dir,debug_hook=self._hook)
 def add_breakpoint(self,line,condition=None):
  b=Breakpoint(int(line),condition);self.breakpoints[b.line]=b;return asdict(b)
 def remove_breakpoint(self,line):return self.breakpoints.pop(int(line),None) is not None
 def _user_vars(self):
  hidden={'range','len','str','number','int','type','upper','lower','split','join','append','keys','values','read','write','exists','sqrt','round','sleep','file','path','json','csv','env','datetime','regex','http','process','task','workflow','ai','tool','agent','skill'}
  return {k:v for k,v in self.vm.env.snapshot().items() if k not in hidden}
 def variables(self,scope='locals'):return self._user_vars() if scope=='locals' else self.vm.global_env.snapshot()
 def stack(self):return [{'id':1,'name':'<module>','source':self.source_name,'line':self._paused.span.line if self._paused and self._paused.span else 1}]
 def evaluate(self,expression):return self.vm.eval(parse_source('print '+expression,self.source_name).statements[0].value)
 def _hook(self,vm,node):
  line=node.span.line if node.span else 1;bp=self.breakpoints.get(line);stop=self.mode in ('step_in','step_over') or bool(bp and bp.enabled)
  if stop:
   if bp:bp.hit_count+=1;bp.enabled=False
   self._paused=node;self.events.append({'reason':'breakpoint' if bp else 'step','line':line,'source':self.source_name,'statement':type(node).__name__,'variables':self._user_vars()});raise DebugPause()
 def _execute(self):
  try:self.vm.run(self.program,self.source_name);return {'reason':'end','variables':self._user_vars()}
  except DebugPause:return self.events[-1]
 def start(self):self.mode='continue';return self._execute()
 def continue_run(self):
  if self._paused:
   node=self._paused;self._paused=None;self.vm.debug_hook=None;self.vm.exec_stmt(node);self.vm.debug_hook=self._hook
  self.mode='continue';return self._execute_remaining()
 def step_in(self):return self._resume_step('step_in')
 def step_over(self):return self._resume_step('step_over')
 def step_out(self):return self.continue_run()
 def _resume_step(self,mode):
  if self._paused:
   node=self._paused;self._paused=None;self.vm.debug_hook=None;self.vm.exec_stmt(node);self.vm.debug_hook=self._hook
  self.mode=mode;return self._execute_remaining()
 def _execute_remaining(self):
  # Resume from nearest top-level statement after the paused line. Nested statements are hook-visible during execution.
  line=self.events[-1]['line'] if self.events else 0
  pending=[x for x in self.program.statements if (x.span.line if x.span else 1)>line]
  try:
   for node in pending:self.vm.exec_stmt(node)
   return {'reason':'end','variables':self._user_vars()}
  except DebugPause:return self.events[-1]


