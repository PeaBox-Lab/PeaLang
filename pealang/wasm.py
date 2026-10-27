from dataclasses import dataclass,asdict
from pathlib import Path
import json
MAGIC=b'\x00asm'; VERSION=b'\x01\x00\x00\x00'; ABI_VERSION='pea-browser-abi-1'
def _uleb(n):
 out=bytearray()
 while True:
  b=n&127;n>>=7
  if n:b|=128
  out.append(b)
  if not n:return bytes(out)
def _custom(name,payload):
 name=name.encode();body=_uleb(len(name))+name+payload
 return b'\x00'+_uleb(len(body))+body
@dataclass(frozen=True)
class WasmPolicy:
 max_memory_pages:int=256;max_fuel:int=1_000_000;allow_network:bool=False;allow_filesystem:bool=False;allow_clock:bool=True
@dataclass
class WasmArtifact:
 peac:dict;exports:list;imports:list;policy:WasmPolicy
 def manifest(self):return {'format':'PEAWASM','version':'0.39','abi':ABI_VERSION,'exports':self.exports,'imports':self.imports,'policy':asdict(self.policy)}
 def to_bytes(self):
  m=json.dumps(self.manifest(),sort_keys=True,separators=(',',':')).encode();p=json.dumps(self.peac,sort_keys=True,separators=(',',':')).encode()
  return MAGIC+VERSION+_custom('pealang.manifest',m)+_custom('pealang.peac',p)
 def save(self,path):Path(path).write_bytes(self.to_bytes())
def compile_peac_to_wasm(module,policy=None,exports=None,imports=None):
 return WasmArtifact(module.to_dict() if hasattr(module,'to_dict') else dict(module),list(exports or ['pea_run']),list(imports or ['pea_host_log']),policy or WasmPolicy())
def inspect_wasm(value):
 data=Path(value).read_bytes() if isinstance(value,(str,Path)) else bytes(value)
 if not data.startswith(MAGIC+VERSION):raise ValueError('Not a WebAssembly v1 module')
 pos=8;sections={}
 def read():
  nonlocal pos
  out=shift=0
  while True:
   b=data[pos];pos+=1;out|=(b&127)<<shift
   if not b&128:return out
   shift+=7
 while pos<len(data):
  kind=data[pos];pos+=1;size=read();end=pos+size
  if kind==0:
   n=read();name=data[pos:pos+n].decode();pos+=n;sections[name]=data[pos:end]
  pos=end
 return {'manifest':json.loads(sections['pealang.manifest']),'peac':json.loads(sections['pealang.peac'])}
def browser_loader_source():return 'export async function loadPeaWasm(url,imports={}) { const bytes=await (await fetch(url)).arrayBuffer(); return WebAssembly.instantiate(bytes,imports); }'
