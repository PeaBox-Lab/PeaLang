from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import json, math, os, time

class PeaError(Exception): pass

@dataclass
class Token:
    kind: str
    value: Any
    line: int
    col: int

KEYWORDS = {"let","const","print","if","else","while","for","in","function","return","true","false","null","and","or","not"}

class Lexer:
    def __init__(self, text:str): self.text=text; self.i=0; self.line=1; self.col=1
    def peek(self,n=0):
        j=self.i+n
        return self.text[j] if j < len(self.text) else "\0"
    def advance(self):
        c=self.peek(); self.i+=1
        if c=='\n': self.line+=1; self.col=1
        else: self.col+=1
        return c
    def tokens(self):
        out=[]
        two_ops={"==","!=","<=",">=","+=","-=","*=","/="}
        singles=set("+-*/%(){}[],:;<>!=")
        while self.i < len(self.text):
            c=self.peek()
            if c in ' \t\r': self.advance(); continue
            if c=='\n': out.append(Token('NEWLINE','\n',self.line,self.col)); self.advance(); continue
            if c=='#' or (c=='/' and self.peek(1)=='/'):
                while self.peek() not in ('\n','\0'): self.advance()
                continue
            line,col=self.line,self.col
            if c in ('"',"'"):
                q=self.advance(); s=''
                while self.peek()!=q:
                    if self.peek()=='\0': raise PeaError(f"Unterminated string at {line}:{col}")
                    if self.peek()=='\\':
                        self.advance(); esc=self.advance(); s += {'n':'\n','t':'\t','r':'\r','"':'"',"'":"'",'\\':'\\'}.get(esc,esc)
                    else: s+=self.advance()
                self.advance(); out.append(Token('STRING',s,line,col)); continue
            if c.isdigit():
                s=''
                while self.peek().isdigit(): s+=self.advance()
                if self.peek()=='.' and self.peek(1).isdigit():
                    s+=self.advance()
                    while self.peek().isdigit(): s+=self.advance()
                out.append(Token('NUMBER',float(s) if '.' in s else int(s),line,col)); continue
            if c.isalpha() or c=='_':
                s=''
                while self.peek().isalnum() or self.peek()=='_': s+=self.advance()
                out.append(Token(s.upper() if s in KEYWORDS else 'IDENT',s,line,col)); continue
            op=c+self.peek(1)
            if op in two_ops:
                self.advance(); self.advance(); out.append(Token(op,op,line,col)); continue
            if c in singles:
                self.advance(); out.append(Token(c,c,line,col)); continue
            raise PeaError(f"Unexpected character {c!r} at {line}:{col}")
        out.append(Token('EOF',None,self.line,self.col)); return out

class ReturnSignal(Exception):
    def __init__(self,v): self.value=v

class Env:
    def __init__(self,parent=None): self.parent=parent; self.values={}; self.const=set()
    def define(self,n,v,const=False):
        if n in self.values: raise PeaError(f"Variable '{n}' is already defined")
        self.values[n]=v
        if const: self.const.add(n)
    def get(self,n):
        if n in self.values: return self.values[n]
        if self.parent: return self.parent.get(n)
        raise PeaError(f"Undefined variable '{n}'")
    def set(self,n,v):
        if n in self.values:
            if n in self.const: raise PeaError(f"Cannot assign to constant '{n}'")
            self.values[n]=v; return v
        if self.parent: return self.parent.set(n,v)
        raise PeaError(f"Undefined variable '{n}'")

@dataclass
class UserFunction:
    params:list
    body:list
    closure:Env

