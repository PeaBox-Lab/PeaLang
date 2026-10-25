
"""Ed25519 publisher signatures and public-key trust for PeaLang packages."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import base64,hashlib,json,os,time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from .errors import PeaError
from .signing import file_hash
@dataclass
class Ed25519Envelope:
 algorithm:str;key_id:str;package_sha256:str;signature:str;created:int;publisher:str|None=None
 def to_dict(self):return asdict(self)
def public_key_id(raw):return hashlib.sha256(raw).hexdigest()[:24]
def generate_ed25519_keypair(private_path,public_path=None):
 private_path=Path(private_path);public_path=Path(public_path or (str(private_path)+'.pub'));private_path.parent.mkdir(parents=True,exist_ok=True)
 private=Ed25519PrivateKey.generate();priv_raw=private.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption());pub_raw=private.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
 private_path.write_text(base64.b64encode(priv_raw).decode()+'\n');public_path.write_text(base64.b64encode(pub_raw).decode()+'\n')
 try:os.chmod(private_path,0o600)
 except OSError:pass
 return public_key_id(pub_raw),private_path,public_path
def _private(path):return Ed25519PrivateKey.from_private_bytes(base64.b64decode(Path(path).read_text().strip(),validate=True))
def _public(path):return Ed25519PublicKey.from_public_bytes(base64.b64decode(Path(path).read_text().strip(),validate=True))
def public_key_bytes(path):return base64.b64decode(Path(path).read_text().strip(),validate=True)
def sign_ed25519(package,private_key,output=None,publisher=None):
 digest=file_hash(package);key=_private(private_key);pub=key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw);signature=key.sign(digest.encode());env=Ed25519Envelope('Ed25519',public_key_id(pub),digest,base64.b64encode(signature).decode(),int(time.time()),publisher);out=Path(output or (str(package)+'.sig'));out.write_text(json.dumps(env.to_dict(),indent=2,sort_keys=True)+'\n');return out,env
def verify_ed25519(package,signature,public_key,revoked=None):
 data=json.loads(Path(signature).read_text());pub=public_key_bytes(public_key);kid=public_key_id(pub)
 if data.get('algorithm')!='Ed25519':raise PeaError('Unsupported signature algorithm')
 if data.get('key_id')!=kid:raise PeaError('Signature key ID mismatch')
 if kid in set(revoked or []):raise PeaError(f'Signing key {kid} is revoked')
 digest=file_hash(package)
 if digest!=data.get('package_sha256'):raise PeaError('Package SHA-256 mismatch')
 try:_public(public_key).verify(base64.b64decode(data['signature']),digest.encode())
 except InvalidSignature as e:raise PeaError('Ed25519 package signature invalid') from e
 return True
class PublicTrustStore:
 def __init__(self,path):self.path=Path(path);self.data={'keys':{},'revoked':{},'registries':{}};self.load()
 def load(self):
  if self.path.exists():self.data=json.loads(self.path.read_text())
 def save(self):self.path.parent.mkdir(parents=True,exist_ok=True);self.path.write_text(json.dumps(self.data,indent=2,sort_keys=True)+'\n')
 def trust(self,public_key,label=None):
  raw=public_key_bytes(public_key);kid=public_key_id(raw);self.data['keys'][kid]={'label':label or kid,'public_key':base64.b64encode(raw).decode()};self.save();return kid
 def revoke(self,key_id,reason='revoked'):
  if key_id not in self.data['keys']:raise PeaError('Unknown key ID')
  self.data['revoked'][key_id]={'reason':reason,'at':int(time.time())};self.save()
 def configure_registry(self,name,url,key_ids):
  if not url.startswith('https://'):raise PeaError('Registry URL must use HTTPS')
  for kid in key_ids:
   if kid not in self.data['keys'] or kid in self.data['revoked']:raise PeaError(f'Untrusted or revoked key: {kid}')
  self.data['registries'][name]={'url':url.rstrip('/'),'keys':list(key_ids)};self.save()

