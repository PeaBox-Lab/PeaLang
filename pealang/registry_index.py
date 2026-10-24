
"""Canonical signed registry indexes, publisher namespaces and anti-replay policy."""
from __future__ import annotations
from dataclasses import dataclass,asdict,field
from pathlib import Path
import json,time
from .errors import PeaError
from .ed25519_signing import sign_ed25519,verify_ed25519,PublicTrustStore
@dataclass
class PackageRecord:
 name:str;version:str;sha256:str;url:str;signature_url:str;publisher_key_id:str;published:int;expires:int|None=None
@dataclass
class RegistryIndex:
 registry:str;sequence:int;generated:int;packages:list[dict]=field(default_factory=list)
 def canonical_bytes(self):return json.dumps(asdict(self),sort_keys=True,separators=(',',':')).encode()
 def save(self,path):Path(path).write_bytes(self.canonical_bytes()+b'\n')
 @classmethod
 def load(cls,path):
  d=json.loads(Path(path).read_text());return cls(d['registry'],d['sequence'],d['generated'],d.get('packages',[]))
def build_index(registry,sequence,records):return RegistryIndex(registry,int(sequence),int(time.time()),[asdict(x) if hasattr(x,'__dataclass_fields__') else dict(x) for x in records])
def validate_index(index,expected_registry=None,last_sequence=None,now=None):
 now=int(now or time.time())
 if expected_registry and index.registry!=expected_registry:raise PeaError('Registry identity mismatch')
 if last_sequence is not None and index.sequence<=last_sequence:raise PeaError('Registry index replay or stale sequence detected')
 seen=set()
 for p in index.packages:
  key=(p['name'],p['version'])
  if key in seen:raise PeaError(f'Duplicate immutable version: {p["name"]} {p["version"]}')
  seen.add(key)
  if p.get('expires') and now>p['expires']:raise PeaError(f'Package metadata expired: {p["name"]} {p["version"]}')
  if not p['url'].startswith('https://') or not p['signature_url'].startswith('https://'):raise PeaError('Registry package URLs must use HTTPS')
 return True
class NamespacePolicy:
 def __init__(self):self.bindings={}
 def authorize(self,namespace,key_id):self.bindings.setdefault(namespace,set()).add(key_id)
 def check(self,package,key_id):
  namespace=package.split('/',1)[0] if '/' in package else package.split('.',1)[0]
  if key_id not in self.bindings.get(namespace,set()):raise PeaError(f'Publisher {key_id} is not authorized for namespace {namespace}')
  return True
class RegistryState:
 def __init__(self,path):self.path=Path(path);self.data={'sequences':{},'versions':{}};self.load()
 def load(self):
  if self.path.exists():self.data=json.loads(self.path.read_text())
 def save(self):self.path.parent.mkdir(parents=True,exist_ok=True);self.path.write_text(json.dumps(self.data,indent=2,sort_keys=True)+'\n')
 def accept(self,index):
  last=self.data['sequences'].get(index.registry)
  validate_index(index,index.registry,last)
  versions=self.data['versions'].setdefault(index.registry,{})
  for p in index.packages:
   prior=versions.get(p['name'],{}).get(p['version'])
   if prior and prior!=p['sha256']:raise PeaError(f'Immutable version changed: {p["name"]} {p["version"]}')
   versions.setdefault(p['name'],{})[p['version']]=p['sha256']
  self.data['sequences'][index.registry]=index.sequence;self.save();return True
