#!/usr/bin/env python
with open('pealang/parser.py', 'r') as f:
    lines = f.readlines()

# Find 'x=self.cur()' in the statement method and add SPLICE before it
for i, line in enumerate(lines):
    if 'x=self.cur()' in line and i > 60 and i < 80:
        # Insert SPLICE match before this line
        splice_code = '  if self.match(\"SPLICE\"):\\n      # Splice block - erased at runtime\\n      pass\\n'
        lines.insert(i, splice_code)
        print(f'Added SPLICE at line {i+1}')
        break

with open('pealang/parser.py', 'w') as f:
    f.writelines(lines)
print('SPLICE keyword added to parser')