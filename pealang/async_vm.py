



"""Native cooperative async execution for PeaLang bytecode."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass
from .vm import VirtualMachine,AsyncSuspension,VMFunction,Frame,VMError
from .compiler import compile_source_to_bytecode
from .embedding import RuntimeOptions,to_pea,from_pea,PeaPermissionError
from .structured_concurrency import TaskGroup,CancellationScope,gather_structured
@dataclass
class CancellationToken:
 cancelled:bool=False
 def cancel(self):self.cancelled=True
 def throw_if_cancelled(self):
  if self.cancelled:raise asyncio.CancelledError('PeaLang execution cancelled')
class AsyncVirtualMachine(VirtualMachine):
 async def run_async(self,module,globals=None,timeout=None,cancellation=None):
  cancellation=cancellation or CancellationToken();self.module=module
  env=dict(globals or {});env.update({'len':len,'str':str,'int':int,'number':float,'upper':lambda x:str(x).upper(),'lower':lambda x:str(x).lower(),'all':self._all})
  self.frames=[Frame(module.code,env,name='<module>')]
  async def drive():
   while True:
    cancellation.throw_if_cancelled();result=self.loop()
    if isinstance(result,AsyncSuspension):
     cancellation.throw_if_cancelled();value=await result.awaitable;self.stack.append(value);continue
    return result
  return await asyncio.wait_for(drive(),timeout) if timeout else await drive()
 async def _all(self,items):return await asyncio.gather(*items)
class AsyncVMModule:
 def __init__(self,runtime,vm,module):self.runtime,self.vm,self.module=runtime,vm,module
 async def call_async(self,name,*args,output_type=None,cancellation=None):
  fn=self.vm.exports.get(name)
  if not isinstance(fn,VMFunction):raise VMError(f"Module does not export async function '{name}'")
  code=self.module.functions[fn.name];env=dict(fn.closure);env.update(code.defaults);env.update(zip(code.params,[to_pea(x) for x in args]));self.vm.frames=[Frame(code,env,name=fn.name)]
  value=await self.runtime._drive(self.vm,cancellation);return from_pea(value,output_type) if output_type else value
class AsyncVMRuntime:
 def __init__(self,options=None,output=None):self.options=options or RuntimeOptions();self.output=output;self.host={}
 def register_async_function(self,name,function,permission=None):self.host[name]=(function,permission);return self
 def _globals(self):
  root={}
  for full,(fn,permission) in self.host.items():
   node=root;parts=full.split('.')
   for part in parts[:-1]:node=node.setdefault(part,{})
   def wrapper(*args,_fn=fn,_permission=permission,_name=full):
    if _permission and _permission not in self.options.permissions:raise PeaPermissionError(f"Permission '{_permission}' is required for '{_name}'")
    return _fn(*args)
   node[parts[-1]]=wrapper
  return root
 async def load_async(self,source,source_name='<async>'):
  module=compile_source_to_bytecode(source,source_name);vm=AsyncVirtualMachine(self.output,self.options.max_instructions);await vm.run_async(module,self._globals(),self.options.max_execution_ms/1000);return AsyncVMModule(self,vm,module)
 async def _drive(self,vm,cancellation=None):
  async def drive():
   while True:
    if cancellation:cancellation.throw_if_cancelled()
    result=vm.loop()
    if isinstance(result,AsyncSuspension):vm.stack.append(await result.awaitable);continue
    return result
  return await asyncio.wait_for(drive(),self.options.max_execution_ms/1000)




