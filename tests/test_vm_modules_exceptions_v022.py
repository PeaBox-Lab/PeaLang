



from pathlib import Path
from pealang import compile_source_to_bytecode,VirtualMachine,BytecodeModule

def run(src,name='test.pea'):
 out=[];vm=VirtualMachine(out.append);result=vm.run(compile_source_to_bytecode(src,name));return out,result,vm
def test_try_catch():
 out,_,_=run('try { throw "boom" } catch error { print error }');assert out==['boom']
def test_try_finally_normal():
 out,_,_=run('try { print "work" } finally { print "cleanup" }');assert out==['work','cleanup']
def test_try_catch_finally():
 out,_,_=run('try { throw "bad" } catch error { print error } finally { print "done" }');assert out==['bad','done']
def test_default_argument():
 out,_,_=run('function greet(name="Pea") { return name }\nprint greet()');assert out==['Pea']
def test_override_default():
 out,_,_=run('function greet(name="Pea") { return name }\nprint greet("Rajesh")');assert out==['Rajesh']
def test_shared_closure_sees_later_update():
 out,_,_=run('let rate=2\nfunction calc(x){return x*rate}\nrate=3\nprint calc(4)');assert out==[12]
def test_module_import(tmp_path):
 lib=tmp_path/'lib.pea';lib.write_text('function add(a,b){return a+b}\nexport add')
 main=tmp_path/'main.pea';main.write_text('import "lib.pea" as lib\nprint lib.add(2,5)')
 out=[];VirtualMachine(out.append).run(compile_source_to_bytecode(main.read_text(),str(main)));assert out==[7]
def test_module_cache(tmp_path):
 lib=tmp_path/'lib.pea';lib.write_text('let value=3\nexport value')
 main=tmp_path/'main.pea';main.write_text('import "lib.pea" as a\nimport "lib.pea" as b\nprint a.value+b.value')
 out=[];vm=VirtualMachine(out.append);vm.run(compile_source_to_bytecode(main.read_text(),str(main)));assert out==[6] and len(vm.module_cache)==1
def test_peac_defaults_roundtrip(tmp_path):
 m=compile_source_to_bytecode('function f(x=4){return x}\nprint f()');p=tmp_path/'x.peac';m.save(p);out=[];VirtualMachine(out.append).run(BytecodeModule.load(p));assert out==[4]




