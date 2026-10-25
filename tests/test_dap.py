

import io,json
from pealang.dap import serve
def m(o):
 b=json.dumps(o).encode();return f'Content-Length: {len(b)}\r\n\r\n'.encode()+b
def test_initialize_disconnect():
 inp=io.BytesIO(m({'seq':1,'type':'request','command':'initialize','arguments':{}})+m({'seq':2,'type':'request','command':'disconnect','arguments':{}}));out=io.BytesIO();serve(inp,out);assert b'supportsConfigurationDoneRequest' in out.getvalue()


