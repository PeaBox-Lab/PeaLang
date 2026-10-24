from pathlib import Path
from pealang import TypeRef,parse_type,substitute_type,infer_generic_bindings,parse_generic_functions,parse_protocols,protocol_conforms,option_type,result_type,future_type,analyze_project,execute
def test_generic_parse():
 g=parse_generic_functions('function first<T>(items: List<T>) -> T? { return null }')['first'];assert g.type_params==('T',) and g.params[0][1].args[0].name=='T'
def test_substitution():assert str(substitute_type(parse_type('List<T>'),{'T':TypeRef('String')}))=='List<String>'
def test_generic_inference():assert infer_generic_bindings(parse_type('List<T>'),parse_type('List<Int>'),{'T'})['T'].name=='Int'
def test_result_semantics():assert str(result_type(TypeRef('Int'),TypeRef('String')))=='Result<Int, String>'
def test_option_semantics():assert str(option_type(TypeRef('Int')))=='Option<Int>'
def test_future_semantics():assert str(future_type(TypeRef('String')))=='Future<String>'
def test_protocol_parse():
 p=parse_protocols('protocol Printable { function to_string() -> String\n }')['Printable'];assert p.methods[0][0]=='to_string'
def test_protocol_structural_conformance():
 p=parse_protocols('protocol Printable { function to_string() -> String\n }')['Printable'];assert protocol_conforms({'to_string':TypeRef('Function')},p)
def test_generic_runtime_erasure():
 out=[];execute('function id<T>(x: T) -> T { return x }\nprint id(3)',output=out.append);assert out==['3']
def test_cross_module_collection(tmp_path):
 a=tmp_path/'a.pea';b=tmp_path/'b.pea';a.write_text('function a(x:Int)->Int{ return x }');b.write_text('type User={name:String}\nfunction b()->Int{ return 1 }');r=analyze_project([a,b]);assert len(r['functions'])==2 and 'b.User' in r['records']
def test_nested_generic_substitution():assert str(substitute_type(parse_type('Result<T, E>'),{'T':TypeRef('Int'),'E':TypeRef('String')}))=='Result<Int, String>'
def test_generic_conflict():
 import pytest
 with pytest.raises(ValueError):infer_generic_bindings(parse_type('Tuple<T,T>'),parse_type('Tuple<Int,String>'),{'T'})
