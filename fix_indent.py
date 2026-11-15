#!/usr/bin/env python
with open('pealang/interpreter.py', 'r') as f:
    lines = f.readlines()

# Fix line 397 (index 396) to have 8-space indentation
lines[396] = '        ai_ns=build_ai_namespace();self.global_env.define("ai",ai_ns,True)\n'

with open('pealang/interpreter.py', 'w') as f:
    f.writelines(lines)
print('Fixed indentation')