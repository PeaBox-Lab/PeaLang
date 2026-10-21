
from pealang.editor import diagnostics,symbols,definition,completions,hover

def test_diagnostics_valid(): assert diagnostics('let x = 1\nprint x') == []
def test_diagnostics_invalid(): assert diagnostics('let =')['0' if False else 0]['severity'] == 'error'
def test_symbols_and_definition():
    src='let answer = 42\nfunction add(a) { return a + answer }'
    names={x['name'] for x in symbols(src)}; assert {'answer','add'} <= names
    assert definition(src,'add')['kind']=='function'
def test_completion(): assert 'function' in completions('', 'fun')
def test_hover(): assert hover('let total = 1','total')['kind']=='variable'
