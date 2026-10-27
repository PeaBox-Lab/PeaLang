from pathlib import Path
import hashlib,json
def sha256(path):
 h=hashlib.sha256();h.update(Path(path).read_bytes());return h.hexdigest()
def inventory(root):
 root=Path(root);skip={'__pycache__','.pytest_cache','build','.git'};out={}
 for p in sorted(root.rglob('*')):
  if p.is_file() and not any(x in p.parts for x in skip) and '.egg-info' not in str(p):out[str(p.relative_to(root))]={'bytes':p.stat().st_size,'sha256':sha256(p)}
 return out
def compare(previous,current):
 a,b=inventory(previous),inventory(current);return {'previous_files':len(a),'current_files':len(b),'added':sorted(set(b)-set(a)),'removed':sorted(set(a)-set(b)),'modified':sorted(k for k in set(a)&set(b) if a[k]['sha256']!=b[k]['sha256'])}
