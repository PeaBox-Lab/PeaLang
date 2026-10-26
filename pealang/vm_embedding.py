



"""Capability-safe, VM-backed embedding API."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import time
from .compiler import compile_source_to_bytecode
from .bytecode import BytecodeModule
from .vm import VirtualMachine,VMFunction,VMError,Frame
from .embedding import RuntimeOptions,to_pea,from_pea,PeaPermissionError,PeaResourceLimitError
@dataclass
class VMHostFunction:
 name:str;function:object;permission:str|None=None
class VMModule:
 def __init__(self,runtime,vm,module):self.runtime,self.vm,self.module=runtime,vm,module
 @property
 def exports(self):return dict(self.vm.exports)
 def call(self,name,*args,output_type=None):
  fn=self.vm.exports.get(name)
  if not isinstance(fn,VMFunction):raise VMError(f"Module does not export VM function '{name}'")
  code=self.module.functions[fn.name];required=len(code.params)-len(code.defaults)
  if not required<=len(args)<=len(code.params):raise VMError(f'Expected {required} to {len(code.params)} arguments, got {len(args)}')
  env=dict(fn.closure);env.update(code.defaults);env.update(zip(code.params,[to_pea(x) for x in args]));self.vm.frames=[Frame(code,env,name=fn.name)]
  started=time.perf_counter();value=self.vm.loop();elapsed=(time.perf_counter()-started)*1000
  if elapsed>self.runtime.options.max_execution_ms:raise PeaResourceLimitError('Execution timeout exceeded')
  return from_pea(value,output_type) if output_type else value
class VMRuntime:
 def __init__(self,options=None,output=None,max_instructions=None,globals=None):
  self.options=options or RuntimeOptions();self.output=output;self.globals=dict(globals or {});self.host_functions={}
  if max_instructions is not None:self.options=RuntimeOptions(self.options.permissions,self.options.max_execution_ms,max_instructions,self.options.max_call_depth,self.options.allow_process)
 def register_function(self,name,function,permission=None):self.host_functions[name]=VMHostFunction(name,function,permission);return self
 def register_module(self,name,functions,permission_prefix=None):
  for child,fn in functions.items():self.register_function(f'{name}.{child}',fn,f'{permission_prefix}.{child}' if permission_prefix else None)
  return self
 def _globals(self):
  root=dict(self.globals)
  for full,item in self.host_functions.items():
   parts=full.split('.');node=root
   for part in parts[:-1]:node=node.setdefault(part,{})
   def wrapper(*args,_item=item):
    if _item.permission and _item.permission not in self.options.permissions:raise PeaPermissionError(f"Permission '{_item.permission}' is required for '{_item.name}'")
    return to_pea(_item.function(*args))
   node[parts[-1]]=wrapper
  return root
 def load(self,source,source_name='<embedded>'):return self.load_bytecode(compile_source_to_bytecode(source,source_name))
 def load_file(self,path):
  p=Path(path).resolve();return self.load(p.read_text(encoding='utf-8'),str(p))
 def load_bytecode(self,module):
  if isinstance(module,(str,Path)):module=BytecodeModule.load(module)
  vm=VirtualMachine(self.output,self.options.max_instructions);vm.run(module,self._globals());return VMModule(self,vm,module)