class Interpreter:
    def __init__(self, output=None):
        self.output=output or print; self.global_env=Env(); self.env=self.global_env
        builtins={
            'range': lambda *a:list(range(*map(int,a))), 'len':len, 'str':lambda x:self.stringify(x),
            'number':lambda x:float(x), 'int':lambda x:int(float(x)), 'type':lambda x:type(x).__name__,
            'upper':lambda x:str(x).upper(), 'lower':lambda x:str(x).lower(), 'split':lambda x,s=None:str(x).split(s),
            'join':lambda s,x:str(s).join(map(str,x)), 'append':self._append, 'keys':lambda d:list(d.keys()),
            'values':lambda d:list(d.values()), 'json':lambda x:json.dumps(x,indent=2),
            'read':lambda p:open(p,encoding='utf-8').read(), 'write':self._write,
            'exists':os.path.exists, 'sqrt':math.sqrt, 'round':round, 'sleep':time.sleep
        }
        for k,v in builtins.items(): self.global_env.define(k,v,True)
    def _append(self,a,v): a.append(v); return a
    def _write(self,p,c):
        with open(p,'w',encoding='utf-8') as f: f.write(str(c))
        return p
    def stringify(self,v):
        if v is None:return 'null'
        if v is True:return 'true'
        if v is False:return 'false'
        if isinstance(v,float) and v.is_integer(): return str(int(v))
        if isinstance(v,(list,dict)): return json.dumps(v,ensure_ascii=False)
        return str(v)
    def run(self, program):
        result=None
        for stmt in program: result=self.exec_stmt(stmt)
        return result
    def exec_block(self,body,env=None):
        old=self.env; self.env=env or Env(old)
        try:
            r=None
            for s in body:r=self.exec_stmt(s)
            return r
        finally:self.env=old
    def exec_stmt(self,s):
        t=s[0]
        if t=='let': self.env.define(s[1],self.eval(s[2]),s[3]); return
        if t=='assign':
            val=self.eval(s[3]); cur=self.env.get(s[1]); op=s[2]
            if op!='=': val=self.apply(op[0],cur,val)
            return self.env.set(s[1],val)
        if t=='print': self.output(self.stringify(self.eval(s[1]))); return
        if t=='expr': return self.eval(s[1])
        if t=='if':
            if self.truth(self.eval(s[1])): return self.exec_block(s[2])
            if s[3] is not None:return self.exec_block(s[3])
        if t=='while':
            while self.truth(self.eval(s[1])): self.exec_block(s[2])
        if t=='for':
            seq=self.eval(s[2])
            for v in seq:
                e=Env(self.env); e.define(s[1],v); self.exec_block(s[3],e)
        if t=='function': self.env.define(s[1],UserFunction(s[2],s[3],self.env),True)
        if t=='return': raise ReturnSignal(self.eval(s[1]) if s[1] else None)
    def truth(self,v): return bool(v)
    def apply(self,op,a,b):
        if op=='+': return a+b
        if op=='-': return a-b
        if op=='*': return a*b
        if op=='/': return a/b
        if op=='%': return a%b
        if op=='==': return a==b
        if op=='!=': return a!=b
        if op=='<': return a<b
        if op=='<=': return a<=b
        if op=='>': return a>b
        if op=='>=': return a>=b
        if op=='and': return self.truth(a) and self.truth(b)
        if op=='or': return self.truth(a) or self.truth(b)
        raise PeaError(f"Unknown operator {op}")
    def eval(self,e):
        t=e[0]
        if t=='lit': return e[1]
        if t=='var': return self.env.get(e[1])
        if t=='list': return [self.eval(x) for x in e[1]]
        if t=='dict': return {self.eval(k):self.eval(v) for k,v in e[1]}
        if t=='unary':
            v=self.eval(e[2]); return (-v if e[1]=='-' else (not self.truth(v)))
        if t=='bin':
            if e[1]=='and' and not self.truth(self.eval(e[2])): return False
            if e[1]=='or' and self.truth(self.eval(e[2])): return True
            return self.apply(e[1],self.eval(e[2]),self.eval(e[3]))
        if t=='index': return self.eval(e[1])[self.eval(e[2])]
        if t=='call':
            f=self.eval(e[1]); args=[self.eval(x) for x in e[2]]
            if isinstance(f,UserFunction):
                if len(args)!=len(f.params): raise PeaError(f"Expected {len(f.params)} arguments, got {len(args)}")
                env=Env(f.closure)
                for n,v in zip(f.params,args):env.define(n,v)
                try:return self.exec_block(f.body,env)
                except ReturnSignal as r:return r.value
            if callable(f):
                try:return f(*args)
                except Exception as ex: raise PeaError(str(ex)) from ex
            raise PeaError('Value is not callable')

