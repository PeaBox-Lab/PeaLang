
"""Profiling, coverage and observability primitives for PeaLang."""
from __future__ import annotations
from dataclasses import dataclass,field,asdict
import time,json
@dataclass
class TraceEvent:
 name:str;timestamp:float;attributes:dict=field(default_factory=dict);duration_ms:float|None=None
class Observer:
 def on_event(self,event:TraceEvent):pass
class MemoryObserver(Observer):
 def __init__(self):self.events=[]
 def on_event(self,event):self.events.append(event)
class Profiler:
 def __init__(self):self.started=None;self.ended=None;self.instructions=0;self.opcodes={};self.functions={}
 def start(self):self.started=time.perf_counter();return self
 def instruction(self,opcode,frame):self.instructions+=1;self.opcodes[opcode]=self.opcodes.get(opcode,0)+1;self.functions[frame]=self.functions.get(frame,0)+1
 def stop(self):self.ended=time.perf_counter();return self
 def report(self):return {'elapsed_ms':((self.ended or time.perf_counter())-(self.started or time.perf_counter()))*1000,'instructions':self.instructions,'opcodes':dict(sorted(self.opcodes.items())),'functions':dict(sorted(self.functions.items()))}
class Coverage:
 def __init__(self):self.lines={}
 def hit(self,source,line):self.lines.setdefault(source,set()).add(int(line))
 def report(self):return {k:sorted(v) for k,v in sorted(self.lines.items())}
 def to_json(self):return json.dumps(self.report(),indent=2)
class Instrumentation:
 def __init__(self,profiler=None,coverage=None,observers=None):self.profiler=profiler or Profiler();self.coverage=coverage or Coverage();self.observers=list(observers or [])
 def hook(self,vm,frame,ins):
  self.profiler.instruction(ins.op,frame.name);self.coverage.hit(frame.code.source_name,ins.line)
  event=TraceEvent('vm.instruction',time.time(),{'opcode':ins.op,'function':frame.name,'source':frame.code.source_name,'line':ins.line})
  for o in self.observers:o.on_event(event)

