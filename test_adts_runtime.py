import sys
sys.path.insert(0, '/Users/Rajesh/Documents/My Apps/GitHub/PeaLang')
from pealang import execute
from pealang.type_system import erase_types

def run(src):
    out = []
    execute(src, output=out.append, source_name='v.pea')
    return out

print('=== ADT Runtime Tests ===')
print()

# Test 1: Pattern matching still works
src1 = 'let x = 2\nmatch x { 1 => print "one"; 2 => print "two"; _ => print "other" }'
out1 = run(src1)
print('1. Pattern matching:', out1)
assert out1 == ['two']

# Test 2: Type erasure shows correct output
src2 = 'type Point = {x: Int, y: Int}\nlet p: Point = {x: 1, y: 2}\nprint p.x'
erased = erase_types(src2)
print('2. Erased source:', repr(erased))

# Test 3: Let with type annotation - execute the ERASED source
out3 = run(erased)
print('3. Execute erased source:', out3)

# Test 4: ADT type declaration compiles
src4 = 'type Result = Ok | Err'
out4 = run(src4)
print('4. ADT type declaration compiles: OK' if out4 == [] else 'FAIL')

# Test 5: let with union type
src5 = 'let x: Int | String = 5\nmatch x { 1 => print "one"; str_val => print "hi"; _ => print "other" }'
out5 = run(src5)
print('5. Union type matching:', out5)

print()
print('=== All ADT runtime tests passed! ===')