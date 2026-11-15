import sys
sys.path.insert(0, '/Users/Rajesh/Documents/My Apps/GitHub/PeaLang')
from pealang import execute

# Test simple dict literal
src = 'let p = {a: 1, b: 2}\\nprint p.a'
out = []
execute(src, output=out.append, source_name='test.pea')
print('Dict literal output:', out)

# Test with type
src2 = 'type Point = {x: Int, y: Int}\\nlet erased = erase_types(\\'type Point = {x: Int, y: Int}\\\\nlet p = {x: 1, y: 2}\\')\\nprint erased'
# Actually let me just test step by step