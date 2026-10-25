

from pathlib import Path
from pealang import compile_source_to_bytecode,VirtualMachine,BytecodeModule,disassemble

def run(src):
 out=[];m=compile_source_to_bytecode(src,'test.pea');VirtualMachine(out.append).run(m);return out,m
def test_arithmetic():assert run('print 2 + 3 * 4')[0]==[14]
def test_variables():assert run('let x=4\nprint x+1')[0]==[5]
def test_if():assert run('let x=4\nif x > 2 { print "yes" } else { print "no" }')[0]==['yes']
def test_while():assert run('let x=0\nwhile x < 3 { print x\nx=x+1 }')[0]==[0,1,2]
def test_for():assert run('for x in [1,2,3] { print x }')[0]==[1,2,3]
def test_function():assert run('function add(a,b) { return a+b }\nprint add(3,4)')[0]==[7]
def test_dict_property():assert run('let x={"name":"Pea"}\nprint x.name')[0]==['Pea']
def test_roundtrip(tmp_path):
 m=compile_source_to_bytecode('print "hello"');p=tmp_path/'x.peac';m.save(p);out=[];VirtualMachine(out.append).run(BytecodeModule.load(p));assert out==['hello']
def test_disassembly():assert 'PRINT' in disassemble(compile_source_to_bytecode('print 1'))
def test_export():
 m=compile_source_to_bytecode('function add(a,b){return a+b}\nexport add');vm=VirtualMachine();vm.run(m);assert 'add' in vm.exports
def test_instruction_limit():
 import pytest
 with pytest.raises(Exception):VirtualMachine(max_instructions=4).run(compile_source_to_bytecode('let x=0\nwhile x<10 {x=x+1}'))


