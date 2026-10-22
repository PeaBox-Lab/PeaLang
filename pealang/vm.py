"""Stack-based PeaLang virtual machine."""
from __future__ import annotations
from dataclasses import dataclass
from .bytecode import BytecodeModule,Op
class VMError(Exception):pass
@dataclass
class VMFunction:name:str;module:BytecodeModule;closure:dict
@dataclass
class Frame:code:object;env:dict;ip:int=0;name:str='<module>';stack_base:int=0
class VirtualMachine:
 def __init__(self,output=None,max_instructions=100000):self.output=output or print;self.max_instructions=max_instructions;self.instructions=0;self.stack=[];self.frames=[];self.exports={}
 def run(self,module,globals=None):
  self.module=module;env=dict(globals or {});env.update({'len':len,'str':str,'int':int,'number':float,'upper':lambda x:str(x).upper(),'lower':lambda x:str(x).lower(),'append':lambda a,x:(a.append(x) or a)})
  self.frames=[Frame(module.code,env,name='<module>')];result=self.loop();return result
 def pop(self):
  if not self.stack:raise VMError('Stack underflow')
  return self.stack.pop()
 def truth(self,v):return bool(v)
 def loop(self):
  ret=None
  while self.frames:
   f=self.frames[-1]
   if f.ip>=len(f.code.instructions):self.frames.pop();continue
   ins=f.code.instructions[f.ip];f.ip+=1;self.instructions+=1
   if self.instructions>self.max_instructions:raise VMError('VM instruction limit exceeded')
   op=ins.op
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
   elif op in (Op.ADD.value,Op.SUB.value,Op.MUL.value,Op.DIV.value,Op.MOD.value,Op.EQ.value,Op.NE.value,Op.LT.value,Op.LE.value,Op.GT.value,Op.GE.value):
    b=self.pop();a=self.pop();self.stack.append({Op.ADD.value:lambda:a+b,Op.SUB.value:lambda:a-b,Op.MUL.value:lambda:a*b,Op.DIV.value:lambda:a/b,Op.MOD.value:lambda:a%b,Op.EQ.value:lambda:a==b,Op.NE.value:lambda:a!=b,Op.LT.value:lambda:a<b,Op.LE.value:lambda:a<=b,Op.GT.value:lambda:a>b,Op.GE.value:lambda:a>=b}[op]())
   elif op==Op.NEG.value:self.stack.append(-self.pop())
   elif op==Op.NOT.value:self.stack.append(not self.truth(self.pop()))
   elif op==Op.LIST.value:
    vals=self.stack[-ins.arg:] if ins.arg else []
    if ins.arg: del self.stack[-ins.arg:]
    self.stack.append(vals)
   elif op==Op.DICT.value:
    d={}
    items=[self.pop() for _ in range(ins.arg*2)][::-1]
    for i in range(0,len(items),2):d[items[i]]=items[i+1]
    self.stack.append(d)
   elif op==Op.GET_INDEX.value:b=self.pop();a=self.pop();self.stack.append(a[b])
   elif op==Op.GET_PROPERTY.value:
    a=self.pop();self.stack.append(a[ins.arg] if isinstance(a,dict) else getattr(a,ins.arg))
   elif op==Op.JUMP.value:f.ip=ins.arg
   elif op==Op.JUMP_IF_FALSE.value:
    if not self.truth(self.pop()):f.ip=ins.arg
   elif op==Op.ITER.value:self.stack.append(iter(self.pop()))
   elif op==Op.ITER_NEXT.value:
    it=self.stack[-1]
    try:f.env[ins.arg['name']]=next(it)
    except StopIteration:self.stack.pop();f.ip=ins.arg['end']
   elif op==Op.FUNCTION.value:self.stack.append(VMFunction(ins.arg,self.module,dict(f.env)))
   elif op==Op.CALL.value:
    args=[self.pop() for _ in range(ins.arg)][::-1];callee=self.pop()
    if isinstance(callee,VMFunction):
     code=self.module.functions[callee.name];env=dict(callee.closure);env.update(zip(code.params,args));self.frames.append(Frame(code,env,name=callee.name,stack_base=len(self.stack)))
    elif callable(callee):self.stack.append(callee(*args))
    else:raise VMError('Value is not callable')
   elif op==Op.RETURN.value:
    value=self.pop();done=self.frames.pop()
    if self.frames:self.stack.append(value)
    else:ret=value
   elif op==Op.EXPORT.value:self.exports[ins.arg]=f.env.get(ins.arg)
   elif op==Op.HALT.value:self.frames.pop();ret=self.stack[-1] if self.stack else None
   else:raise VMError(f'Unknown opcode {op}')
  return ret
