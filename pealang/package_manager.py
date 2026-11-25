"""PeaLang 0.27 deterministic package ecosystem."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib,json,os,re,shutil,tarfile,tempfile,time,urllib.request,urllib.error
try:
 tomllib=__import__('tomllib')
except ModuleNotFoundError:  # Python 3.10 has no tomllib
 import tomli as tomllib
from .errors import PeaError

DEFAULT_REGISTRY='http://127.0.0.1:8788'

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
def registry_cache_dir():
  """Directory used for registry metadata and offline resolution."""
  return Path.home()/'.pealang'/'registry_cache'
def registry_cache_path(name,registry=DEFAULT_REGISTRY):
  key=re.sub(r'[^A-Za-z0-9_.-]','_',f'{registry}::{name}')
  return registry_cache_dir()/f'{key}.json'
def fetch_registry_versions(name,registry=DEFAULT_REGISTRY,token=None,offline=False,timeout=5):
  """Fetch and cache available versions of a registry package."""
  path=registry_cache_path(name,registry)
  if offline:
   if not path.is_file():raise PeaError(f'No cached registry metadata for {name} at {registry}')
   cached=json.loads(path.read_text(encoding='utf-8'))
   versions=cached.get('versions',[])
   return {'name':name,'registry':registry,'versions':versions,'cached':True,'offline':True}
  request=urllib.request.Request(f'{registry.rstrip("/")}/api/v1/packages/{name}')
  if token:request.add_header('Authorization',f'Bearer {token}')
  try:
   with urllib.request.urlopen(request,timeout=timeout) as response:
    info=json.loads(response.read().decode('utf-8'))
  except urllib.error.HTTPError as e:
   if e.code==404:raise PeaError(f'Package {name} not found on registry {registry}')
   raise PeaError(f'Registry request failed for {name}: HTTP {e.code}')
  except (urllib.error.URLError,OSError,ValueError) as e:
   raise PeaError(f'Registry request failed for {name}: {e}')
  versions=[]
  for item in info.get('versions',[]):
   version=str(item.get('version',''))
   Version.parse(version)
   versions.append({
    'version':version,
    'sha256':item.get('sha256',''),
    'published':item.get('published'),
    'url':item.get('url',''),
    'signature_url':item.get('signature_url',''),
    'signature_key_id':item.get('signature_key_id') or item.get('publisher_key_id',''),
   })
  versions.sort(key=lambda item:Version.parse(item['version']),reverse=True)
  result={'name':name,'registry':registry,'versions':versions,'cached':False,'offline':False,'fetched_at':int(time.time())}
  path.parent.mkdir(parents=True,exist_ok=True)
  path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
  return result
def select_registry_version(versions,constraint='*'):
  """Select the highest available version satisfying a semver constraint."""
  candidates=[]
  for item in versions:
   version=str(item.get('version','') if isinstance(item,dict) else item)
   try:
    if satisfies(version,constraint):candidates.append((Version.parse(version),item))
   except PeaError:
    continue
  if not candidates:
   available=', '.join(str(item.get('version',item)) for item in versions)
   raise PeaError(f'No registry version of package satisfies {constraint!r}; available: {available or "none"}')
  candidates.sort(key=lambda pair:pair[0],reverse=True)
  return candidates[0][1]
def resolve_registry_dependency(name,spec,registry=None,token=None,offline=False):
  """Resolve one registry dependency to a concrete version and checksum."""
  registry=spec.get('registry') or registry or DEFAULT_REGISTRY
  constraint=spec.get('version') or spec.get('constraint') or '*'
  info=fetch_registry_versions(name,registry,token=token,offline=offline)
  selected=select_registry_version(info['versions'],constraint)
  return {
   'name':name,
   'version':selected.get('version',constraint),
   'source':'registry',
   'registry':registry,
   'sha256':selected.get('sha256',''),
   'url':selected.get('url',''),
   'signature_url':selected.get('signature_url',''),
   'published':selected.get('published'),
   'permissions':spec.get('permissions',[]),
   'resolved_by':'registry',
   'offline':offline,
  }
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
def resolve(root='.',*,registry_resolve=False,offline=False,registry=None,token=None):
 mf,data=load_pea_toml(root);resolved=[]
 for name,spec in sorted(dependency_entries(data).items()):
  spec={'path':spec} if isinstance(spec,str) else dict(spec)
  if 'path' in spec:
   p=(mf.parent/spec['path']).resolve();dm,dd=load_pea_toml(p);ver=dd['project']['version'];constraint=spec.get('version','*')
   if not satisfies(ver,constraint):raise PeaError(f'{name} {ver} does not satisfy {constraint}')
   resolved.append({'name':name,'version':ver,'source':'path','path':str(p.relative_to(mf.parent) if p.is_relative_to(mf.parent) else p),'manifest_sha256':sha256_file(dm),'permissions':dd.get('permissions',{}).get('allow',[])})
  elif spec.get('workspace'):
   from .workspace import load_workspace
   target=None
   for candidate in load_workspace(mf.parent)['members']:
    try:
     _,candidate_data=load_pea_toml(candidate)
    except PeaError:
     continue
    if candidate_data.get('project',{}).get('name')==name:
     target=candidate;break
   if target is None:raise PeaError(f'Workspace member {name} not found')
   dm,dd=load_pea_toml(target);ver=dd['project']['version'];constraint=spec.get('version','*')
   if not satisfies(ver,constraint):raise PeaError(f'{name} {ver} does not satisfy {constraint}')
   resolved.append({'name':name,'version':ver,'source':'path','path':str(target.relative_to(mf.parent) if target.is_relative_to(mf.parent) else target),'workspace':True,'manifest_sha256':sha256_file(dm),'permissions':dd.get('permissions',{}).get('allow',[])})
  elif 'git' in spec:
   resolved.append({'name':name,'version':spec.get('version','0.0.0'),'source':'git','git':spec['git'],'rev':spec.get('rev'),'permissions':spec.get('permissions',[])})
  elif 'registry' in spec:
   if registry_resolve:
    resolved.append(resolve_registry_dependency(name,spec,registry=registry,token=token,offline=offline))
   else:
    resolved.append({'name':name,'version':spec.get('version','0.0.0'),'source':'registry','registry':spec['registry'],'permissions':spec.get('permissions',[])})
  else:raise PeaError(f"Dependency '{name}' needs path, git, or registry")
 return {'lock_version':1,'pealang':'0.35.0','package':data['project'],'dependencies':resolved}
def write_lock(root='.',*,registry_resolve=False,offline=False,registry=None,token=None):
 mf,_=load_pea_toml(root);lock=resolve(mf.parent,registry_resolve=registry_resolve,offline=offline,registry=registry,token=token);p=mf.parent/'pea.lock';p.write_text(json.dumps(lock,indent=2,sort_keys=True)+'\n');return p,lock
def lock_drift(root='.',*,offline=False,registry=None,token=None):
  """Report detailed drift between pea.toml and pea.lock."""
  mf,data=load_pea_toml(root)
  lock_path=mf.parent/'pea.lock'
  if not lock_path.exists():
    return {'ok':False,'issues':['pea.lock not found'],'deps':[],'changes':[],'sha256':''}
  lock=json.loads(lock_path.read_text(encoding='utf-8'))
  deps=lock.get('dependencies',[])
  try:
   registry_resolved=any(isinstance(d,dict) and d.get('resolved_by')=='registry' for d in deps)
   expected=resolve(mf.parent,registry_resolve=registry_resolved,offline=offline or registry_resolved,registry=registry,token=token)
  except PeaError as e:
   return {'ok':False,'issues':[f'Cannot resolve lock: {e}'],'deps':deps,'changes':[],'sha256':sha256_file(lock_path)}
  issues=[];changes=[]
  old_pkg=lock.get('package',{});new_pkg=expected.get('package',{})
  for key in ('name','version','entry'):
   if old_pkg.get(key)!=new_pkg.get(key):
    change={'field':f'project.{key}','expected':new_pkg.get(key),'actual':old_pkg.get(key)}
    changes.append(change);issues.append(f"Project {key} drift: lock={old_pkg.get(key)!r}, manifest={new_pkg.get(key)!r}")
  old_deps={d.get('name'):d for d in deps if d.get('name')}
  new_deps={d.get('name'):d for d in expected.get('dependencies',[]) if d.get('name')}
  for name in sorted(set(old_deps)-set(new_deps)):
   issues.append(f"Dependency '{name}' in lock but not in pea.toml")
  for name in sorted(set(new_deps)-set(old_deps)):
   issues.append(f"Dependency '{name}' in pea.toml but not in lock")
  for name in sorted(set(old_deps)&set(new_deps)):
   for key in ('version','source','path','git','rev','registry','manifest_sha256','sha256','url','signature_url','permissions','resolved_by'):
    old_value=old_deps[name].get(key);new_value=new_deps[name].get(key)
    if old_value!=new_value:
     change={'field':f'{name}.{key}','expected':new_value,'actual':old_value}
     changes.append(change);issues.append(f"Dependency '{name}' drift in {key}: lock={old_value!r}, manifest={new_value!r}")
  return {'ok':not issues,'issues':issues,'deps':deps,'changes':changes,'sha256':sha256_file(lock_path)}
def check_lock(root='.',*,offline=False,registry=None,token=None):
  """Validate pea.lock against pea.toml: verify all deps are present and consistent."""
  report=lock_drift(root,offline=offline,registry=registry,token=token)
  return {'ok':report['ok'],'issues':report['issues'],'deps':report['deps']}
def refresh_lock(root='.',*,registry_resolve=False,offline=False,registry=None,token=None):
  """Rebuild pea.lock from pea.toml and return a deterministic report."""
  path,lock=write_lock(root,registry_resolve=registry_resolve,offline=offline,registry=registry,token=token)
  return {'ok':True,'updated':True,'lock':str(path),'sha256':sha256_file(path),'dependencies':lock.get('dependencies',[])}
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
def dependency_graph(root='.'):
  """Analyze the dependency graph for cycles, duplicates, and version conflicts."""
  cycles=[];occurrences={};versions={};seen=set();stack_paths=[];stack_names=[]
  def spec_dict(spec):
   return {'path':spec} if isinstance(spec,str) else dict(spec)
  def walk(path):
   mf,data=load_pea_toml(path)
   nodes=[]
   for name,raw_spec in sorted(dependency_entries(data).items()):
    spec=spec_dict(raw_spec)
    node={'name':name}
    version=spec.get('version') or spec.get('rev') or '*'
    if 'path' in spec:
     src=(mf.parent/spec['path']).resolve()
     node['source']='path';node['path']=spec['path']
     try:
      _,dep_data=load_pea_toml(src)
      version=dep_data.get('project',{}).get('version',version)
     except PeaError:
      pass
     node['version']=version
     if src.is_dir():
      if str(src) in stack_paths:
       idx=stack_paths.index(str(src))
       cycle_names=stack_names[idx:]+[name]
       node['cycle']=True;node['cycle_path']=cycle_names
       cycles.append({'name':name,'path':str(src),'cycle':cycle_names})
      elif str(src) not in seen:
       seen.add(str(src));stack_paths.append(str(src));stack_names.append(name)
       node['children']=walk(str(src))
       stack_paths.pop();stack_names.pop()
    elif 'git' in spec:
     node['source']='git';node['git']=spec['git'];node['version']=version
    elif 'registry' in spec:
     node['source']='registry';node['registry']=spec['registry'];node['version']=version
    else:
     node['source']='unknown';node['version']=version
    occurrences[name]=occurrences.get(name,0)+1
    versions.setdefault(name,set()).add(str(version))
    nodes.append(node)
   return nodes
  tree=walk(root)
  conflicts=[{'name':name,'versions':sorted(found)} for name,found in sorted(versions.items()) if len(found)>1]
  duplicates=[{'name':name,'count':count} for name,count in sorted(occurrences.items()) if count>1]
  return {'ok':not cycles and not conflicts,'tree':tree,'cycles':cycles,'conflicts':conflicts,'duplicates':duplicates}
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
   provenance.json - deterministic build evidence
 """
 from .compiler import compile_source_to_bytecode
 from . import __version__ as _pealang_version

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
 entries={}
 with tarfile.open(fileobj=raw,mode='w',format=tarfile.PAX_FORMAT) as tf:
  def add_file(arcname,content_bytes):entries[arcname]=content_bytes

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
  manifest_bytes=_json.dumps(manifest,indent=2).encode('utf-8')
  add_file('manifest.json',manifest_bytes)

  # source
  source_bytes=source.encode('utf-8')
  add_file(entry,source_bytes)

  # bytecode
  bytecode_bytes=_json.dumps(bytecode,indent=2).encode('utf-8')
  add_file(entry.replace('.pea','.peac'),bytecode_bytes)

  # exports.json
  exports_manifest={
   'exports':exports,
   'entry':entry,
  }
  exports_bytes=_json.dumps(exports_manifest,indent=2).encode('utf-8')
  add_file('exports.json',exports_bytes)

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

  # provenance.json - deterministic build evidence
  lock_path=base/'pea.lock'
  lock_hash=sha256_file(lock_path) if lock_path.is_file() else ''
  dependencies=[]
  if lock_hash:
   lock_data=_json.loads(lock_path.read_text(encoding='utf-8'))
   dependencies=[{'name':d.get('name'),'version':d.get('version'),'source':d.get('source')} for d in lock_data.get('dependencies',[])]
  provenance={
   'format':'pelib-provenance-v1',
   'name':name,
   'version':version,
   'source_sha256':hashlib.sha256(source_bytes).hexdigest(),
   'bytecode_sha256':hashlib.sha256(bytecode_bytes).hexdigest(),
   'manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),
   'exports_sha256':hashlib.sha256(exports_bytes).hexdigest(),
   'lock_sha256':lock_hash,
   'dependencies':dependencies,
   'builder':'pealang',
   'builder_version':_pealang_version,
   'deterministic':True,
   'normalization':{'tar_mtime':0,'tar_uid':0,'tar_gid':0,'gzip_mtime':0,'entry_order':'sorted'},
  }
  add_file('provenance.json',_json.dumps(provenance,indent=2,sort_keys=True).encode('utf-8'))

  for arcname in sorted(entries):
   content_bytes=entries[arcname]
   info=tarfile.TarInfo(arcname);info.size=len(content_bytes);info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
   tf.addfile(info,io.BytesIO(content_bytes))

 with open(out,'wb') as target:
  with gzip.GzipFile(filename='',mode='wb',fileobj=target,mtime=0) as gz:gz.write(raw.getvalue())

 return out,sha256_file(out)
