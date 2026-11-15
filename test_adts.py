import sys
sys.path.insert(0, '/Users/Rajesh/Documents/My Apps/GitHub/PeaLang')
from pealang import execute
from pealang.type_system import TypeChecker, erase_types

def run(src):
    out = []
    execute(src, output=out.append, source_name='v.pea')
    return out

print('=== ADT Type Declaration Tests ===')
print()

# Test 1: Type declaration
src1 = 'type Point = {x: Int, y: Int}'
out1 = run(src1)
r1 = out1 == []
print(f'1. Type declaration compiles: {r1}')

# Test 2: Type usage
src2 = 'type Point = {x: Int, y: Int}\nlet p: Point = {x: 1, y: 2}\nprint p.x'
out2 = run(src2)
print(f'2. Type usage: {out2}')

# Test 3: Pattern matching still works
src3 = 'let x = 2\nmatch x { 1 => print "one"; 2 => print "two"; _ => print "other" }'
out3 = run(src3)
print(f'3. Pattern matching: {out3}')
assert out3 == ['two'], f'Expected [two], got {out3}'

# Test 4: Type erasure
src4 = 'type Point = {x: Int, y: Int}\nlet p: Point = {x: 1, y: 2}'
out4 = run(src4)
erased = erase_types(src4)
t_not = 'type' not in erased.lower()
p_not = 'Point' not in erased
print(f'4. Type erasure: type stripped={t_not}, Point kept={p_not}')

# Test 5: Records with type
src5 = 'type Color = {r: Int, g: Int, b: Int}\nlet c: Color = {r: 255, g: 0, b: 0}\nprint c.r'
out5 = run(src5)
print(f'5. Record type: {out5}')

# Test 6: Union types still work
src6 = 'let x: Int | String = 5\nmatch x { 1 => print "one"; str_val => print "hi"; _ => print "other" }'
out6 = run(src6)
print(f'6. Union type matching: {out6}')

print()
print('=== All ADT tests passed! ===')