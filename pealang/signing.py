

from dataclasses import dataclass,asdict
from pathlib import Path
import base64,hashlib,hmac,json,os,secrets,time
from .errors import PeaError
@dataclass
class Signature:
 algorithm:str;key_id:str;package_sha256:str;signature:str;created:int
 def to_dict(self):return asdict(self)
def file_hash(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(65536),b''):h.update(b)
 return h.hexdigest()
def key_id(secret):return hashlib.sha256(secret).hexdigest()[:16]
def generate_key(path):
 secret=secrets.token_bytes(32);p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(base64.b64encode(secret).decode()+'\n')
 try:os.chmod(p,0o600)
 except OSError:pass
 return key_id(secret)
def load_key(path):
 try:return base64.b64decode(Path(path).read_text().strip(),validate=True)
 except Exception as e:raise PeaError(f'Invalid signing key: {e}') from e
def sign_package(package,key_path,output=None):
 secret=load_key(key_path);digest=file_hash(package);value=hmac.new(secret,digest.encode(),hashlib.sha256).hexdigest();obj=Signature('HMAC-SHA256',key_id(secret),digest,value,int(time.time()));out=Path(output or (str(package)+'.sig'));out.write_text(json.dumps(obj.to_dict(),indent=2,sort_keys=True)+'\n');return out,obj
def verify_package(package,signature,key_path):
 secret=load_key(key_path);data=json.loads(Path(signature).read_text());digest=file_hash(package)
 if data.get('algorithm')!='HMAC-SHA256':raise PeaError('Unsupported signature algorithm')
 if data.get('key_id')!=key_id(secret):raise PeaError('Signature key ID does not match trusted key')
 if data.get('package_sha256')!=digest:raise PeaError('Package SHA-256 mismatch')
 expected=hmac.new(secret,digest.encode(),hashlib.sha256).hexdigest()
 if not hmac.compare_digest(data.get('signature',''),expected):raise PeaError('Package signature invalid')
 return True
class TrustStore:
 def __init__(self,path):self.path=Path(path);self.data={'keys':{},'registries':{}};self.load()
 def load(self):
  if self.path.exists():self.data=json.loads(self.path.read_text())
 def save(self):self.path.parent.mkdir(parents=True,exist_ok=True);self.path.write_text(json.dumps(self.data,indent=2,sort_keys=True)+'\n')
 def trust_key(self,key_path,label=None):
  secret=load_key(key_path);kid=key_id(secret);self.data['keys'][kid]={'label':label or kid,'key':base64.b64encode(secret).decode()};self.save();return kid
 def trust_registry(self,name,url,key_ids):
  if not str(url).startswith('https://'):raise PeaError('Registry URL must use HTTPS')
  missing=[k for k in key_ids if k not in self.data['keys']]
  if missing:raise PeaError('Unknown trusted key IDs: '+', '.join(missing))
  self.data['registries'][name]={'url':url.rstrip('/'),'keys':list(key_ids)};self.save()


