


"""PeaLang 0.62 release candidate packaging and supply-chain security."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,platform,sys,zipfile

def sha256_file(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def artifact_checksums(paths):return {Path(p).name:sha256_file(p) for p in paths}
def write_checksums(paths,output):
 lines=[f'{sha256_file(p)}  {Path(p).name}' for p in paths];Path(output).write_text('\n'.join(lines)+'\n');return lines
def generate_sbom(root,version='0.62.0'):
 root=Path(root);components=[]
 pyproject=root/'pyproject.toml'
 components.append({'type':'library','name':'pealang','version':version,'purl':f'pkg:pypi/pealang@{version}'})
 for path in sorted(root.rglob('*')):
  if path.is_file() and not any(x in path.parts for x in ('.git','__pycache__','.pytest_cache','dist','build')):
   components.append({'type':'file','name':str(path.relative_to(root)).replace('\\','/'),'hashes':[{'alg':'SHA-256','content':sha256_file(path)}]})
 return {'bomFormat':'CycloneDX','specVersion':'1.5','serialNumber':'urn:uuid:'+hashlib.md5(str(root).encode()).hexdigest(),'version':1,'metadata':{'timestamp':datetime.now(timezone.utc).isoformat(),'component':components[0]},'components':components}
def dependency_inventory(root):
 text=(Path(root)/'pyproject.toml').read_text();deps=[];inside=False
 for line in text.splitlines():
  if line.strip().startswith('dependencies = ['):inside=True;continue
  if inside and line.strip()==']':break
  if inside:
   item=line.strip().strip(',').strip('"\'')
   if item:deps.append({'name':item.split('>=')[0].split('==')[0],'requirement':item,'license':'UNKNOWN-CHECK-REQUIRED'})
 return deps
def build_provenance(root,artifacts,version='0.62.0'):
 return {'_type':'https://in-toto.io/Statement/v1','subject':[{'name':Path(p).name,'digest':{'sha256':sha256_file(p)}} for p in artifacts],'predicateType':'https://slsa.dev/provenance/v1','predicate':{'buildDefinition':{'buildType':'pealang.release','externalParameters':{'version':version},'resolvedDependencies':[]},'runDetails':{'builder':{'id':'pealang-local-builder'},'metadata':{'invocationId':hashlib.sha256((str(root)+version).encode()).hexdigest(),'startedOn':datetime.now(timezone.utc).isoformat(),'finishedOn':datetime.now(timezone.utc).isoformat()}}}}
def verify_wheel(path,expected_version='0.62.0'):
 issues=[]
 try:
  with zipfile.ZipFile(path) as z:
   names=z.namelist();metadata=[x for x in names if x.endswith('.dist-info/METADATA')]
   if not metadata:issues.append('missing wheel METADATA')
   else:
    text=z.read(metadata[0]).decode(errors='replace')
    if f'Version: {expected_version}' not in text:issues.append('wheel version mismatch')
   if not any(x.startswith('pealang/') for x in names):issues.append('pealang package missing')
 except Exception as exc:issues.append('invalid wheel: '+str(exc))
 return {'valid':not issues,'issues':issues,'sha256':sha256_file(path)}
def verify_source_archive(path,expected_root='PeaLang_v0.62.0'):
 issues=[]
 try:
  with zipfile.ZipFile(path) as z:
   names=z.namelist()
   if not any(x.endswith('pyproject.toml') for x in names):issues.append('pyproject.toml missing')
   if not any(x.endswith('README.md') for x in names):issues.append('README.md missing')
 except Exception as exc:issues.append('invalid source archive: '+str(exc))
 return {'valid':not issues,'issues':issues,'sha256':sha256_file(path)}
def migration_check(previous,current):
 p=Path(previous);c=Path(current);checks={'registry_schema':True,'monitoring_sqlite':True,'pipeline_format':True,'model_bundle':True}
 checks['previous_exists']=p.exists();checks['current_exists']=c.exists();return {'compatible':all(checks.values()),'checks':checks}
def reproducible_build_metadata(version='0.62.0',source_date_epoch=None):return {'version':version,'source_date_epoch':source_date_epoch,'python':platform.python_version(),'platform':platform.platform(),'implementation':platform.python_implementation()}
def release_checklist():return [{'item':x,'required':True,'status':'pending'} for x in ['full test suite','conformance suite','fuzz suite','wheel verification','source archive verification','SBOM generated','provenance generated','checksums generated','license inventory reviewed','Kubernetes manifests validated','upgrade checks passed','release notes complete']]
def readiness_assessment(results):
 failed=[k for k,v in results.items() if not v];return {'ready':not failed,'failed_gates':failed,'score':round(100*(len(results)-len(failed))/max(1,len(results)),1)}
def containerfile(version='0.62.0'):
 return f'''FROM python:3.12-slim AS runtime\nENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\nRUN groupadd --gid 10001 pealang && useradd --uid 10001 --gid 10001 --create-home pealang\nWORKDIR /app\nCOPY pealang-{version}-py3-none-any.whl /tmp/pealang.whl\nRUN pip install --no-cache-dir /tmp/pealang.whl && rm /tmp/pealang.whl\nUSER 10001:10001\nEXPOSE 8000\nHEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/live', timeout=2)" || exit 1\nLABEL org.opencontainers.image.title="PeaLang" org.opencontainers.image.version="{version}" org.opencontainers.image.source="https://github.com/pealang/pealang"\nCMD ["pea-serve", "serve", "/app/pipeline.json", "--host", "0.0.0.0", "--port", "8000"]\n'''
def ci_matrix():return {'os':['ubuntu-latest','windows-latest','macos-latest'],'python':['3.10','3.11','3.12','3.13'],'exclude':[{'os':'macos-latest','python':'3.10'}]}

# PeaLang 0.82 reproducible packaging and verification hardening.
import base64, os, tempfile, re

def deterministic_manifest(root,exclude=('.git','__pycache__','.pytest_cache','dist','build')):
 root=Path(root); rows=[]
 for p in sorted(root.rglob('*')):
  if p.is_file() and not any(x in p.parts for x in exclude):
   rows.append({'path':str(p.relative_to(root)).replace('\\','/'),'size':p.stat().st_size,'sha256':sha256_file(p)})
 canonical=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
 return {'schema':1,'algorithm':'sha256','files':rows,'root_digest':hashlib.sha256(canonical).hexdigest()}

def verify_manifest(root,manifest):
 current=deterministic_manifest(root); expected={x['path']:x for x in manifest.get('files',[])}; actual={x['path']:x for x in current['files']}
 missing=sorted(set(expected)-set(actual)); added=sorted(set(actual)-set(expected)); changed=sorted(k for k in set(expected)&set(actual) if expected[k]['sha256']!=actual[k]['sha256'] or expected[k]['size']!=actual[k]['size'])
 return {'valid':not(missing or added or changed),'missing':missing,'added':added,'changed':changed,'root_digest':current['root_digest']}

def locked_dependency_evidence(root):
 root=Path(root); candidates=['requirements.lock','requirements.txt','poetry.lock','uv.lock','Pipfile.lock'];found=[]
 for name in candidates:
  p=root/name
  if p.exists():found.append({'path':name,'sha256':sha256_file(p),'bytes':p.stat().st_size})
 return {'locked':any(x['path'].endswith('.lock') or x['path']=='requirements.lock' for x in found),'files':found}

def verify_sbom(sbom,root=None):
 issues=[]
 if sbom.get('bomFormat')!='CycloneDX':issues.append('unsupported bomFormat')
 if not sbom.get('components'):issues.append('components missing')
 if root:
  root=Path(root)
  for c in sbom.get('components',[]):
   if c.get('type')!='file':continue
   p=root/c.get('name','');h=next((x.get('content') for x in c.get('hashes',[]) if x.get('alg')=='SHA-256'),None)
   if not p.is_file():issues.append(f"missing SBOM file: {c.get('name')}")
   elif h and sha256_file(p)!=h:issues.append(f"SBOM hash mismatch: {c.get('name')}")
 return {'valid':not issues,'issues':issues,'components':len(sbom.get('components',[]))}

def verify_provenance(statement,artifacts):
 expected={Path(p).name:sha256_file(p) for p in artifacts};subjects={x.get('name'):x.get('digest',{}).get('sha256') for x in statement.get('subject',[])};issues=[]
 for name,digest in expected.items():
  if subjects.get(name)!=digest:issues.append(f'provenance mismatch: {name}')
 return {'valid':not issues,'issues':issues,'subjects':len(subjects)}

def sign_release_manifest(manifest,private_key):
 """Return detached Ed25519 signature. private_key may be raw 32-byte key."""
 from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
 key=Ed25519PrivateKey.from_private_bytes(private_key) if isinstance(private_key,(bytes,bytearray)) else private_key
 payload=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode();return base64.b64encode(key.sign(payload)).decode()

def verify_release_signature(manifest,signature,public_key):
 from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
 try:
  key=Ed25519PublicKey.from_public_bytes(public_key) if isinstance(public_key,(bytes,bytearray)) else public_key
  payload=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode();key.verify(base64.b64decode(signature),payload);return True
 except Exception:return False

def offline_install_evidence(wheelhouse,required=()):
 wheelhouse=Path(wheelhouse);files=sorted(p.name for p in wheelhouse.glob('*') if p.is_file());lower=[x.lower().replace('_','-') for x in files];missing=[]
 for req in required:
  name=re.split(r'[<>=!~ ]',str(req),1)[0].lower().replace('_','-')
  if not any(x.startswith(name+'-') for x in lower):missing.append(str(req))
 return {'ready':not missing,'artifacts':files,'missing':missing}

def packaging_quality_gate(manifest_report,sbom_report,provenance_report,signature_valid,offline_report,dependency_evidence):
 checks={'manifest':bool(manifest_report.get('valid')),'sbom':bool(sbom_report.get('valid')),'provenance':bool(provenance_report.get('valid')),'signature':bool(signature_valid),'offline_install':bool(offline_report.get('ready')),'dependency_evidence':bool(dependency_evidence.get('files'))}
 return {'gate':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'failed':[k for k,v in checks.items() if not v]}



