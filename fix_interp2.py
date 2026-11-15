#!/usr/bin/env python
with open('pealang/interpreter.py', 'r') as f:
    lines = f.readlines()

# Fix line 397 (index 396): change from ai_ns,self.ai_service=... to separate statements
old_line = "        ai_ns,self.ai_service=build_ai_namespace();self.global_env.define('ai',ai_ns,True)\n"
new_line = "        ai_ns=build_ai_namespace(); self.ai_service = ai_ns; self.global_env.define('ai',ai_ns,True)\n"

# Check if old line exists
if lines[396] == old_line:
    print('Old line found, replacing...')
    lines[396] = new_line
    with open('pealang/interpreter.py', 'w') as f:
        f.writelines(lines)
    print('Fixed interpreter.py line 397')
else:
    print('Line format different')
    print(f'Current line 397: {repr(lines[396])}')