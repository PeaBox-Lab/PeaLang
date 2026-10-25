

from pealang import SemanticAnalyzer

def check(src):return SemanticAnalyzer().analyze(src)
def codes(src):return [x.code for x in check(src).diagnostics]
def test_valid_function_return():assert check('function add(a: Int,b: Int) -> Int {\n return a+b\n}').ok
def test_wrong_return_type():assert 'F201' in codes('function f() -> Int {\n return "x"\n}')
def test_missing_return():assert 'F202' in codes('function f() -> Int {\n let x=1\n}')
def test_unreachable_warning():assert 'F401' in codes('function f() -> Int {\n return 1\n print 2\n}')
def test_record_valid():assert check('type User={name:String,age:Int}\nlet u: User={"name":"A","age":2}').ok
def test_record_missing():assert 'R201' in codes('type User={name:String,age:Int}\nlet u: User={"name":"A"}')
def test_record_unknown():assert 'R203' in codes('type User={name:String}\nlet u: User={"name":"A","bad":2}')
def test_record_wrong_field_type():assert 'R202' in codes('type User={name:String}\nlet u: User={"name":2}')
def test_call_arity():assert 'C201' in codes('function add(a:Int,b:Int)->Int{return a+b}\nprint add(1)')
def test_call_argument_type():assert 'C202' in codes('function echo(a:Int)->Int{return a}\nprint echo("bad")')
def test_numeric_inference():assert check('function f()->Int{\n return 1+2\n}').ok
def test_float_division():assert check('function f()->Float{\n return 4/2\n}').ok
def test_nullable_return_allows_null():assert check('function f()->String?{\n return null\n}').ok
def test_symbol_collection():assert check('let x: Int=1').symbols['x'].name=='Int'
def test_function_contract_collection():assert check('function f(a:String)->Int{\n return 1\n}').functions['f'].params[0][1].name=='String'


