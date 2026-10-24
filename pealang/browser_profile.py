"""Browser-safe capability and UI-schema validation profile."""
from __future__ import annotations
from .errors import PeaError
BROWSER_SAFE_CAPABILITIES=frozenset({'console','storage.read','storage.write','http.fetch'})
def validate_browser_permissions(permissions):
 bad=sorted(set(permissions)-BROWSER_SAFE_CAPABILITIES)
 if bad:raise PeaError('Browser-unsafe capabilities: '+', '.join(bad))
 return True
def validate_ui_schema(node,depth=0):
 if depth>32:raise PeaError('UI schema depth exceeds 32')
 if not isinstance(node,dict) or node.get('type') not in ('text','button','stack'):raise PeaError('Invalid UI node')
 allowed={'type','text','action','children'}
 extra=set(node)-allowed
 if extra:raise PeaError('Unknown UI fields: '+', '.join(sorted(extra)))
 if node['type']=='stack':
  children=node.get('children',[])
  if not isinstance(children,list) or len(children)>100:raise PeaError('Invalid UI children')
  for child in children:validate_ui_schema(child,depth+1)
 return node

