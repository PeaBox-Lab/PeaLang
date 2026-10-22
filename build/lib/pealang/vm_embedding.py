"""VM-backed embedding facade for compiled PeaLang extensions."""
from __future__ import annotations
from pathlib import Path
from .compiler import compile_source_to_bytecode
from .bytecode import BytecodeModule
from .vm import VirtualMachine,VMFunction,VMError
class VMModule:
 def __init__(self,vm,module):self.vm,self.module=vm,module
 @property
 def exports(self):return dict(self.vm.exports)
 def call(self,name,*args):
  fn=self.vm.exports.get(name)
  if not isinstance(fn,VMFunction):raise VMError(f"Module does not export VM function '{name}'")
  code=self.module.functions[fn.name];env=dict(fn.closure);env.update(zip(code.params,args));self.vm.frames=[__import__('pealang.vm',fromlist=['Frame']).Frame(code,env,name=fn.name)];return self.vm.loop()
class VMRuntime:
 def __init__(self,output=None,max_instructions=100000,globals=None):self.output=output;self.max_instructions=max_instructions;self.globals=dict(globals or {})
 def load(self,source,source_name='<embedded>'):
  module=compile_source_to_bytecode(source,source_name);return self.load_bytecode(module)
 def load_file(self,path):
  p=Path(path);return self.load(p.read_text(encoding='utf-8'),str(p))
 def load_bytecode(self,module):
  if isinstance(module,(str,Path)):module=BytecodeModule.load(module)
  vm=VirtualMachine(self.output,self.max_instructions);vm.run(module,self.globals);return VMModule(vm,module)
