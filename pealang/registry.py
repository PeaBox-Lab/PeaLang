"""Verified registry index, cache and remote-install primitives."""
from pathlib import Path
import hashlib,json,ssl,urllib.request
from .errors import PeaError
from .ed25519_signing import verify_ed25519,PublicTrustStore
from .secure_packages import safe_extract,write_receipt,validate_remote_source
class PackageCache:
 def __init__(self,path):self.path=Path(path);self.path.mkdir(parents=True,exist_ok=True)
 def put(self,name,data):
  digest=hashlib.sha256(data).hexdigest();p=self.path/f'{digest}-{Path(name).name}';p.write_bytes(data);return p,digest
 def find_hash(self,digest):
  hits=list(self.path.glob(digest+'-*'));return hits[0] if hits else None
def fetch_https(url,timeout=20):
 validate_remote_source(url);ctx=ssl.create_default_context()
 with urllib.request.urlopen(url,timeout=timeout,context=ctx) as r:return r.read()
def verify_registry_index(index_path,signature_path,public_key,revoked=None):
 return verify_ed25519(index_path,signature_path,public_key,revoked)
def install_verified(package,signature,public_key,destination,source='registry',revoked=None):
 verify_ed25519(package,signature,public_key,revoked);safe_extract(package,destination);data=json.loads(Path(signature).read_text());return write_receipt(destination,package,signature,data['key_id'],source)
def remote_install(package_url,signature_url,public_key,destination,cache,expected_sha256=None,offline=False,revoked=None):
 cache=cache if isinstance(cache,PackageCache) else PackageCache(cache)
 if offline:
  if not expected_sha256:raise PeaError('Offline install requires expected SHA-256')
  package=cache.find_hash(expected_sha256)
  if not package:raise PeaError('Package not found in offline cache')
  sig=Path(str(package)+'.sig')
  if not sig.exists():raise PeaError('Signature not found in offline cache')
 else:
  data=fetch_https(package_url);package,digest=cache.put(Path(package_url).name,data)
  sigdata=fetch_https(signature_url);sig=Path(str(package)+'.sig');sig.write_bytes(sigdata)
  if expected_sha256 and digest!=expected_sha256:raise PeaError('Downloaded package SHA-256 does not match lockfile')
 return install_verified(package,sig,public_key,destination,'registry',revoked)
