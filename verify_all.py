import sys
sys.path.insert(0, '/Users/Rajesh/Documents/My Apps/GitHub/PeaLang')
from pealang import execute
from pealang.type_system import TypeChecker, erase_types
from pealang.ai import build_ai_namespace

def run(src):
    out = []
    execute(src, output=out.append, source_name='v.pea')
    return out

print('=== Feature Verification ===')
print()

# Test 1: Interpolated string (quasisyntax baseline)
src1 = 'let x = 1\nprint "x: {x}"'
out1 = run(src1)
print('1. Interpolated string:', out1)
assert out1 == ['x: 1']

# Test 2: Type system
tc = TypeChecker()
result = tc.check('let x: Int = 5')
print('2. Type check:', result.ok)
assert result.ok

# Test 3: Type erasure
erased = erase_types('trait MyTrait\nlet x: Int = 5')
trait_stripped = 'trait' not in erased
print('3. Type erasure: trait stripped =', trait_stripped)
assert trait_stripped

# Test 4: Pattern matching
src4 = 'let x = 2\nmatch x { 1 => print "one"; 2 => print "two"; _ => print "other" }'
out4 = run(src4)
print('4. Pattern matching:', out4)
assert out4 == ['two']

# Test 5: AI namespace
ns = build_ai_namespace()
print('5. AI namespace keys:', list(ns.keys())[:5])
assert 'AIConfig' in ns

print()
print('=== All baselines verified! ===')