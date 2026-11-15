import sys
sys.path.insert(0, '/Users/Rajesh/Documents/My Apps/GitHub/PeaLang')
from pealang import execute

def run(src):
    out = []
    execute(src, output=out.append, source_name='v.pea')
    return out

# Test type declaration
src1 = 'type Point = {x: Int, y: Int}'
out1 = run(src1)
print('1. Type declaration compiles:', out1 == [])

# Test pattern matching still works
src2 = 'let x = 2\nmatch x { 1 => print "one"; 2 => print "two"; _ => print "other" }'
out2 = run(src2)
print('2. Pattern matching:', out2)
assert out2 == ['two']

# Test basic operations
src3 = 'let x = 1\nprint "x: {x}"'
out3 = run(src3)
print('3. Interpolated string:', out3)
assert out3 == ['x: 1']

print()
print('=== All baselines verified! ===')