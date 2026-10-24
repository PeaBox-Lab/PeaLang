import pytest
from pealang import compile_source_to_bytecode,VirtualMachine,VMRuntime,execute

def vmout(src):
 out=[];VirtualMachine(out.append).run(compile_source_to_bytecode(src,'parity.pea'));return out
def intout(src):
 out=[];execute(src,output=out.append);return [int(x) if isinstance(x,str) and x.isdigit() else x for x in out]
def test_break():assert vmout('for x in [1,2,3,4] { if x == 3 { break } print x }')==[1,2]
def test_continue():assert vmout('for x in [1,2,3] { if x == 2 { continue } print x }')==[1,3]
def test_compound_assignment():assert vmout('let x=2\nx += 3\nprint x')==[5]
def test_property_assignment():assert vmout('let x={"a":1}\nx.a=8\nprint x.a')==[8]
def test_index_assignment():assert vmout('let x=[1,2]\nx[0]=9\nprint x[0]')==[9]
def test_throw():
 with pytest.raises(Exception,match='boom'):vmout('throw "boom"')
def test_parity_arithmetic():
 src='function add(a,b){return a+b}\nprint add(2,5)';assert vmout(src)==intout(src)
def test_vm_embedding_call():
 m=VMRuntime().load('function add(a,b){return a+b}\nexport add');assert m.call('add',4,6)==10
def test_vm_breakpoint():
 src='let x=1\nprint x';m=compile_source_to_bytecode(src,'debug.pea');vm=VirtualMachine(output=lambda x:None);vm.module=m;vm.add_breakpoint(2,'debug.pea');e=vm.run(m);assert e['reason']=='breakpoint' and e['line']==2
def test_vm_stack_frames():
 m=compile_source_to_bytecode('function add(a,b){return a+b}\nprint add(1,2)','stack.pea');events=[]
 def hook(vm,frame,ins):
  if frame.name=='add':events.extend(vm.stack_trace())
 VirtualMachine(output=lambda x:None,debug_hook=hook).run(m);assert any(x['name']=='add' for x in events)