def reproducible_build_check(root='.',runs=2):
  """Build the same library repeatedly and verify byte-identical output."""
  if runs<2:raise PeaError('Reproducible build check requires at least two runs')
  hashes=[]
  with tempfile.TemporaryDirectory() as td:
   for index in range(runs):
    out=Path(td)/f'build-{index}.pelib'
    _,digest=build_library(root,str(out))
    hashes.append(digest)
  return {'ok':len(set(hashes))==1,'runs':runs,'hashes':hashes,'sha256':hashes[0] if hashes else ''}
def sign_library(root='.',private_key=None,publisher=None,output=None,trust_store=None):
  """Build a library and create a detached Ed25519 publisher signature."""
  if not private_key:raise PeaError('Signing requires a private key path')
  from .ed25519_signing import PublicTrustStore,default_trust_store_path,sign_ed25519
  out,h=build_library(root,output)
  signature,envelope=sign_ed25519(str(out),private_key,publisher=publisher)
  report={'path':str(out),'sha256':h,'signature':str(signature),'key_id':envelope.key_id,'publisher':publisher,'signed':True,'trusted_key':None}
  public_key=Path(str(private_key)+'.pub')
  if public_key.is_file():
   store=PublicTrustStore(trust_store or default_trust_store_path())
   if envelope.key_id not in store.data.get('keys',{}):
    store.trust(str(public_key),label=publisher or envelope.key_id)
   report['trusted_key']=envelope.key_id
  return report
