



from pealang import TypeChecker,parse_type,execute

def test_parse_generic():assert str(parse_type('List<String>'))=='List<String>'
def test_parse_nullable():assert str(parse_type('Employee?'))=='Employee?'
def test_parse_union():assert str(parse_type('String | Int'))=='Union<String, Int>'
def test_valid_typed_declaration():assert TypeChecker().check('let x: Int = 3').ok
def test_invalid_assignment():assert not TypeChecker().check('let x: Int = "bad"').ok
def test_unknown_type():assert not TypeChecker().check('let x: Missing = 1').ok
def test_number_accepts_int():assert TypeChecker().check('let x: Number = 1').ok
def test_nullable_accepts_null():assert TypeChecker().check('let x: String? = null').ok
def test_record_and_function_signature():
 src='type User = {name: String, age: Int}\nfunction greet(user: User) -> String { return user.name }'
 assert TypeChecker().check(src).ok
def test_typed_code_executes():
 out=[];execute('let x: Int = 3\nprint x',output=out.append);assert out==['3']
def test_typed_function_executes():
 out=[];execute('function add(a: Int, b: Int) -> Int { return a+b }\nprint add(2,3)',output=out.append);assert out==['5']




