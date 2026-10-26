
"""PeaLang 0.99.4 security closure checks."""
from pathlib import Path
import ast,re
SECRET_PATTERNS=(re.compile(r"AKIA[0-9A-Z]{16}"),re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"))
FORBIDDEN_CALLS={("os","system"),("tempfile","mktemp")}
def audit_python_tree(root):
 root=Path(root); findings=[]
 for path in (root/"pealang").rglob("*.py"):
  text=path.read_text(errors="replace")
  for pat in SECRET_PATTERNS:
   if pat.search(text): findings.append({"kind":"embedded-secret","path":str(path.relative_to(root))})
  try: tree=ast.parse(text,filename=str(path))
  except SyntaxError as e: findings.append({"kind":"syntax-error","path":str(path.relative_to(root)),"line":e.lineno}); continue
  for n in ast.walk(tree):
   if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name):
    key=(n.func.value.id,n.func.attr)
    if key in FORBIDDEN_CALLS: findings.append({"kind":"forbidden-call","call":".".join(key),"path":str(path.relative_to(root)),"line":n.lineno})
   if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {"eval","exec"}: findings.append({"kind":"python-dynamic-exec","call":n.func.id,"path":str(path.relative_to(root)),"line":n.lineno})
   if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in {"md5","sha1"}: findings.append({"kind":"weak-hash","call":n.func.attr,"path":str(path.relative_to(root)),"line":n.lineno})
 return {"passed":not findings,"findings":findings}

