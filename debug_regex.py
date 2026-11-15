import re
source = 'type Point = {x: Int, y: Int}\nlet p: Point = {x: 1, y: 2}\nprint p.x'
# Test matching just 'type'
m1 = re.search(r'(?m)^type', source)
print('type at start:', m1)

# Test the full pattern part by part
pattern_parts = [
    r'(?m)^',
    r'[ \t]*type',
    r'[ \t]+[A-Za-z_]\w*',
    r'[ \t]*=',
    r'[ \t]*\\{',
]
for i, p in enumerate(pattern_parts):
    m = re.search(p, source)
    print(f'Part {i+1} "{p}": {m}')

# Try the full regex
pattern = r'(?m)^[ \t]*type[ \t]+[A-Za-z_]\w*[ \t]*=[ \t]*\{[^{}]*\}[ \t]*(?:\n|$)'
m = re.search(pattern, source)
print('Full pattern match:', m)
if m:
    print('Matched group:', repr(m.group()))