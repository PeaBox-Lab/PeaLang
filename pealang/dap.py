from __future__ import annotations
import json,sys
from pathlib import Path
from .debugger import DebugSession
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
 inp=inp or sys.stdin.buffer;out=out or sys.stdout.buffer;seq=1;session=None
 while True:
  r=read_message(inp)
  if r is None:return 0
  cmd=r.get('command');args=r.get('arguments',{});body={};success=True
  try:
   if cmd=='initialize':body={'supportsConfigurationDoneRequest':True,'supportsEvaluateForHovers':True}
   elif cmd in ('launch','attach'):
    path=Path(args['program']);session=DebugSession(path.read_text(),str(path),output=lambda x:None,base_dir=path.parent)
   elif cmd=='setBreakpoints':
    body={'breakpoints':[{'verified':True,'line':session.add_breakpoint(x['line'],x.get('condition'))['line']} for x in args.get('breakpoints',[])]}
   elif cmd=='configurationDone':body=session.start()
   elif cmd=='continue':body=session.continue_run()
   elif cmd=='next':body=session.step_over()
   elif cmd=='stepIn':body=session.step_in()
   elif cmd=='stepOut':body=session.step_out()
   elif cmd=='threads':body={'threads':[{'id':1,'name':'PeaLang main'}]}
   elif cmd=='stackTrace':body={'stackFrames':session.stack(),'totalFrames':len(session.stack())}
   elif cmd=='scopes':body={'scopes':[{'name':'Locals','variablesReference':1,'expensive':False},{'name':'Globals','variablesReference':2,'expensive':False}]}
   elif cmd=='variables':
    vals=session.variables('locals' if args.get('variablesReference')==1 else 'globals');body={'variables':[{'name':k,'value':repr(v),'variablesReference':0} for k,v in vals.items()]}
   elif cmd=='evaluate':body={'result':repr(session.evaluate(args['expression'])),'variablesReference':0}
   elif cmd in ('disconnect','terminate'):
    body={}
   else:body={}
  except Exception as e:success=False;body={'error':str(e)}
  write_message(out,{'seq':seq,'type':'response','request_seq':r.get('seq',0),'success':success,'command':cmd,'body':body});seq+=1
  if cmd in ('disconnect','terminate'):return 0
def main():return serve()
if __name__=='__main__':raise SystemExit(main())