class Parser:
    def __init__(self,tokens): self.t=tokens; self.i=0
    def cur(self): return self.t[self.i]
    def match(self,*k):
        if self.cur().kind in k: return self.advance()
    def advance(self): x=self.cur(); self.i+=1; return x
    def need(self,k,msg=None):
        if self.cur().kind!=k:
            x=self.cur(); raise PeaError(msg or f"Expected {k} at {x.line}:{x.col}, got {x.kind}")
        return self.advance()
    def skip(self):
        while self.cur().kind in ('NEWLINE',';'):self.advance()
    def parse(self):
        out=[]; self.skip()
        while self.cur().kind!='EOF':out.append(self.statement()); self.skip()
        return out
    def statement(self):
        if self.match('LET'): return self.var_decl(False)
        if self.match('CONST'): return self.var_decl(True)
        if self.match('PRINT'):
            e=self.expression(); return ('print',e)
        if self.match('IF'): return self.if_stmt()
        if self.match('WHILE'):
            c=self.expression(); b=self.block(); return ('while',c,b)
        if self.match('FOR'):
            n=self.need('IDENT').value; self.need('IN'); seq=self.expression(); b=self.block(); return ('for',n,seq,b)
        if self.match('FUNCTION'): return self.function()
        if self.match('RETURN'):
            return ('return',None if self.cur().kind in ('NEWLINE',';','}') else self.expression())
        if self.cur().kind=='IDENT' and self.t[self.i+1].kind in ('=','+=','-=','*=','/='):
            n=self.advance().value; op=self.advance().kind; return ('assign',n,op,self.expression())
        return ('expr',self.expression())
    def var_decl(self,const):
        n=self.need('IDENT').value; self.need('='); return ('let',n,self.expression(),const)
    def block(self):
        self.skip(); self.need('{'); body=[]; self.skip()
        while self.cur().kind!='}':
            if self.cur().kind=='EOF': raise PeaError('Unterminated block')
            body.append(self.statement()); self.skip()
        self.need('}'); return body
    def if_stmt(self):
        c=self.expression(); yes=self.block(); self.skip(); no=None
        if self.match('ELSE'):
            if self.match('IF'):
                nested=self.if_stmt(); no=[nested]
            else:no=self.block()
        return ('if',c,yes,no)
    def function(self):
        n=self.need('IDENT').value; self.need('('); p=[]
        if self.cur().kind!=')':
            while True:
                p.append(self.need('IDENT').value)
                if not self.match(','):break
        self.need(')'); return ('function',n,p,self.block())
    def expression(self): return self.or_expr()
    def or_expr(self): return self.left(self.and_expr,('OR',))
    def and_expr(self): return self.left(self.equality,('AND',))
    def equality(self): return self.left(self.compare,('==','!='))
    def compare(self): return self.left(self.term,('<','<=','>','>='))
    def term(self): return self.left(self.factor,('+','-'))
    def factor(self): return self.left(self.unary,('*','/','%'))
    def left(self,sub,ops):
        e=sub()
        while self.cur().kind in ops:
            op=self.advance().value; e=('bin',op,e,sub())
        return e
    def unary(self):
        if self.cur().kind in ('-','NOT'):
            op=self.advance().value; return ('unary',op,self.unary())
        return self.postfix()
    def postfix(self):
        e=self.primary()
        while True:
            if self.match('('):
                a=[]
                if self.cur().kind!=')':
                    while True:
                        a.append(self.expression())
                        if not self.match(','):break
                self.need(')'); e=('call',e,a)
            elif self.match('['): idx=self.expression(); self.need(']'); e=('index',e,idx)
            else:break
        return e
    def primary(self):
        x=self.cur()
        if self.match('NUMBER','STRING'):return ('lit',x.value)
        if self.match('TRUE'):return ('lit',True)
        if self.match('FALSE'):return ('lit',False)
        if self.match('NULL'):return ('lit',None)
        if self.match('IDENT'):return ('var',x.value)
        if self.match('('): e=self.expression(); self.need(')'); return e
        if self.match('['):
            a=[]
            if self.cur().kind!=']':
                while True:
                    a.append(self.expression())
                    if not self.match(','):break
            self.need(']'); return ('list',a)
        if self.match('{'):
            pairs=[]
            if self.cur().kind!='}':
                while True:
                    k=self.expression(); self.need(':'); v=self.expression(); pairs.append((k,v))
                    if not self.match(','):break
            self.need('}'); return ('dict',pairs)
        raise PeaError(f"Unexpected token {x.kind} at {x.line}:{x.col}")

def compile_source(source): return Parser(Lexer(source).tokens()).parse()
def execute(source,output=None, interpreter=None):
    vm=interpreter or Interpreter(output=output)
    return vm.run(compile_source(source))
