def disassemble(module):
 lines=[f'PEAC {module.version}  source={module.source_name}',f'constants ({len(module.constants)}):']
 for i,v in enumerate(module.constants):lines.append(f'  {i:04} {v!r}')
 def code(c):
  lines.append(f'\ncode {c.name}({", ".join(c.params)}):')
  for i,x in enumerate(c.instructions):lines.append(f'  {i:04} L{x.line:<4} {x.op:<16} {"" if x.arg is None else x.arg}')
 code(module.code)
 for c in module.functions.values():code(c)
 return '\n'.join(lines)+'\n'

