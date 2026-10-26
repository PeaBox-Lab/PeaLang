



from difflib import get_close_matches
from .errors import PeaError, SourceSpan
class Env:
    def __init__(self,parent=None):self.parent=parent;self.values={};self.const=set()
    def define(self,n,v,const=False):
        if n in self.values:raise PeaError(f"Variable '{n}' is already defined")
        self.values[n]=v
        if const:self.const.add(n)
    def names(self):return set(self.values)|(self.parent.names() if self.parent else set())
    def get(self,n,span=None,source_name='<input>'):
        if n in self.values:return self.values[n]
        if self.parent:return self.parent.get(n,span,source_name)
        hint=get_close_matches(n,self.names(),n=1,cutoff=.6)
        suffix=f". Did you mean '{hint[0]}'?" if hint else ''
        raise PeaError(f"Undefined variable '{n}'{suffix}",span,source_name)
    def set(self,n,v,span=None,source_name='<input>'):
        if n in self.values:
            if n in self.const:raise PeaError(f"Cannot assign to constant '{n}'",span,source_name)
            self.values[n]=v;return v
        if self.parent:return self.parent.set(n,v,span,source_name)
        raise PeaError(f"Undefined variable '{n}'",span,source_name)

    def snapshot(self):return dict(self.values)




