import io,json
import pytest
from pealang import VMRuntime,RuntimeOptions,PeaPermissionError
from pealang.vm_dap import serve

def test_vm_host_permission_allowed():
 r=VMRuntime(RuntimeOptions(permissions=frozenset({'hr.get'}))).register_function('hr.get',lambda x:{'id':x},'hr.get')
 assert r.load('function work(){return hr.get("E1").id}\nexport work').call('work')=='E1'
def test_vm_host_permission_denied():
 r=VMRuntime().register_function('hr.get',lambda x:x,'hr.get')
 with pytest.raises(PeaPermissionError):r.load('function work(){return hr.get("E1")}\nexport work').call('work')
def test_vm_registered_module():
 r=VMRuntime(RuntimeOptions(permissions=frozenset({'math.double'}))).register_module('mathx',{'double':lambda x:x*2},'math')
 assert r.load('function work(x){return mathx.double(x)}\nexport work').call('work',4)==8
def msg(o):
 b=json.dumps(o).encode();return f'Content-Length: {len(b)}\r\n\r\n'.encode()+b
def test_vm_dap_initialize(tmp_path):
 p=tmp_path/'a.pea';p.write_text('print "ok"');req=[{'seq':1,'type':'request','command':'initialize','arguments':{}},{'seq':2,'type':'request','command':'launch','arguments':{'program':str(p)}},{'seq':3,'type':'request','command':'configurationDone','arguments':{}},{'seq':4,'type':'request','command':'disconnect','arguments':{}}];out=io.BytesIO();serve(io.BytesIO(b''.join(msg(x) for x in req)),out);raw=out.getvalue();assert b'initialized' in raw and b'terminated' in raw and b'PeaLang VM' not in raw
def test_vm_dap_breakpoint(tmp_path):
 p=tmp_path/'b.pea';p.write_text('let x=1\nprint x');req=[{'seq':1,'type':'request','command':'initialize','arguments':{}},{'seq':2,'type':'request','command':'launch','arguments':{'program':str(p)}},{'seq':3,'type':'request','command':'setBreakpoints','arguments':{'source':{'path':str(p)},'breakpoints':[{'line':2}]}},{'seq':4,'type':'request','command':'configurationDone','arguments':{}},{'seq':5,'type':'request','command':'disconnect','arguments':{}}];out=io.BytesIO();serve(io.BytesIO(b''.join(msg(x) for x in req)),out);assert b'"event":"stopped"' in out.getvalue()

