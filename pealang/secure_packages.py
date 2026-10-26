



from pathlib import Path
import json,tarfile,time
from .errors import PeaError
from .signing import file_hash
def safe_extract(package,destination):
 dest=Path(destination).resolve();dest.mkdir(parents=True,exist_ok=True)
 with tarfile.open(package,'r:gz') as tf:
  for m in tf.getmembers():
   target=(dest/m.name).resolve()
   if dest not in target.parents and target!=dest:raise PeaError(f'Unsafe package path: {m.name}')
   if m.issym() or m.islnk():raise PeaError(f'Package links are not allowed: {m.name}')
  tf.extractall(dest,filter='data')
 return dest
def write_receipt(destination,package,signature=None,key_id=None,source='local'):
 receipt={'installed_at':int(time.time()),'package':Path(package).name,'sha256':file_hash(package),'signature':str(signature) if signature else None,'key_id':key_id,'source':source}
 p=Path(destination)/'.pea-install.json';p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n');return p
def validate_remote_source(url):
 if not str(url).startswith('https://'):raise PeaError('Remote package source must use HTTPS')
 return True
def dependency_confusion_guard(name,declared_source,registry_name):
 if declared_source not in ('registry','git','path'):raise PeaError(f"Dependency '{name}' has unknown source")
 if declared_source!='registry' and registry_name:raise PeaError(f"Dependency '{name}' cannot be substituted from registry '{registry_name}'")
 return True




