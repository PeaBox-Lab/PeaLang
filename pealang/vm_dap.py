



"""Debug Adapter Protocol server powered by the PeaLang VM."""
from __future__ import annotations
import json,sys
from pathlib import Path
from .compiler import compile_source_to_bytecode
from .bytecode import BytecodeModule
from .vm import VirtualMachine

def read_message(inp):
 h={}
 while True:
  line=inp.readline()
  if not line:return None
  if line in (b'\r\n',b'\n'):break
  k,v=line.decode().split(':',1);h[k.lower()]=v.strip()
 return json.loads(inp.read(int(h['content-length'])))
def write_message(out,obj):
 b=json.dumps(obj,default=str,separators=(',',':')).encode();out.write(f'Content-Length: {len(b)}\r\n\r\n'.encode()+b);out.flush()
def serve(inp=None,out=None):
 inp=inp or sys.stdin.buffer;out=out or sys.stdout.buffer;seq=1;vm=None;module=None;refs={};breakpoints={}
 def send(obj):
  nonlocal seq;write_message(out,{'seq':seq,**obj});seq+=1
 def response(req,body=None,success=True,message=None):send({'type':'response','request_seq':req.get('seq',0),'command':req.get('command'),'success':success,'body':body or {},**({'message':message} if message else {})})
 def event(name,body=None):send({'type':'event','event':name,'body':body or {}})
 def report(result):
  if isinstance(result,dict) and result.get('reason') in ('breakpoint','step'):event('stopped',{'reason':result['reason'],'threadId':1,'allThreadsStopped':True})
  else:event('terminated')
 while True:
  r=read_message(inp)
  if r is None:return 0
  cmd=r.get('command');a=r.get('arguments',{})
  try:
   post=None;body={}
   if cmd=='initialize':body={'supportsConfigurationDoneRequest':True,'supportsConditionalBreakpoints':True,'supportsHitConditionalBreakpoints':False,'supportsEvaluateForHovers':True,'supportsExceptionInfoRequest':True};post=lambda:event('initialized')
   elif cmd in ('launch','attach'):
    path=Path(a['program']).resolve();module=BytecodeModule.load(path) if path.suffix=='.peac' else compile_source_to_bytecode(path.read_text(encoding='utf-8'),str(path));vm=VirtualMachine(output=lambda x:event('output',{'category':'stdout','output':str(x)+'\n'}));vm.module=module
   elif cmd=='setBreakpoints':
    source=str(Path(a['source']['path']).resolve());vm.breakpoints={x for x in vm.breakpoints if x[0]!=source};items=[]
    for bp in a.get('breakpoints',[]):vm.add_breakpoint(bp['line'],source);items.append({'verified':True,'line':bp['line']})
    body={'breakpoints':items}
   elif cmd=='configurationDone':post=lambda:report(vm.run(module))
   elif cmd=='continue':body={'allThreadsContinued':True};post=lambda:report(vm.continue_run())
   elif cmd in ('next','stepIn','stepOut'):post=lambda:report(vm.step())
   elif cmd=='threads':body={'threads':[{'id':1,'name':'PeaLang VM main'}]}
   elif cmd=='stackTrace':
    frames=[]
    for f in vm.stack_trace():
     refs[1000+f['id']]=f['locals'];frames.append({'id':f['id'],'name':f['name'],'line':f['line'],'column':1,'source':{'name':Path(f['source']).name,'path':f['source']}})
    body={'stackFrames':frames,'totalFrames':len(frames)}
   elif cmd=='scopes':body={'scopes':[{'name':'Locals','variablesReference':1000+a['frameId'],'expensive':False}]}
   elif cmd=='variables':body={'variables':[{'name':k,'value':repr(v),'type':type(v).__name__,'variablesReference':0} for k,v in refs.get(a['variablesReference'],{}).items()]}
   elif cmd=='evaluate':
    env=refs.get(1000+a.get('frameId',1),{});expr=a['expression'];value=env.get(expr,'<evaluation supports variable names>');body={'result':repr(value),'variablesReference':0}
   elif cmd=='exceptionInfo':body={'exceptionId':'PeaLangVMError','description':'VM exception','breakMode':'unhandled'}
   elif cmd in ('disconnect','terminate'):post=lambda:event('terminated')
   response(r,body)
   if post:post()
   if cmd in ('disconnect','terminate'):return 0
  except Exception as e:response(r,success=False,message=str(e),body={'error':str(e)})
def main():return serve()
if __name__=='__main__':raise SystemExit(main())




