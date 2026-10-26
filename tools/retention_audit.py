
import argparse,fnmatch,hashlib,json,re,zipfile
from pathlib import Path
R=re.compile(r"^PeaLang_v[^/]+/")
IGN=("build/**","dist/**","*.egg-info/**","**/__pycache__/**","*.pyc",".pytest_cache/**")
def norm(n):return R.sub("",n.replace("\\","/")).rstrip("/")
def load_zip(path):
 o={}
 with zipfile.ZipFile(path) as z:
  for i in z.infolist():
   q=norm(i.filename)
   if not q or i.is_dir() or any(fnmatch.fnmatch(q,g) for g in IGN):continue
   o[q]=hashlib.sha256(z.read(i)).hexdigest()
 return o
def compare(a,b,approved=()):
 a,b=load_zip(a),load_zip(b);approved=set(approved);same=sorted(k for k in a.keys()&b if a[k]==b[k]);mod=sorted(k for k in a.keys()&b if a[k]!=b[k]);add=sorted(b.keys()-a.keys());rem=sorted(a.keys()-b.keys());bad=sorted(set(rem)-approved);return {"unchanged":same,"modified":mod,"added":add,"removed":rem,"unapproved_removed":bad,"passed":not bad}

