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
 inp=inp or sys.stdin.buffer;out=out or sys.stdout.buffer;seq=1;session=None;refs={}
 def send(obj):
  nonlocal seq
  obj={'seq':seq,**obj};seq+=1;write_message(out,obj)
 def event(name,body=None):send({'type':'event','event':name,'body':body or {}})
 def stopped_or_terminated(result):
  if result.get('reason')=='end' or result.get('terminated'):event('terminated')
  else:event('stopped',{'reason':result.get('reason','pause'),'threadId':1,'allThreadsStopped':True,'text':result.get('text')})
 while True:
  r=read_message(inp)
  if r is None:return 0
  cmd=r.get('command');args=r.get('arguments',{});body={};success=True;post=None
  try:
   if cmd=='initialize':
    body={'supportsConfigurationDoneRequest':True,'supportsEvaluateForHovers':True,'supportsConditionalBreakpoints':True,'supportsHitConditionalBreakpoints':True,'supportsLogPoints':True,'supportsTerminateRequest':True,'supportsExceptionFilterOptions':True,'exceptionBreakpointFilters':[{'filter':'all','label':'All PeaLang exceptions','default':False}]};post=lambda:event('initialized')
   elif cmd in ('launch','attach'):
    path=Path(args['program']).resolve();session=DebugSession(path.read_text(encoding='utf-8'),str(path),output=lambda x:event('output',{'category':'stdout','output':str(x)+'\n'}),base_dir=path.parent)
   elif cmd=='setBreakpoints':
    source=str(Path(args.get('source',{}).get('path',session.source_name)).resolve());session.clear_breakpoints(source);items=[]
    for x in args.get('breakpoints',[]):
     b=session.add_breakpoint(x['line'],x.get('condition'),x.get('hitCondition'),x.get('logMessage'),source);items.append({'verified':True,'line':b['line']})
    body={'breakpoints':items}
   elif cmd=='setExceptionBreakpoints':session.set_exception_breakpoints(args.get('filters',[]));body={'breakpoints':[]}
   elif cmd=='configurationDone':post=lambda:stopped_or_terminated(session.start())
   elif cmd=='continue':body={'allThreadsContinued':True};post=lambda:stopped_or_terminated(session.continue_run())
   elif cmd=='next':post=lambda:stopped_or_terminated(session.step_over())
   elif cmd=='stepIn':post=lambda:stopped_or_terminated(session.step_in())
   elif cmd=='stepOut':post=lambda:stopped_or_terminated(session.step_out())
   elif cmd=='threads':body={'threads':[{'id':1,'name':'PeaLang main'}]}
   elif cmd=='stackTrace':
    frames=[]
    for f in session.stack():frames.append({'id':f['id'],'name':f['name'],'source':{'name':Path(f['source']).name,'path':f['source']},'line':f['line'],'column':1})
    body={'stackFrames':frames,'totalFrames':len(frames)}
   elif cmd=='scopes':
    fid=args.get('frameId',1);lr=1000+fid;gr=2000+fid;refs[lr]=('locals',fid);refs[gr]=('globals',fid)
    body={'scopes':[{'name':'Locals','variablesReference':lr,'expensive':False},{'name':'Globals','variablesReference':gr,'expensive':True}]}
   elif cmd=='variables':
    scope,fid=refs.get(args.get('variablesReference'),('globals',1));vals=session.variables(scope,fid);body={'variables':[{'name':k,'value':repr(v),'type':type(v).__name__,'variablesReference':0} for k,v in vals.items()]}
   elif cmd=='evaluate':body={'result':repr(session.evaluate(args['expression'],args.get('frameId'))),'variablesReference':0}
   elif cmd in ('disconnect','terminate'):body={};post=lambda:event('terminated')
  except Exception as e:success=False;body={'error':{'id':1,'format':str(e)},'message':str(e)}
  send({'type':'response','request_seq':r.get('seq',0),'success':success,'command':cmd,'body':body})
  if post:post()
  if cmd in ('disconnect','terminate'):return 0

def main():return serve()
if __name__=='__main__':raise SystemExit(main())
