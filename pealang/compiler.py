"""AST to PeaLang bytecode compiler."""
from .ast_nodes import *
from .parser import parse_source
from .bytecode import BytecodeModule,CodeObject,Instruction,Op
class CompileError(Exception):pass
from .metaprogramming import expand_source_macros
class Compiler:
 def __init__(self,source_name='<input>'):self.module=BytecodeModule(source_name=source_name);self.code=self.module.code;self.code.source_name=source_name;self.loops=[]
 def emit(self,op,arg=None,node=None):self.code.instructions.append(Instruction(op.value if hasattr(op,'value') else op,arg,getattr(getattr(node,'span',None),'line',1)));return len(self.code.instructions)-1
 def patch(self,i,arg):self.code.instructions[i].arg=arg
 def _pattern_to_string(self, pattern):
  """Convert a pattern AST node to its string representation for match_pattern."""
  from .ast_nodes import WildcardPattern, LiteralPattern, VariablePattern, ListPattern, DictPattern, OrPattern
  if isinstance(pattern, WildcardPattern):
    return "_"
  if isinstance(pattern, LiteralPattern):
    v = pattern.value
    if isinstance(v, bool):
      return "true" if v else "false"
    if isinstance(v, str):
      return f'"{v}"'
    return str(v)
  if isinstance(pattern, VariablePattern):
    return pattern.name
  if isinstance(pattern, ListPattern):
    elems = [self._pattern_to_string(e) for e in pattern.elements]
    rest = pattern.rest
    if rest:
      elems.append(rest)
    return "[" + ", ".join(elems) + "]"
  if isinstance(pattern, DictPattern):
    fields = []
    for k, p in pattern.fields:
      k_str = self._pattern_to_string(k) if hasattr(k, '__class__') else str(k)
      p_str = self._pattern_to_string(p)
      fields.append(f"{k_str}: {p_str}")
    return "{" + ", ".join(fields) + "}"
  if isinstance(pattern, OrPattern):
    pats = [self._pattern_to_string(p) for p in pattern.patterns]
    return " | ".join(pats)
  return str(pattern)

 def const(self,v):
  try:return self.module.constants.index(v)
  except ValueError:self.module.constants.append(v);return len(self.module.constants)-1
 def compile(self,program):
  for s in program.statements:self.stmt(s)
  self.emit(Op.HALT);return self.module
 def block(self,items):
  for s in items:self.stmt(s)
 def stmt(self,s):
  if isinstance(s,VarDecl):self.expr(s.value) if s.value else self.emit(Op.NULL,node=s);self.emit(Op.STORE,s.name,s);return
  if isinstance(s,Assign):
   if isinstance(s.target,Variable):
    if s.op!='=':self.expr(s.target);self.expr(s.value);self.emit({'+=':Op.ADD,'-=':Op.SUB,'*=':Op.MUL,'/=':Op.DIV,'%=':Op.MOD}[s.op],node=s)
    else:self.expr(s.value)
    self.emit(Op.STORE,s.target.name,s);return
   if isinstance(s.target,Property):self.expr(s.target.target);self.expr(s.value);self.emit(Op.SET_PROPERTY,s.target.name,s);return
   if isinstance(s.target,Index):self.expr(s.target.target);self.expr(s.target.index);self.expr(s.value);self.emit(Op.SET_INDEX,node=s);return
   raise CompileError('Unsupported assignment target')
  if isinstance(s,PrintStmt):self.expr(s.value);self.emit(Op.PRINT,node=s);return
  if isinstance(s,ExprStmt):self.expr(s.value);self.emit(Op.POP,node=s);return
  if isinstance(s,ReturnStmt):self.expr(s.value) if s.value else self.emit(Op.NULL,node=s);self.emit(Op.RETURN,node=s);return
  if isinstance(s,IfStmt):
   self.expr(s.condition);jf=self.emit(Op.JUMP_IF_FALSE,None,s);self.block(s.then_body);j=self.emit(Op.JUMP,None,s);self.patch(jf,len(self.code.instructions));self.block(s.else_body or []);self.patch(j,len(self.code.instructions));return
  if isinstance(s,WhileStmt):
   start=len(self.code.instructions);self.expr(s.condition);end=self.emit(Op.JUMP_IF_FALSE,None,s);ctx={'continue':start,'breaks':[]};self.loops.append(ctx);self.block(s.body);self.loops.pop();self.emit(Op.JUMP,start,s);target=len(self.code.instructions);self.patch(end,target)
   for i in ctx['breaks']:self.patch(i,target)
   return
  if isinstance(s,ForStmt):
   if getattr(s,'pattern',None):raise CompileError('Destructuring for is not supported in bytecode')
   self.expr(s.iterable);self.emit(Op.ITER,node=s);start=len(self.code.instructions);end=self.emit(Op.ITER_NEXT,{'name':s.name,'end':None},s);ctx={'continue':start,'breaks':[]};self.loops.append(ctx);self.block(s.body);self.loops.pop();self.emit(Op.JUMP,start,s);cleanup=len(self.code.instructions);self.emit(Op.CLOSE_ITER,node=s);target=len(self.code.instructions);self.code.instructions[end].arg['end']=target
   for i in ctx['breaks']:self.patch(i,cleanup)
   return
  if isinstance(s,BreakStmt):
   if not self.loops:raise CompileError('break outside loop')
   self.loops[-1]['breaks'].append(self.emit(Op.JUMP,None,s));return
  if isinstance(s,ContinueStmt):
   if not self.loops:raise CompileError('continue outside loop')
   self.emit(Op.JUMP,self.loops[-1]['continue'],s);return
  if isinstance(s,MatchStmt):
   # Compile match statement to bytecode
   # 1. Emit the value to match
   self.expr(s.value)
   # 2. For each case, compile pattern matching
   for i, case in enumerate(s.cases):
    # Emit the pattern as a string representation
    pattern_str = self._pattern_to_string(case.pattern)
    # Push pattern string as constant
    self.emit(Op.CONST, self.const(pattern_str))
    # Call match_pattern(pattern_str, value) - 2 args: pattern and value
    # match_pattern returns {} (truthy after NOT) or None (falsy after NOT)
    self.emit(Op.CALL, 2)
    # NOT the result: {} -> True, None -> False
    self.emit(Op.NOT)
    # JUMP_IF_FALSE to the case body if match succeeded
    jt_idx = len(self.code.instructions)  # save position for patching
    self.emit(Op.JUMP_IF_FALSE, None, s)
    # Emit the case body
    self.block(case.body)
    # After the body, emit JUMP to skip to after the match statement
    jf_idx = len(self.code.instructions)
    self.emit(Op.JUMP, None, s)
    # Patch the JUMP_IF_FALSE to skip over this case body
    target = len(self.code.instructions)
    self.code.instructions[jt_idx].arg = target
    # Patch the last JUMP's target (if not the last case)
    if i < len(s.cases) - 1:
      # The JUMP after this case's body should go to the next case's JUMP_IF_FALSE check
      # We need to link them properly
      self.code.instructions[jf_idx].arg = len(self.code.instructions) + 1  # approximate
    else:
      # Last case - JUMP to after the match statement
      self.code.instructions[jf_idx].arg = len(self.code.instructions) + 1
   # Pop the match result
   self.emit(Op.POP, node=s)
   return
  if isinstance(s,ThrowStmt):self.expr(s.value);self.emit(Op.RAISE,node=s);return
  if isinstance(s,TryStmt):
   push=self.emit(Op.PUSH_HANDLER,{'catch':None,'finally':None,'end':None,'name':s.catch_name,'catch_type':getattr(s,'catch_type',None)},s);self.block(s.try_body);self.emit(Op.POP_HANDLER,node=s)
   normal_finally=len(self.code.instructions)
   if s.finally_body:self.block(s.finally_body)
   jump_end=self.emit(Op.JUMP,None,s);catch_target=None
   if s.catch_body is not None:
    catch_target=len(self.code.instructions);self.block(s.catch_body)
    if s.finally_body:self.block(s.finally_body)
   end=len(self.code.instructions);self.patch(jump_end,end)
   self.code.instructions[push].arg.update({'catch':catch_target,'finally':normal_finally if s.finally_body else None,'end':end})
   return
  if isinstance(s,ImportStmt):self.emit(Op.IMPORT,{'path':s.path,'alias':s.alias},s);return
  if isinstance(s,FunctionStmt):
   old=self.code;params=[getattr(p,'name',str(p)) for p in s.params];defaults={};
   for p in s.params:
    if getattr(p,'default',None) is not None:
     if isinstance(p.default,Literal):defaults[p.name]=p.default.value
     else:raise CompileError('VM default parameters must be literals in 0.22')
   fn=CodeObject(s.name,params,source_name=self.module.source_name,defaults=defaults);self.code=fn;self.block(s.body);self.emit(Op.NULL);self.emit(Op.RETURN);self.module.functions[s.name]=fn;self.code=old;self.emit(Op.FUNCTION,s.name,s);self.emit(Op.STORE,s.name,s);return
  if isinstance(s,ExportStmt):self.emit(Op.EXPORT,s.name,s);return
  raise CompileError(f'Unsupported statement: {type(s).__name__}')
 def expr(self,e):
  if isinstance(e,Literal):
   if e.value is None:self.emit(Op.NULL,node=e)
   elif e.value is True:self.emit(Op.TRUE,node=e)
   elif e.value is False:self.emit(Op.FALSE,node=e)
   else:self.emit(Op.CONST,self.const(e.value),e)
  elif isinstance(e,Variable):self.emit(Op.LOAD,e.name,e)
  elif isinstance(e,ListExpr):
   for x in e.items:self.expr(x)
   self.emit(Op.LIST,len(e.items),e)
  elif isinstance(e,DictExpr):
   for k,v in e.pairs:self.expr(k);self.expr(v)
   self.emit(Op.DICT,len(e.pairs),e)
  elif isinstance(e,Unary):self.expr(e.value);self.emit({'-':Op.NEG,'!':Op.NOT,'not':Op.NOT}[e.op],node=e)
  elif isinstance(e,Binary):self.expr(e.left);self.expr(e.right);self.emit({'+':Op.ADD,'-':Op.SUB,'*':Op.MUL,'/':Op.DIV,'%':Op.MOD,'==':Op.EQ,'!=':Op.NE,'<':Op.LT,'<=':Op.LE,'>':Op.GT,'>=':Op.GE}[e.op],node=e)
  elif isinstance(e,Index):self.expr(e.target);self.expr(e.index);self.emit(Op.GET_INDEX,node=e)
  elif isinstance(e,Property):self.expr(e.target);self.emit(Op.GET_PROPERTY,e.name,e)
  elif isinstance(e,AwaitExpr):self.expr(e.value);self.emit(Op.AWAIT,node=e)
  elif isinstance(e,Call):
   self.expr(e.callee)
   for a in e.args:self.expr(a)
   self.emit(Op.CALL,len(e.args),e)
  else:raise CompileError(f'Unsupported expression: {type(e).__name__}')
def compile_source_to_bytecode(source,source_name='<input>'):return Compiler(source_name).compile(parse_source(source,source_name))
def compile_source_with_macros(source,source_name='<input>',expander=None):return compile_source_to_bytecode(expand_source_macros(source,expander),source_name)
