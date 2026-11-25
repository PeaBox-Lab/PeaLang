"""PeaLang stack VM with resumable frames, handlers, modules and shared closures."""
from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
from .bytecode import BytecodeModule,Op
from .error_values import build_error, error_value_from_raw, matches_error
from .iterators import make_iterator,iterator_next,has_next,peek,close_iterator,ITER_EXHAUSTED
from .project import ModuleResolver,load_manifest
class VMError(Exception):pass
@dataclass
class AsyncSuspension:
 awaitable:object
 source:str
 line:int
class VMThrown(Exception):
 def __init__(self,value,source=None,line=None):
  self.value=value;self.source=source;self.line=line;super().__init__(str(value))
class _StepPause(Exception):
 def __init__(self,frame,ins):self.frame,self.ins=frame,ins
@dataclass
class VMFunction:name:str;module:BytecodeModule;closure:dict
@dataclass
class Handler:catch:int|None;finally_ip:int|None;end:int;name:str|None;stack_size:int;catch_type:str|None=None
@dataclass
class Frame:code:object;env:dict;ip:int=0;name:str='<module>';stack_base:int=0;handlers:list[Handler]=field(default_factory=list)
class VirtualMachine:
 def __init__(self,output=None,max_instructions=100000,debug_hook=None,module_loader=None,instrumentation=None,module_resolver=None):
  self.output=output or print;self.max_instructions=max_instructions;self.debug_hook=debug_hook;self.module_loader=module_loader;self.instrumentation=instrumentation;self.module_resolver=module_resolver;self.reset()
 def reset(self):self.instructions=0;self.stack=[];self.frames=[];self.exports={};self.paused=False;self.breakpoints=set();self.last_event=None;self.module_cache={};self.module_loading=set()
 def run(self,module,globals=None):
  self.module=module;env=dict(globals or {});env.update({'len':len,'str':str,'int':int,'number':float,'upper':lambda x:str(x).upper(),'lower':lambda x:str(x).lower(),'append':lambda a,x:(a.append(x) or a),'iter':make_iterator,'next':iterator_next,'has_next':has_next,'peek':peek,'error':build_error})
  self.frames=[Frame(module.code,env,name='<module>')];return self.loop()
 def pop(self):
  if not self.stack:raise VMError('Stack underflow')
  return self.stack.pop()
 def truth(self,v):return bool(v)
 def add_breakpoint(self,line,source=None):self.breakpoints.add((str(source or self.module.source_name),int(line)))
 def continue_run(self):self.paused=False;return self.loop()
 def step(self):
  if not self.frames:return {'reason':'end'}
  target=self.instructions+1;previous=self.debug_hook
  def hook(vm,frame,ins):
   if vm.instructions>=target:raise _StepPause(frame,ins)
  self.debug_hook=hook
  try:return self.loop()
  except _StepPause as x:return {'reason':'step','source':x.frame.code.source_name,'line':x.ins.line,'frame':x.frame.name}
  finally:self.debug_hook=previous
 def stack_trace(self):return [{'id':i+1,'name':f.name,'source':f.code.source_name,'line':f.code.instructions[max(0,f.ip-1)].line if f.code.instructions else 1,'locals':dict(f.env)} for i,f in enumerate(reversed(self.frames))]
 def _invoke(self,callee,args):
  if isinstance(callee,VMFunction):
   code=callee.module.functions[callee.name];required=len(code.params)-len(code.defaults)
   if not required<=len(args)<=len(code.params):raise VMError(f'Expected {required} to {len(code.params)} arguments, got {len(args)}')
   env=dict(callee.closure);env.update(code.defaults);env.update(zip(code.params,args));self.frames.append(Frame(code,env,name=callee.name,stack_base=len(self.stack)));return None
  if callable(callee):self.stack.append(callee(*args));return None
  raise VMError('Value is not callable')
 def _discard_stack(self,index):
  for value in self.stack[index:]:close_iterator(value)
  del self.stack[index:]
 def _structured_throw(self,thrown):
  record=error_value_from_raw(thrown.value)
  if not record.get('source'):record['source']=thrown.source or self.module.source_name
  if record.get('line') is None:record['line']=thrown.line
  if record.get('frames') is None:record['frames']=self.stack_trace()
  return record
 def _handle_throw(self,thrown):
  record=self._structured_throw(thrown)
  while self.frames:
   f=self.frames[-1]
   if f.handlers:
    h=f.handlers.pop();self._discard_stack(h.stack_size)
    if h.catch_type and not matches_error(record,h.catch_type):continue
    if h.catch is not None:
     if h.name:f.env[h.name]=record
     f.ip=h.catch;return True
   self._discard_stack(f.stack_base);self.frames.pop()
  return False
 def _resolver_for_frame(self,frame):
  if self.module_resolver is not None:return self.module_resolver
  name=str(frame.code.source_name or '')
  if not name or name.startswith('<'):return None
  manifest,data=load_manifest(name)
  if not manifest:return None
  self.module_resolver=ModuleResolver(manifest.parent,data.get('dependencies'))
  return self.module_resolver
 def _load_module(self,path,alias,frame):
  base=Path(str(frame.code.source_name or '.')).parent;resolver=self._resolver_for_frame(frame)
  if resolver:
   resolution=resolver.resolve(path,base,alias);resolved=resolution.path;key=resolution.key;binding=resolution.alias
  else:
   resolved=(base/path).resolve() if not Path(path).is_absolute() else Path(path);key=str(resolved);binding=alias or Path(path).stem
  if not self.module_loader and not resolved.is_file():raise VMError(f"Module not found: {path}")
  if key in self.module_cache:exports=self.module_cache[key]
  else:
   if key in self.module_loading:raise VMError(f"Circular module import: {path}")
   self.module_loading.add(key)
   try:
    if self.module_loader:module=self.module_loader(key)
    else:
     from .compiler import compile_source_to_bytecode
     module=compile_source_to_bytecode(resolved.read_text(encoding='utf-8'),key)
    child=VirtualMachine(self.output,self.max_instructions-self.instructions,module_loader=self.module_loader,module_resolver=resolver);child.module_cache=self.module_cache;child.module_loading=self.module_loading;child.run(module,frame.env);exports=dict(child.exports);self.instructions+=child.instructions;self.module_cache[key]=exports
   finally:self.module_loading.discard(key)
  frame.env[binding]=exports
 def loop(self):
  ret=None
  while self.frames:
   f=self.frames[-1]
   if f.ip>=len(f.code.instructions):self.frames.pop();continue
   ins=f.code.instructions[f.ip]
   if self.instrumentation:self.instrumentation.hook(self,f,ins)
   if self.debug_hook:self.debug_hook(self,f,ins)
   if (f.code.source_name,ins.line) in self.breakpoints and self.last_event!=(f.code.source_name,ins.line,f.ip):self.paused=True;self.last_event=(f.code.source_name,ins.line,f.ip);return {'reason':'breakpoint','source':f.code.source_name,'line':ins.line,'frame':f.name}
   f.ip+=1;self.instructions+=1
   if self.instructions>self.max_instructions:raise VMError('VM instruction limit exceeded')
   op=ins.op
   try:
    if op==Op.CONST.value:self.stack.append(self.module.constants[ins.arg])
    elif op==Op.NULL.value:self.stack.append(None)
    elif op==Op.TRUE.value:self.stack.append(True)
    elif op==Op.FALSE.value:self.stack.append(False)
    elif op==Op.LOAD.value:
     if ins.arg not in f.env:raise VMError(f"Undefined variable '{ins.arg}' at line {ins.line}")
     self.stack.append(f.env[ins.arg])
    elif op==Op.STORE.value:f.env[ins.arg]=self.pop()
    elif op==Op.POP.value:self.pop()
    elif op==Op.PRINT.value:self.output(self.pop())
    elif op in ('ADD','SUB','MUL','DIV','MOD','EQ','NE','LT','LE','GT','GE'):
     b=self.pop();a=self.pop();self.stack.append({'ADD':lambda:a+b,'SUB':lambda:a-b,'MUL':lambda:a*b,'DIV':lambda:a/b,'MOD':lambda:a%b,'EQ':lambda:a==b,'NE':lambda:a!=b,'LT':lambda:a<b,'LE':lambda:a<=b,'GT':lambda:a>b,'GE':lambda:a>=b}[op]())
    elif op==Op.NEG.value:self.stack.append(-self.pop())
    elif op==Op.NOT.value:self.stack.append(not self.truth(self.pop()))
    elif op==Op.LIST.value:
     vals=self.stack[-ins.arg:] if ins.arg else []
     if ins.arg:del self.stack[-ins.arg:]
     self.stack.append(vals)
    elif op==Op.DICT.value:
     items=[self.pop() for _ in range(ins.arg*2)][::-1];self.stack.append({items[i]:items[i+1] for i in range(0,len(items),2)})
    elif op==Op.GET_INDEX.value:b=self.pop();a=self.pop();self.stack.append(a[b])
    elif op==Op.GET_PROPERTY.value:a=self.pop();self.stack.append(a[ins.arg] if isinstance(a,dict) else getattr(a,ins.arg))
    elif op==Op.SET_PROPERTY.value:
     value=self.pop();a=self.pop();a.__setitem__(ins.arg,value) if isinstance(a,dict) else setattr(a,ins.arg,value)
    elif op==Op.SET_INDEX.value:value=self.pop();index=self.pop();self.pop().__setitem__(index,value)
    elif op==Op.JUMP.value:f.ip=ins.arg
    elif op==Op.JUMP_IF_FALSE.value:
     if not self.truth(self.pop()):f.ip=ins.arg
    elif op==Op.ITER.value:self.stack.append(make_iterator(self.pop()))
    elif op==Op.ITER_NEXT.value:
     value=iterator_next(self.stack[-1],ITER_EXHAUSTED)
     if value is ITER_EXHAUSTED:close_iterator(self.stack.pop());f.ip=ins.arg['end']
     else:f.env[ins.arg['name']]=value
    elif op==Op.CLOSE_ITER.value:close_iterator(self.pop())
    elif op==Op.FUNCTION.value:self.stack.append(VMFunction(ins.arg,self.module,f.env))
    elif op==Op.CALL.value:
     callee,args=self.pop_args(ins.arg);self._invoke(callee,args)
    elif op==Op.AWAIT.value:
     value=self.pop()
     if hasattr(value,'__await__'):return AsyncSuspension(value,f.code.source_name,ins.line)
     self.stack.append(value)
    elif op==Op.RETURN.value:
     value=self.pop();self._discard_stack(f.stack_base);self.frames.pop();self.stack.append(value) if self.frames else None;ret=value
    elif op==Op.PUSH_HANDLER.value:f.handlers.append(Handler(ins.arg.get('catch'),ins.arg.get('finally'),ins.arg['end'],ins.arg.get('name'),len(self.stack),ins.arg.get('catch_type')))
    elif op==Op.POP_HANDLER.value:
     if f.handlers:f.handlers.pop()
    elif op==Op.RAISE.value:raise VMThrown(self.pop(),f.code.source_name,ins.line)
    elif op==Op.IMPORT.value:self._load_module(ins.arg['path'],ins.arg.get('alias'),f)
    elif op==Op.EXPORT.value:self.exports[ins.arg]=f.env.get(ins.arg)
    elif op==Op.HALT.value:self.frames.pop();ret=self.stack[-1] if self.stack else None
    else:raise VMError(f'Unknown opcode {op}')
   except VMThrown as ex:
    if not self._handle_throw(ex):raise VMError(str(ex.value))
   except (ZeroDivisionError, IndexError, KeyError, TypeError, ValueError, AttributeError) as ex:
    record=build_error(type(ex).__name__,str(ex),cause=ex)
    if not self._handle_throw(VMThrown(record,f.code.source_name,ins.line)):raise VMError(str(ex)) from ex
  return ret
 def pop_args(self,n):
  args=[self.pop() for _ in range(n)][::-1];return self.pop(),args
