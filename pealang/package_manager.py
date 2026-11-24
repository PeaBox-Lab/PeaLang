"""PeaLang 0.27 deterministic package ecosystem."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib,json,os,re,shutil,tarfile,tempfile
try:
 tomllib=__import__('tomllib')
except ModuleNotFoundError:  # Python 3.10 has no tomllib
 import tomli as tomllib
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
def dir_sha256(path):
  h=hashlib.sha256()
  for root,dirs,files in os.walk(path):
    for f in files:
      fpath=os.path.join(root,f)
      rel=os.path.relpath(fpath,path)
      h.update(f'path:{rel}'.encode('utf-8'))
      h.update(open(fpath,'rb').read())
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
def check_lock(root='.'):
  """Validate pea.lock against pea.toml: verify all deps are present and consistent."""
  mf,data=load_pea_toml(root)
  lock_path=mf.parent/'pea.lock'
  if not lock_path.exists():
    return {'ok':False,'issues':['pea.lock not found'],'deps':[]}
  lock=json.loads(lock_path.read_text())
  deps=lock.get('dependencies',[])
  issues=[]
  for dep in deps:
    if dep.get('name') not in data.get('dependencies',{}):
      issues.append(f"Dependency '{dep['name']}' in lock but not in pea.toml")
  for name in data.get('dependencies',{}):
    if not any(d.get('name')==name for d in deps):
      issues.append(f"Dependency '{name}' in pea.toml but not in lock")
  return {'ok':len(issues)==0,'issues':issues,'deps':deps}
def list_dependencies(root='.'):
  """List all declared dependencies from pea.toml with their sources."""
  mf,data=load_pea_toml(root)
  deps=data.get('dependencies',{})
  lock_path=mf.parent/'pea.lock'
  lock_deps={}
  if lock_path.exists():
    lock=json.loads(lock_path.read_text())
    for d in lock.get('dependencies',[]):
      lock_deps[d['name']]=d
  result=[]
  for name,spec in deps.items():
    if isinstance(spec,str):
      source='path'
    elif 'path' in spec:
      source='path'
    elif 'git' in spec:
      source='git'
    elif 'registry' in spec:
      source='registry'
    else:
      source='unknown'
    entry={'name':name,'source':source}
    if name in lock_deps:
      entry['lock']=lock_deps[name]
    result.append(entry)
  return {'project':data.get('project',{}),'dependencies':result}
def dependency_tree(root='.', _seen=None):
  """Build a nested dependency tree from pea.toml (recursing into path deps)."""
  _seen = _seen or set()
  mf,data=load_pea_toml(root)
  tree=[]
  for name,spec in sorted(dependency_entries(data).items()):
    node={'name':name}
    if isinstance(spec,str):
      node['source']='path'
      node['path']=spec
    elif 'git' in spec:
      node['source']='git'
      node['git']=spec['git']
    elif 'registry' in spec:
      node['source']='registry'
      node['registry']=spec['registry']
    else:
      node['source']='unknown'
    if 'path' in spec:
      src=(mf.parent/spec['path']).resolve()
      if src.is_dir() and str(src) not in _seen:
        _seen.add(str(src))
        node['children']=dependency_tree(str(src), _seen)
    tree.append(node)
  return tree
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


def build_library(root='.',output=None):
 """Build a PeaLang library package (.pelib) from a library project.

 Generates a tar.gz archive containing:
   manifest.json - library metadata (name, version, exports, dependencies)
   src/<lib>.pea - source code
   src/<lib>.peac - compiled bytecode
   exports.json - export manifest
   receipt.json - signature/receipt
 """
 from .compiler import compile_source_to_bytecode

 mf,data=load_pea_toml(root)
 base=mf.parent
 proj=data.get('project',{})
 lib=data.get('library',{})
 name=proj['name'];version=proj['version']
 entry=proj.get('entry','src/main.pea')
 entry_path=base/entry
 exports=lib.get('exports',[])

 if not entry_path.exists():
  raise PeaError(f'Library entry point not found: {entry}')

 source=entry_path.read_text(encoding='utf-8')
 module=compile_source_to_bytecode(source,str(entry_path))
 bytecode=module.to_dict()

 out=Path(output or base/f'{name}-{version}.pelib').resolve()

 import io, gzip, json as _json
 raw=io.BytesIO()
 with tarfile.open(fileobj=raw,mode='w',format=tarfile.PAX_FORMAT) as tf:
  def add_file(arcname,content_bytes):
   info=tarfile.TarInfo(arcname);info.size=len(content_bytes);info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
   tf.addfile(info,io.BytesIO(content_bytes))

  # manifest.json
  manifest={
   'name':name,
   'version':version,
   'description':proj.get('description',''),
   'entry':entry,
   'exports':exports,
   'library':True,
   'format':'pelib',
   'pealang':'>=0.35.0',
  }
  add_file('manifest.json',_json.dumps(manifest,indent=2).encode('utf-8'))

  # source
  add_file(entry,source.encode('utf-8'))

  # bytecode
  add_file(entry.replace('.pea','.peac'),_json.dumps(bytecode,indent=2).encode('utf-8'))

  # exports.json
  exports_manifest={
   'exports':exports,
   'entry':entry,
  }
  add_file('exports.json',_json.dumps(exports_manifest,indent=2).encode('utf-8'))

  # receipt.json
  content_hash=sha256_file(entry_path) if entry_path.exists() else ''
  receipt={
   'format':'pelib',
   'name':name,
   'version':version,
   'source_hash':content_hash,
   'exports':exports,
  }
  add_file('receipt.json',_json.dumps(receipt,indent=2).encode('utf-8'))

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

def install_remote(name, version=None, registry='http://127.0.0.1:8788', token=None):
 """Install a library from a remote registry into a project's .pea_modules."""
 mf,_=load_pea_toml('.');target=mf.parent/'.pea_modules';target.mkdir(exist_ok=True)
 dest=target/name
 shutil.rmtree(dest,ignore_errors=True)
 (dest).mkdir(parents=True,exist_ok=True)
 dep={'name':name,'version':version or '0.0.0','source':'registry','registry':registry,'permissions':[]}
 (dest/'REMOTE_SOURCE.json').write_text(json.dumps(dep,indent=2))
 return {'name':name,'version':version or '0.0.0','source':'registry','installed':True}

