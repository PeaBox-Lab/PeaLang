from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .errors import PeaError, SourceSpan

@dataclass(frozen=True)
class Token:
    kind:str; value:Any; line:int; col:int
    @property
    def span(self): return SourceSpan(self.line,self.col)

KEYWORDS={"let","const","print","if","else","while","for","in","function","return","true","false","null","and","or","not","break","continue","import","assert","parallel","try","catch","finally","throw"}

class Lexer:
    def __init__(self,text:str,source_name='<input>'):
        self.text=text; self.source_name=source_name; self.i=0; self.line=1; self.col=1
    def peek(self,n=0):
        j=self.i+n; return self.text[j] if j<len(self.text) else '\0'
    def advance(self):
        c=self.peek(); self.i+=1
        if c=='\n': self.line+=1; self.col=1
        else:self.col+=1
        return c
    def error(self,msg,line,col): raise PeaError(msg,SourceSpan(line,col),self.source_name)
    def tokens(self):
        out=[]; two={"==","!=","<=",">=","+=","-=","*=","/="}; singles=set("+-*/%(){}[],.:;<>!=")
        while self.i<len(self.text):
            c=self.peek()
            if c in ' \t\r':self.advance();continue
            if c=='\n':out.append(Token('NEWLINE','\n',self.line,self.col));self.advance();continue
            if c=='#' or (c=='/' and self.peek(1)=='/'):
                while self.peek() not in ('\n','\0'):self.advance()
                continue
            line,col=self.line,self.col
            if c in ('"',"'"):
                q=self.advance();s=''
                while self.peek()!=q:
                    if self.peek()=='\0':self.error('Unterminated string',line,col)
                    if self.peek()=='\\':
                        self.advance();esc=self.advance();s += {'n':'\n','t':'\t','r':'\r','"':'"',"'":"'",'\\':'\\'}.get(esc,esc)
                    else:s+=self.advance()
                self.advance();out.append(Token('STRING',s,line,col));continue
            if c.isdigit():
                s=''
                while self.peek().isdigit():s+=self.advance()
                if self.peek()=='.' and self.peek(1).isdigit():
                    s+=self.advance()
                    while self.peek().isdigit():s+=self.advance()
                out.append(Token('NUMBER',float(s) if '.' in s else int(s),line,col));continue
            if c.isalpha() or c=='_':
                s=''
                while self.peek().isalnum() or self.peek()=='_':s+=self.advance()
                out.append(Token(s.upper() if s in KEYWORDS else 'IDENT',s,line,col));continue
            op=c+self.peek(1)
            if op in two:self.advance();self.advance();out.append(Token(op,op,line,col));continue
            if c in singles:self.advance();out.append(Token(c,c,line,col));continue
            self.error(f'Unexpected character {c!r}',line,col)
        out.append(Token('EOF',None,self.line,self.col));return out
