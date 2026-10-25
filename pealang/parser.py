

from __future__ import annotations
from .errors import PeaError
from .lexer import Lexer
from .ast_nodes import *
class Parser:
    def __init__(self,tokens,source_name='<input>'):self.t=tokens;self.i=0;self.source_name=source_name;self.loop_depth=0
    def cur(self):return self.t[self.i]
    def advance(self):x=self.cur();self.i+=1;return x
    def match(self,*k):
        if self.cur().kind in k:return self.advance()
    def need(self,k,msg=None):
        if self.cur().kind!=k:
            x=self.cur();raise PeaError(msg or f'Expected {k}, got {x.kind}',x.span,self.source_name)
        return self.advance()
    def skip(self):
        while self.cur().kind in ('NEWLINE',';'):self.advance()
    def parse(self):
        out=[];self.skip()
        while self.cur().kind!='EOF':out.append(self.statement());self.skip()
        return Program(out)
    def statement(self):
        x=self.cur()
        if self.match('LET'):return self.var_decl(False,x.span)
        if self.match('CONST'):return self.var_decl(True,x.span)
        if self.match('PRINT'):return PrintStmt(self.expression(),span=x.span)
        if self.match('IF'):return self.if_stmt(x.span)
        if self.match('WHILE'):
            c=self.expression();self.loop_depth+=1
            try:b=self.block()
            finally:self.loop_depth-=1
            return WhileStmt(c,b,span=x.span)
        if self.match('FOR'):
            n=self.need('IDENT').value;self.need('IN');seq=self.expression();self.loop_depth+=1
            try:b=self.block()
            finally:self.loop_depth-=1
            return ForStmt(n,seq,b,span=x.span)
        if self.match('ASYNC'):
            self.need('FUNCTION');return self.function(x.span)
        if self.match('FUNCTION'):return self.function(x.span)
        if self.match('RETURN'):return ReturnStmt(None if self.cur().kind in ('NEWLINE',';','}') else self.expression(),span=x.span)
        if self.match('BREAK'):
            if not self.loop_depth:raise PeaError("'break' is only valid inside a loop",x.span,self.source_name)
            return BreakStmt(span=x.span)
        if self.match('CONTINUE'):
            if not self.loop_depth:raise PeaError("'continue' is only valid inside a loop",x.span,self.source_name)
            return ContinueStmt(span=x.span)
        if self.match('IMPORT'):
            p=self.need('STRING','Expected a quoted module path after import');alias=None
            if self.match('AS'):alias=self.need('IDENT','Expected alias after as').value
            return ImportStmt(p.value,alias,span=x.span)
        if self.match('EXPORT'):
            name=self.need('IDENT','Expected symbol name after export');return ExportStmt(name.value,span=x.span)
        if self.match('ASSERT'):
            condition=self.expression();message=None
            if self.match(','):message=self.expression()
            return AssertStmt(condition,message,span=x.span)
        if self.match('THROW'):return ThrowStmt(self.expression(),span=x.span)
        if self.match('TRY'):
            body=self.block();self.skip();name=None;catch_body=None;finally_body=None
            if self.match('CATCH'):
                if self.cur().kind=='IDENT':name=self.advance().value
                catch_body=self.block();self.skip()
            if self.match('FINALLY'):finally_body=self.block()
            if catch_body is None and finally_body is None:raise PeaError('try requires catch or finally',x.span,self.source_name)
            return TryStmt(body,name,catch_body,finally_body,span=x.span)
        expr=self.expression()
        if self.cur().kind in ('=','+=','-=','*=','/='):
            if not isinstance(expr,(Variable,Index,Property)):raise PeaError('Invalid assignment target',expr.span,self.source_name)
            op=self.advance().kind;return Assign(expr,op,self.expression(),span=x.span)
        return ExprStmt(expr,span=x.span)
    def var_decl(self,const,span):
        n=self.need('IDENT').value;self.need('=');return VarDecl(n,self.expression(),const,span=span)
    def block(self):
        self.skip();self.need('{');body=[];self.skip()
        while self.cur().kind!='}':
            if self.cur().kind=='EOF':raise PeaError('Unterminated block',self.cur().span,self.source_name)
            body.append(self.statement());self.skip()
        self.need('}');return body
    def if_stmt(self,span):
        c=self.expression();yes=self.block();self.skip();no=None
        if self.match('ELSE'):
            if self.match('IF'):no=[self.if_stmt(self.t[self.i-1].span)]
            else:no=self.block()
        return IfStmt(c,yes,no,span=span)
    def function(self,span):
        n=self.need('IDENT').value;self.need('(');p=[];saw_default=False
        if self.cur().kind!=')':
            while True:
                pt=self.need('IDENT');default=None
                if self.match('='):default=self.expression();saw_default=True
                elif saw_default:raise PeaError('Required parameter cannot follow a default parameter',pt.span,self.source_name)
                p.append(Param(pt.value,default,span=pt.span))
                if not self.match(','):break
        self.need(')');return FunctionStmt(n,p,self.block(),span=span)
    def expression(self):return self.or_expr()
    def or_expr(self):return self.left(self.and_expr,('OR',))
    def and_expr(self):return self.left(self.equality,('AND',))
    def equality(self):return self.left(self.compare,('==','!='))
    def compare(self):return self.left(self.term,('<','<=','>','>='))
    def term(self):return self.left(self.factor,('+','-'))
    def factor(self):return self.left(self.unary,('*','/','%'))
    def left(self,sub,ops):
        e=sub()
        while self.cur().kind in ops:
            op=self.advance();e=Binary(op.value,e,sub(),span=op.span)
        return e
    def unary(self):
        if self.match('AWAIT'):
            return AwaitExpr(self.unary(),span=self.t[self.i-1].span)
        if self.cur().kind in ('-','NOT'):
            op=self.advance();return Unary(op.value,self.unary(),span=op.span)
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
                self.need(')');e=Call(e,a,span=e.span)
            elif self.match('['):idx=self.expression();self.need(']');e=Index(e,idx,span=e.span)
            elif self.match('.'):
                name=self.need('IDENT','Expected property name after dot');e=Property(e,name.value,span=e.span)
            else:break
        return e
    def primary(self):
        x=self.cur()
        if self.match('NUMBER'):return Literal(x.value,span=x.span)
        if self.match('STRING'):
            if '{' in x.value:return self.interpolated(x)
            return Literal(x.value,span=x.span)
        if self.match('TRUE'):return Literal(True,span=x.span)
        if self.match('FALSE'):return Literal(False,span=x.span)
        if self.match('NULL'):return Literal(None,span=x.span)
        if self.match('IDENT'):return Variable(x.value,span=x.span)
        if self.match('PARALLEL'):
            self.skip();self.need('{');items=[];self.skip()
            while self.cur().kind!='}':
                items.append(self.expression());self.skip()
            self.need('}');return ParallelExpr(items,span=x.span)
        if self.match('('):e=self.expression();self.need(')');return e
        if self.match('['):
            a=[]
            if self.cur().kind!=']':
                while True:
                    a.append(self.expression())
                    if not self.match(','):break
            self.need(']');return ListExpr(a,span=x.span)
        if self.match('{'):
            pairs=[]
            if self.cur().kind!='}':
                while True:
                    k=self.expression();self.need(':');v=self.expression();pairs.append((k,v))
                    if not self.match(','):break
            self.need('}');return DictExpr(pairs,span=x.span)
        raise PeaError(f'Unexpected token {x.kind}',x.span,self.source_name)
    def interpolated(self,tok):
        text=tok.value;parts=[];i=0;buf=''
        while i<len(text):
            if text[i]=='{' and i+1<len(text) and text[i+1]=='{':buf+='{';i+=2;continue
            if text[i]=='}' and i+1<len(text) and text[i+1]=='}':buf+='}';i+=2;continue
            if text[i]=='{':
                if buf:parts.append(buf);buf=''
                end=text.find('}',i+1)
                if end<0:raise PeaError('Unterminated interpolation expression',tok.span,self.source_name)
                src=text[i+1:end].strip()
                if not src:raise PeaError('Empty interpolation expression',tok.span,self.source_name)
                sub=Parser(Lexer(src,self.source_name).tokens(),self.source_name).parse()
                if len(sub.statements)!=1 or not isinstance(sub.statements[0],ExprStmt):raise PeaError('Interpolation must contain an expression',tok.span,self.source_name)
                parts.append(sub.statements[0].value);i=end+1;continue
            buf+=text[i];i+=1
        if buf:parts.append(buf)
        return InterpolatedString(parts,span=tok.span)

def parse_source(source,source_name='<input>'):
    from .type_system import erase_types
    return Parser(Lexer(erase_types(source),source_name).tokens(),source_name).parse()