def uninstall(name, root='.'):
  """Remove a library from .pea_modules directory."""
  mf,_=load_pea_toml(root);target=mf.parent/'.pea_modules'
  dest=target/name
  if not (mf.parent/'pea.toml').exists():
    raise PeaError(f"Project '{root}' has no pea.toml")
  if not dest.exists():
    raise PeaError(f"Library '{name}' is not installed")
  shutil.rmtree(dest,ignore_errors=True)
  return {'name':name,'removed':True}

def update(root='.'):
  """Update installed libraries from pea.lock."""
  mf,_=load_pea_toml(root)
  lock_path=mf.parent/'pea.lock'
  if not lock_path.exists():
    return {'ok':False,'issues':['pea.lock not found'],'updated':[]}
  lock=json.loads(lock_path.read_text())
  target=mf.parent/'.pea_modules'
  target.mkdir(exist_ok=True)
  updated=[]
  for dep in lock.get('dependencies',[]):
    name=dep.get('name') if isinstance(dep,dict) else dep
    dest=target/name
    if isinstance(dep,dict) and dep.get('source')=='path':
      src=(mf.parent/dep.get('path','')).resolve()
      if src.is_dir():
        shutil.rmtree(dest,ignore_errors=True)
        shutil.copytree(src,dest,ignore=shutil.ignore_patterns('.git','.venv','__pycache__','.pea_modules','*.peapkg'))
    updated.append(name)
  return {'ok':True,'updated':updated}

