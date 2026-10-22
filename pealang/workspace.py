
from __future__ import annotations
from pathlib import Path
from .parser import parse_source
from .ast_nodes import VarDecl,FunctionStmt,ExportStmt
from .errors import PeaError
class WorkspaceIndex:
    def __init__(self,root='.'):
        self.root=Path(root).resolve();self.symbols={};self.errors=[]
    def build(self):
        self.symbols={};self.errors=[]
        for f in sorted(self.root.rglob('*.pea')):
            try:
                p=parse_source(f.read_text(encoding='utf-8'),str(f))
                exports={x.name for x in p.statements if isinstance(x,ExportStmt)}
                for n in p.statements:
                    if isinstance(n,(VarDecl,FunctionStmt)):
                        self.symbols.setdefault(n.name,[]).append({'name':n.name,'kind':'function' if isinstance(n,FunctionStmt) else 'constant' if n.constant else 'variable','source':str(f),'line':n.span.line if n.span else 1,'col':n.span.col if n.span else 1,'exported':n.name in exports})
            except PeaError as e:self.errors.append({'source':str(f),'message':str(e)})
        return self
    def definition(self,name,exported_only=False):
        hits=self.symbols.get(str(name),[])
        if exported_only:hits=[x for x in hits if x['exported']]
        return hits[0] if hits else None
    def references(self,name):return list(self.symbols.get(str(name),[]))
