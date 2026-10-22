
from .parser import parse_source
from .ast_nodes import VarDecl,FunctionStmt
from .errors import PeaError
KEYWORDS=['let','const','function','return','if','else','while','for','import','export','try','catch','throw','parallel','assert']
def diagnostics(source,source_name='<input>'):
 try:parse_source(source,source_name);return []
 except PeaError as e:return [{'severity':'error','message':e.message,'line':e.span.line if e.span else 1,'col':e.span.col if e.span else 1}]
def symbols(source,source_name='<input>'):
 p=parse_source(source,source_name);o=[]
 for n in p.statements:
  if isinstance(n,(VarDecl,FunctionStmt)):o.append({'name':n.name,'kind':'function' if isinstance(n,FunctionStmt) else 'variable','source':source_name,'line':n.span.line if n.span else 1,'col':n.span.col if n.span else 1})
 return o
def definition(source,name,source_name='<input>'):return next((x for x in symbols(source,source_name) if x['name']==name),None)
def completions(source='',prefix=''):
 try:names=KEYWORDS+[x['name'] for x in symbols(source)]
 except PeaError:names=KEYWORDS
 return sorted(set(x for x in names if x.startswith(prefix)))
