


"""PeaLang 0.27 deterministic package ecosystem."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib,json,re,shutil,tarfile,tempfile,tomllib
from .errors import PeaError

@dataclass(frozen=True,order=True)
class Version:
 major:int;minor:int;patch:int
 @classmethod
 def parse(cls,text):
  m=re.fullmatch(r'(\d+)\.(\d+)\.(\d+)',str(text).strip())
  if not m:raise PeaError(f'Invalid semantic version: {text}')
  return cls(*map(int,m.groups()))
 def __str__(self):return f'{self.major}.{self.minor}.{self.patch}'
def satisfies(version,constraint):
 v=Version.parse(version);c=str(constraint or '*').strip()
 if c in ('','*'):return True
 if c.startswith('^'):
  b=Version.parse(c[1:]);upper=Version(b.major+1,0,0) if b.major else Version(0,b.minor+1,0);return b<=v<upper
 if c.startswith('~'):
  b=Version.parse(c[1:]);return b<=v<Version(b.major,b.minor+1,0)
 if c.startswith('>='):return v>=Version.parse(c[2:])
 if c.startswith('<='):return v<=Version.parse(c[2:])
 if c.startswith('>'):return v>Version.parse(c[1:])
 if c.startswith('<'):return v<Version.parse(c[1:])
 return v==Version.parse(c.lstrip('='))
def sha256_file(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(65536),b''):h.update(block)
 return h.hexdigest()
def load_pea_toml(root='.'):
 p=Path(root).resolve();p=p if p.is_dir() else p.parent;f=p/'pea.toml'
 if not f.is_file():raise PeaError('pea.toml not found')
 data=tomllib.loads(f.read_text(encoding='utf-8'));proj=data.get('project',{})
 for k in ('name','version','entry'):
  if k not in proj:raise PeaError(f"pea.toml [project] requires '{k}'")
 Version.parse(proj['version']);return f,data
def init_manifest(root='.',name=None):
 root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True);p=root/'pea.toml'
 if p.exists():raise PeaError('pea.toml already exists')
 n=name or root.name;p.write_text(f'[project]\nname = "{n}"\nversion = "0.1.0"\nentry = "src/main.pea"\npealang = ">=0.35.0"\n\n[dependencies]\n\n[permissions]\nallow = []\n',encoding='utf-8');(root/'src').mkdir(exist_ok=True);(root/'src/main.pea').write_text(f'print "Hello from {n}"\n');return p
def dependency_entries(data):return data.get('dependencies',{})
def resolve(root='.'):
 mf,data=load_pea_toml(root);resolved=[]
 for name,spec in sorted(dependency_entries(data).items()):
  spec={'path':spec} if isinstance(spec,str) else dict(spec)
  if 'path' in spec:
   p=(mf.parent/spec['path']).resolve();dm,dd=load_pea_toml(p);ver=dd['project']['version'];constraint=spec.get('version','*')
   if not satisfies(ver,constraint):raise PeaError(f'{name} {ver} does not satisfy {constraint}')
   resolved.append({'name':name,'version':ver,'source':'path','path':str(p.relative_to(mf.parent) if p.is_relative_to(mf.parent) else p),'manifest_sha256':sha256_file(dm),'permissions':dd.get('permissions',{}).get('allow',[])})
  elif 'git' in spec:
   resolved.append({'name':name,'version':spec.get('version','0.0.0'),'source':'git','git':spec['git'],'rev':spec.get('rev'),'permissions':spec.get('permissions',[])})
  elif 'registry' in spec:
   resolved.append({'name':name,'version':spec.get('version','0.0.0'),'source':'registry','registry':spec['registry'],'permissions':spec.get('permissions',[])})
  else:raise PeaError(f"Dependency '{name}' needs path, git, or registry")
 return {'lock_version':1,'pealang':'0.35.0','package':data['project'],'dependencies':resolved}
def write_lock(root='.'):
 mf,_=load_pea_toml(root);lock=resolve(mf.parent);p=mf.parent/'pea.lock';p.write_text(json.dumps(lock,indent=2,sort_keys=True)+'\n');return p,lock
def audit(root='.'):
 mf,data=load_pea_toml(root);issues=[];allowed=set(data.get('permissions',{}).get('allow',[]));lock_path=mf.parent/'pea.lock'
 if not lock_path.exists():issues.append('Lock file missing')
 else:
  lock=json.loads(lock_path.read_text())
  for dep in lock.get('dependencies',[]):
   for perm in dep.get('permissions',[]):
    if perm not in allowed:issues.append(f"Dependency {dep['name']} requests undeclared permission {perm}")
   if dep['source']=='path':
    dm=(mf.parent/dep['path']/'pea.toml').resolve()
    if not dm.exists() or sha256_file(dm)!=dep.get('manifest_sha256'):issues.append(f"Dependency {dep['name']} checksum changed")
 return issues
def build_package(root='.',output=None):
 mf,data=load_pea_toml(root);base=mf.parent;name=data['project']['name'];version=data['project']['version'];out=Path(output or base/f'{name}-{version}.peapkg').resolve()
 if not (base/'pea.lock').exists():write_lock(base)
 files=[]
 for p in sorted(base.rglob('*')):
  if p.is_file() and '.pea_modules' not in p.parts and p.suffix!='.peapkg' and p!=out and not any(x in p.parts for x in ('.git','.venv','__pycache__','build')):files.append(p)
 import io, gzip
 raw=io.BytesIO()
 with tarfile.open(fileobj=raw,mode='w',format=tarfile.PAX_FORMAT) as tf:
  for p in files:
   info=tf.gettarinfo(str(p),arcname=str(p.relative_to(base)));info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
   with open(p,'rb') as f:tf.addfile(info,f)
 with open(out,'wb') as target:
  with gzip.GzipFile(filename='',mode='wb',fileobj=target,mtime=0) as gz:gz.write(raw.getvalue())
 return out,sha256_file(out)
def install(root='.'):
 mf,_=load_pea_toml(root);lock_path=mf.parent/'pea.lock'
 if not lock_path.exists():lock_path,_=write_lock(mf.parent)
 lock=json.loads(lock_path.read_text());target=mf.parent/'.pea_modules';target.mkdir(exist_ok=True);installed=[]
 for dep in lock.get('dependencies',[]):
  dest=target/dep['name'];shutil.rmtree(dest,ignore_errors=True)
  if dep['source']=='path':shutil.copytree((mf.parent/dep['path']).resolve(),dest,ignore=shutil.ignore_patterns('.git','.venv','__pycache__','.pea_modules','*.peapkg'))
  else:(dest).mkdir();(dest/'REMOTE_SOURCE.json').write_text(json.dumps(dep,indent=2))
  installed.append(dep['name'])
 return installed