def inspect_library(package):
 """Inspect a built .pelib package without installing it."""
 p=Path(package).resolve()
 if not p.is_file():raise PeaError(f'Library package not found: {package}')
 with tarfile.open(p,'r:gz') as tf:
  names=tf.getnames()
  def read_json(name,default=None):
   if name not in names:return default
   member=tf.extractfile(name)
   return json.loads(member.read().decode('utf-8')) if member else default
  manifest=read_json('manifest.json')
  exports=read_json('exports.json',{}).get('exports',[]) or []
  receipt=read_json('receipt.json')
  provenance=read_json('provenance.json')
 if not isinstance(manifest,dict) or not manifest.get('name'):
  raise PeaError(f'Invalid library package: {package}')
 return {
  'ok':True,
  'package':p.name,
  'sha256':sha256_file(p),
  'name':manifest['name'],
  'version':manifest.get('version',''),
  'description':manifest.get('description',''),
  'format':manifest.get('format','pelib'),
  'entry':manifest.get('entry',''),
  'exports':exports,
  'receipt':receipt,
  'provenance':provenance,
  'files':names,
 }
def verify_library_provenance(package):
  """Verify deterministic build evidence embedded in a .pelib package."""
  info=inspect_library(package)
  provenance=info.get('provenance')
  if not isinstance(provenance,dict):
   return {'ok':False,'issues':['provenance.json not found'],'package':info['package'],'sha256':info['sha256'],'checked':[],'provenance':None}
  entry=info.get('entry','')
  paths={'source_sha256':entry,'bytecode_sha256':entry.replace('.pea','.peac'),'manifest_sha256':'manifest.json','exports_sha256':'exports.json'}
  issues=[];checked=[]
  with tarfile.open(package,'r:gz') as tf:
   names=tf.getnames()
   for field,arcname in paths.items():
    expected=provenance.get(field)
    if not arcname or arcname not in names:
     issues.append(f'{field}: package member {arcname or "<missing>"} not found');continue
    member=tf.extractfile(arcname)
    actual=hashlib.sha256(member.read()).hexdigest() if member else ''
    checked.append({'field':field,'path':arcname,'sha256':actual})
    if expected and actual!=expected:issues.append(f'{field}: expected {expected}, got {actual}')
  if not provenance.get('deterministic'):issues.append('deterministic flag is not true')
  return {'ok':not issues,'issues':issues,'package':info['package'],'sha256':info['sha256'],'checked':checked,'provenance':provenance}
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

