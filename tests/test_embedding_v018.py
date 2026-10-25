
from dataclasses import dataclass
import pytest
from pealang import PeaRuntime,RuntimeOptions,PeaPermissionError,to_pea,from_pea
SRC='''function add(a,b) { return a + b }\nexport add\n'''
def test_load_and_call():assert PeaRuntime().load(SRC).call('add',2,3)==5
def test_host_function():
 r=PeaRuntime(RuntimeOptions(permissions=frozenset({'math.double'}))).register_function('host.double',lambda x:x*2,'math.double')
 assert r.load('function work(x) { return host.double(x) }\nexport work').call('work',4)==8
def test_permission_denied():
 r=PeaRuntime().register_function('host.secret',lambda:42,'secret.read')
 with pytest.raises(PeaPermissionError):r.load('function work() { return host.secret() }\nexport work').call('work')
def test_instruction_budget():
 r=PeaRuntime(RuntimeOptions(max_instructions=3,max_execution_ms=1000))
 with pytest.raises(Exception):r.eval('let x=0\nwhile x < 10 { x = x + 1 }')
@dataclass
class Employee:id:str;salary:float
def test_dataclass_conversion():
 value=to_pea(Employee('E1',10));assert value=={'id':'E1','salary':10};assert from_pea(value,Employee).id=='E1'
def test_register_module():
 r=PeaRuntime(RuntimeOptions(permissions=frozenset({'hr.get'}))).register_module('hr',{'get':lambda x:{'id':x}},'hr')
 assert r.load('function work() { return hr.get("E1").id }\nexport work').call('work')=='E1'

