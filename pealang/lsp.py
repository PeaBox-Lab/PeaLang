
from __future__ import annotations
import json, sys
from .editor import diagnostics, completions, definition, hover

def _read(inp):
    headers={}
    while True:
        line=inp.readline()
        if not line: return None
        if line in (b'\r\n',b'\n'): break
        k,v=line.decode('ascii').split(':',1); headers[k.lower()]=v.strip()
    n=int(headers.get('content-length','0')); return json.loads(inp.read(n).decode('utf-8'))
def _write(out,obj):
    data=json.dumps(obj,separators=(',',':')).encode(); out.write(f'Content-Length: {len(data)}\r\n\r\n'.encode()+data); out.flush()
def serve(inp=None,out=None):
    inp=inp or sys.stdin.buffer; out=out or sys.stdout.buffer; docs={}
    while True:
        m=_read(inp)
        if m is None: return 0
        method=m.get('method'); rid=m.get('id'); p=m.get('params',{})
        if method=='initialize': result={'capabilities':{'textDocumentSync':1,'completionProvider':{},'definitionProvider':True,'hoverProvider':True}}
        elif method=='shutdown': result=None
        elif method=='exit': return 0
        elif method in ('textDocument/didOpen','textDocument/didChange'):
            td=p.get('textDocument',{}); uri=td.get('uri','')
            text=td.get('text') if method.endswith('didOpen') else (p.get('contentChanges') or [{}])[-1].get('text','')
            docs[uri]=text; _write(out,{'jsonrpc':'2.0','method':'textDocument/publishDiagnostics','params':{'uri':uri,'diagnostics':[{'range':{'start':{'line':d['line']-1,'character':d['col']-1},'end':{'line':d['line']-1,'character':d['col']}},'severity':1,'source':'pealang','message':d['message']} for d in diagnostics(text,uri)]}}); continue
        elif method=='textDocument/completion':
            uri=p['textDocument']['uri']; result=[{'label':x,'kind':6} for x in completions(docs.get(uri,''))]
        elif method in ('textDocument/definition','textDocument/hover'):
            uri=p['textDocument']['uri']; text=docs.get(uri,''); pos=p.get('position',{}); lines=text.splitlines(); line=lines[pos.get('line',0)] if lines else ''; c=pos.get('character',0); import re; ms=list(re.finditer(r'[A-Za-z_][A-Za-z0-9_]*',line)); name=next((x.group() for x in ms if x.start()<=c<=x.end()),''); hit=definition(text,name,uri)
            if method.endswith('definition'): result=None if not hit else {'uri':uri,'range':{'start':{'line':hit['line']-1,'character':hit['col']-1},'end':{'line':hit['line']-1,'character':hit['col']-1+len(name)}}}
            else: result=None if not hit else {'contents':{'kind':'markdown','value':f"**{name}** ({hit['kind']})"}}
        else: result=None
        if rid is not None: _write(out,{'jsonrpc':'2.0','id':rid,'result':result})
def main(): return serve()
if __name__=='__main__': raise SystemExit(main())