def install_remote(name, version=None, registry=DEFAULT_REGISTRY, token=None):
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

def clean(root='.', all=False):
  """Remove .pea_modules (and optionally pea.lock) from a project."""
  mf,_=load_pea_toml(root)
  base=mf.parent
  removed=[]
  mods=base/'.pea_modules'
  if mods.is_dir():
    shutil.rmtree(mods,ignore_errors=True)
    removed.append('.pea_modules')
  if all:
    lock=base/'pea.lock'
    if lock.is_file():
      lock.unlink()
      removed.append('pea.lock')
  return {'ok':True,'removed':removed}

def install_remote_verified(name,version=None,registry=DEFAULT_REGISTRY,token=None,*,public_key=None,key_id=None,trust_store=None,root='.'):
  """Download, verify, and install a signed library from a registry."""
  from .ed25519_signing import PublicTrustStore,default_trust_store_path,public_key_bytes,public_key_id,verify_ed25519
  from .secure_packages import safe_extract,write_receipt
  mf,_=load_pea_toml(root);base=mf.parent;target=base/'.pea_modules'
  if version and version.startswith('@'):version=version[1:]
  info=fetch_registry_versions(name,registry,token=token)
  selected=select_registry_version(info['versions'],version or '*')
  package_version=selected.get('version','0.0.0')
  def full_url(value,default):
   value=value or default
   return str(value) if str(value).startswith(('http://','https://')) else registry.rstrip('/')+'/'+str(value).lstrip('/')
  package_url=full_url(selected.get('url'),f'/api/v1/packages/{name}/{package_version}/download')
  signature_url=full_url(selected.get('signature_url'),f'/api/v1/packages/{name}/{package_version}/signature')
  def download(url):
   request=urllib.request.Request(url)
   if token:request.add_header('Authorization','Bearer '+token)
   with urllib.request.urlopen(request,timeout=10) as response:
    return response.read()
  package_bytes=download(package_url)
  actual_sha256=hashlib.sha256(package_bytes).hexdigest()
  expected_sha256=selected.get('sha256','')
  if expected_sha256 and actual_sha256!=expected_sha256:
   raise PeaError(f'Package SHA-256 mismatch: expected {expected_sha256}, got {actual_sha256}')
  signature_bytes=download(signature_url)
  store=PublicTrustStore(trust_store or default_trust_store_path())
  revoked=list(store.data.get('revoked',{}))
  with tempfile.TemporaryDirectory() as td:
   tmp=Path(td)
   package_path=tmp/f'{name}-{package_version}.pelib';package_path.write_bytes(package_bytes)
   signature_path=tmp/f'{name}-{package_version}.sig';signature_path.write_bytes(signature_bytes)
   if public_key:
    verify_ed25519(package_path,signature_path,public_key,revoked=revoked)
    selected_key_id=public_key_id(public_key_bytes(public_key))
   else:
    envelope=json.loads(signature_bytes.decode('utf-8'))
    envelope_key_id=envelope.get('key_id')
    selected_key_id=key_id or envelope_key_id or selected.get('signature_key_id')
    if key_id and envelope_key_id and key_id!=envelope_key_id:
     raise PeaError(f'Requested key {key_id} does not match signature key {envelope_key_id}')
    if not selected_key_id:
     keys=store.registry_keys(registry)
     selected_key_id=keys[0] if keys else None
    if not selected_key_id:raise PeaError(f'No trusted key configured for registry {registry}')
    if selected_key_id not in store.data.get('keys',{}):raise PeaError(f'Untrusted signing key: {selected_key_id}')
    trusted=store.data['keys'][selected_key_id]
    key_path=tmp/'trusted.pub';key_path.write_text(trusted['public_key']+'\n',encoding='utf-8')
    verify_ed25519(package_path,signature_path,key_path,revoked=revoked)
   dest=target/name
   shutil.rmtree(dest,ignore_errors=True)
   safe_extract(package_path,dest)
   write_receipt(dest,package_path,signature_path,selected_key_id,source=registry)
   (dest/'REMOTE_SOURCE.json').write_text(json.dumps({'name':name,'version':package_version,'source':'registry','registry':registry,'sha256':actual_sha256,'key_id':selected_key_id,'verified':True},indent=2,sort_keys=True)+'\n',encoding='utf-8')
  return {'name':name,'version':package_version,'source':'registry','registry':registry,'verified':True,'key_id':selected_key_id,'sha256':actual_sha256,'installed':True}

def publish(root='.', registry=DEFAULT_REGISTRY, token=None,*,sign=False,private_key=None,publisher=None,trust_store=None):
 """Publish a library package (.pelib) to a registry.

 Builds (and optionally signs) the library from the project at `root` and returns
 deterministic publish metadata for CLI upload. Returns name, version, sha256,
 registry, published=True, and optional signature/key metadata.
 """
 out,h=build_library(root)
 mf,data=load_pea_toml(root)
 name=data['project']['name'];version=data['project']['version']
 report={'name':name,'version':version,'sha256':h,'registry':registry,'published':True,'path':str(out),'signed':False}
 if sign:
  signed=sign_library(root,private_key=private_key,publisher=publisher,output=str(out),trust_store=trust_store)
  report['signed']=True;report['signature']=signed['signature'];report['key_id']=signed['key_id'];report['trusted_key']=signed['trusted_key']
 return report

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
