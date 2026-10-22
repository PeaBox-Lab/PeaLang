
from __future__ import annotations
from dataclasses import dataclass, asdict
from .parser import parse_source
from .interpreter import Interpreter
from .errors import PeaError

@dataclass
class Breakpoint:
    line:int
    enabled:bool=True
    condition:str|None=None

@dataclass
class DebugEvent:
    reason:str
    source:str
    line:int
    col:int
    variables:dict
    statement:str
    def to_dict(self): return asdict(self)

class DebugSession:
    """Deterministic statement debugger for top-level PeaLang programs."""
    def __init__(self, source, source_name='<debug>', output=None, base_dir=None):
        self.source=source; self.source_name=source_name
        self.program=parse_source(source,source_name)
        self.vm=Interpreter(output=output,base_dir=base_dir)
        self.breakpoints={}; self.index=0; self.events=[]; self.finished=False
    def add_breakpoint(self,line,condition=None):
        bp=Breakpoint(int(line),True,condition); self.breakpoints[bp.line]=bp; return asdict(bp)
    def remove_breakpoint(self,line): return self.breakpoints.pop(int(line),None) is not None
    def variables(self): return self.vm.global_env.snapshot()
    def stack(self): return [{'name':'<module>','source':self.source_name,'line':self.current_line()}]
    def current_line(self):
        if self.index>=len(self.program.statements): return None
        sp=self.program.statements[self.index].span; return sp.line if sp else 1
    def _statement_name(self,node): return type(node).__name__
    def _event(self,reason,node):
        sp=node.span; e=DebugEvent(reason,self.source_name,sp.line if sp else 1,sp.col if sp else 1,self.variables(),self._statement_name(node)); self.events.append(e); return e.to_dict()
    def step(self):
        if self.finished:return {'reason':'end','variables':self.variables()}
        if self.index>=len(self.program.statements): self.finished=True; return {'reason':'end','variables':self.variables()}
        node=self.program.statements[self.index]
        self.vm.exec_stmt(node); self.index+=1
        if self.index>=len(self.program.statements): self.finished=True
        return self._event('step',node)
    def continue_run(self):
        while not self.finished and self.index<len(self.program.statements):
            node=self.program.statements[self.index]; line=node.span.line if node.span else 1
            bp=self.breakpoints.get(line)
            if bp and bp.enabled:
                bp.enabled=False
                return self._event('breakpoint',node)
            self.step()
        return {'reason':'end','variables':self.variables()}
    def run(self):
        for bp in self.breakpoints.values(): bp.enabled=True
        return self.continue_run()
