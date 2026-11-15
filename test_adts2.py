import sys
sys.path.insert(0, '/Users/Rajesh/Documents/My Apps/GitHub/PeaLang')
from pealang import execute
from pealang.type_system import TypeChecker, erase_types

def run(src):
    out = []
    execute(src, output=out.append, source_name='v.pea')
    return out

tc = TypeChecker()

print('=== ADT Type Declaration Tests ===')
print()

# Test 1: Record-style type (existing functionality)
src1 = 'type Point = {x: Int, y: Int}'
r1 = tc.check(src1)
print(f'1. Record type declaration: {r1.ok}')
print(f'   Records: {r1.records}')

# Test 2: ADT-style type (new)
src2 = 'type Result = Ok | Err'
r2 = tc.check(src2)
print(f'2. ADT type declaration: {r2.ok}')
print(f'   Records: {r2.records}')

# Test 3: ADT with args
src3 = 'type Result = Ok value | Err message'
r3 = tc.check(src3)
print(f'3. ADT with args: {r3.ok}')
print(f'   Records: {r3.records}')

# Test 4: Type erasure with ADT
src4 = 'type Result = Ok | Err\nlet r: Result = Ok'
out4 = run(src4)
erased = erase_types(src4)
t_not = 'type' not in erased.lower()
print(f'4. Type erasure: type stripped={t_not}')

# Test 5: Pattern matching still works
src5 = 'let x = 2\nmatch x { 1 => print "one"; 2 => print "two"; _ => print "other" }'
out5 = run(src5)
print(f'5. Pattern matching: {out5}')
assert out5 == ['two'], f'Expected [two], got {out5}'

# Test 6: let with type annotation
src6 = 'type Point = {x: Int, y: Int}\nlet p: Point = {x: 1, y: 2}\nprint p.x'
out6 = run(src6)
print(f'6. Type annotation usage: {out6}')

print()
print('=== ADT tests completed! ===')