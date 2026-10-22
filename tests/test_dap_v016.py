import io,json,tempfile
from pathlib import Path
from pealang.dap import serve

def m(o):
 b=json.dumps(o).encode();return f'Content-Length: {len(b)}\r\n\r\n'.encode()+b

def test_capabilities_and_events(tmp_path):
 p=tmp_path/'a.pea';p.write_text('print "ok"')
 reqs=[
 {'seq':1,'type':'request','command':'initialize','arguments':{}},
 {'seq':2,'type':'request','command':'launch','arguments':{'program':str(p)}},
 {'seq':3,'type':'request','command':'configurationDone','arguments':{}},
 {'seq':4,'type':'request','command':'disconnect','arguments':{}},]
 out=io.BytesIO();serve(io.BytesIO(b''.join(m(x) for x in reqs)),out);raw=out.getvalue()
 assert b'supportsConditionalBreakpoints' in raw and b'initialized' in raw and b'terminated' in raw