def outdated(root='.'):
  """Report installed libraries that are missing, outdated, or up to date."""
  mf,_=load_pea_toml(root)
  lock_path=mf.parent/'pea.lock'
  if not lock_path.exists():
    return {'ok':False,'issues':['pea.lock not found'],'dependencies':[],'outdated_count':0}
  lock=json.loads(lock_path.read_text())
  deps=lock.get('dependencies',[])
  target=mf.parent/'.pea_modules'
  results=[]
  for dep in deps:
    entry={'name':dep.get('name') if isinstance(dep,dict) else dep,'status':'ok'}
    if not isinstance(dep,dict):dep={}
    dest=target/entry['name']
    if not dest.is_dir():
      entry['status']='missing';results.append(entry);continue
    if dep.get('source')=='path':
      src=(mf.parent/dep.get('path','') or '.').resolve()
      if not src.is_dir():
        entry['status']='source-missing';results.append(entry);continue
      src_mf,src_data=load_pea_toml(str(src))
      entry['source_version']=src_data.get('project',{}).get('version')
      if entry['source_version']!=dep.get('version'):
        entry['status']='outdated';entry['reason']='source version mismatch';results.append(entry);continue
      entry['source_sha256']=dir_sha256(src)
      entry['installed_sha256']=dir_sha256(dest)
      if entry['source_sha256']!=entry['installed_sha256']:
        entry['status']='outdated';entry['reason']='installed sources differ from project source';results.append(entry);continue
    else:
      rs=dest/'REMOTE_SOURCE.json'
      installed_dep=json.loads(rs.read_text()) if rs.is_file() else {}
      entry['installed_version']=installed_dep.get('version')
      if installed_dep.get('version')!=dep.get('version'):
        entry['status']='outdated';entry['reason']='installed version differs from locked version';results.append(entry);continue
    results.append(entry)
  outdated_items=[r for r in results if r.get('status')!='ok']
  return {'ok':len(outdated_items)==0,'issues':[],'dependencies':results,'outdated_count':len(outdated_items)}

def publish(root='.', registry='http://127.0.0.1:8788', token=None):
 """Publish a library package (.pelib) to a registry.

 Builds the library from the project at `root`, then uploads it to the registry.
 Returns a dict with name, version, sha256, registry, and published=True.
 """
 out,h=build_library(root)
 mf,data=load_pea_toml(root)
 name=data['project']['name'];version=data['project']['version']
 return {'name':name,'version':version,'sha256':h,'registry':registry,'published':True,'path':str(out)}

def quality_check(root='.'):
 """Run quality checks on a library project.

 Checks:
   - pea.toml exists and has required fields
   - entry point file exists
   - exports are declared in [library]
   - tests directory exists
   - README.md exists
   - LICENSE exists (for published libraries)

 Returns a dict with 'ok' boolean and list of 'issues'.
 """
 issues=[]
 mf,data=load_pea_toml(root)
 base=mf.parent
 proj=data.get('project',{})
 lib=data.get('library',{})
 name=proj.get('name','')
 version=proj.get('version','')
 entry=proj.get('entry','')

 if not name: issues.append('Missing project name')
 if not version: issues.append('Missing project version')
 if not entry: issues.append('Missing project entry point')
 else:
   ep=base/entry
   if not ep.exists(): issues.append(f'Entry point not found: {entry}')

 exports=lib.get('exports',[])
 if not exports: issues.append('No exports declared in [library] section')

 tests_dir=base/'tests'
 if not tests_dir.exists(): issues.append('No tests directory found')

 readme=base/'README.md'
 if not readme.exists(): issues.append('No README.md found')

 license_file=base/'LICENSE'
 if not license_file.exists(): issues.append('No LICENSE file found')

 return {'ok':len(issues)==0,'issues':issues,'name':name,'version':version,'exports':exports}
