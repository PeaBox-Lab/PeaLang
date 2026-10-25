
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from .errors import SourceSpan

@dataclass
class Node: span: Optional[SourceSpan] = field(default=None, kw_only=True)
@dataclass
class Program(Node): statements: list['Stmt'] = field(default_factory=list)
class Stmt(Node): pass
class Expr(Node): pass
@dataclass
class VarDecl(Stmt): name:str=''; value:Optional[Expr]=None; constant:bool=False
@dataclass
class Assign(Stmt): target:Optional[Expr]=None; op:str='='; value:Optional[Expr]=None
@dataclass
class PrintStmt(Stmt): value:Optional[Expr]=None
@dataclass
class ExprStmt(Stmt): value:Optional[Expr]=None
@dataclass
class IfStmt(Stmt): condition:Optional[Expr]=None; then_body:list[Stmt]=field(default_factory=list); else_body:Optional[list[Stmt]]=None
@dataclass
class WhileStmt(Stmt): condition:Optional[Expr]=None; body:list[Stmt]=field(default_factory=list)
@dataclass
class ForStmt(Stmt): name:str=''; iterable:Optional[Expr]=None; body:list[Stmt]=field(default_factory=list)
@dataclass
class FunctionStmt(Stmt): name:str=''; params:list[Any]=field(default_factory=list); body:list[Stmt]=field(default_factory=list)
@dataclass
class ReturnStmt(Stmt): value:Optional[Expr]=None
@dataclass
class BreakStmt(Stmt): pass
@dataclass
class ContinueStmt(Stmt): pass
@dataclass
class ImportStmt(Stmt): path:str=''; alias:Optional[str]=None
@dataclass
class Literal(Expr): value:Any=None
@dataclass
class Variable(Expr): name:str=''
@dataclass
class ListExpr(Expr): items:list[Expr]=field(default_factory=list)
@dataclass
class DictExpr(Expr): pairs:list[tuple[Expr,Expr]]=field(default_factory=list)
@dataclass
class Unary(Expr): op:str=''; value:Optional[Expr]=None
@dataclass
class Binary(Expr): op:str=''; left:Optional[Expr]=None; right:Optional[Expr]=None
@dataclass
class Index(Expr): target:Optional[Expr]=None; index:Optional[Expr]=None
@dataclass
class Property(Expr): target:Optional[Expr]=None; name:str=''
@dataclass
class Call(Expr): callee:Optional[Expr]=None; args:list[Expr]=field(default_factory=list)
@dataclass
class InterpolatedString(Expr): parts:list[Any]=field(default_factory=list)

@dataclass
class AssertStmt(Stmt): condition:Optional[Expr]=None; message:Optional[Expr]=None
@dataclass
class ParallelExpr(Expr): expressions:list[Expr]=field(default_factory=list)

@dataclass
class TryStmt(Stmt):
    try_body:list[Stmt]=field(default_factory=list); catch_name:Optional[str]=None; catch_body:Optional[list[Stmt]]=None; finally_body:Optional[list[Stmt]]=None
@dataclass
class ThrowStmt(Stmt): value:Optional[Expr]=None
@dataclass
class Param(Node): name:str=''; default:Optional[Expr]=None

@dataclass
class ExportStmt(Stmt): name:str=''

@dataclass
class AwaitExpr(Expr): value:Optional[Expr]=None

