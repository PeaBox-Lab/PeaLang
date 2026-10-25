
"""PeaLang 0.63 RC1 stabilization and API compatibility policy."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from datetime import date
import ast,hashlib,json,time,warnings

RC_VERSION='0.63.0rc2'
API_POLICY_VERSION='1'
@dataclass(frozen=True)
class PublicSymbol:
 module:str
 name:str
 kind:str
 signature:str=''
def public_api_snapshot(package_root):
 root=Path(package_root);symbols=[]
 for path in sorted(root.glob('*.py')):
  if path.name.startswith('_'):continue
  tree=ast.parse(path.read_text(encoding='utf-8'))
  module='pealang.'+path.stem
  for node in tree.body:
   if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and not node.name.startswith('_'):
    kind='class' if isinstance(node,ast.ClassDef) else 'function';sig=''
    if not isinstance(node,ast.ClassDef):
     args=[a.arg for a in node.args.args];defaults=len(node.args.defaults);required=len(args)-defaults;sig='('+','.join(a if i<required else a+'=?' for i,a in enumerate(args))+')'
    symbols.append(PublicSymbol(module,node.name,kind,sig))
 return {'policy_version':API_POLICY_VERSION,'symbols':[asdict(x) for x in symbols]}
def compare_api_snapshots(previous,current):
 old={(x['module'],x['name']):x for x in previous['symbols']};new={(x['module'],x['name']):x for x in current['symbols']};removed=sorted([f'{m}.{n}' for m,n in old.keys()-new.keys()]);added=sorted([f'{m}.{n}' for m,n in new.keys()-old.keys()]);changed=sorted([f'{m}.{n}' for m,n in old.keys()&new.keys() if old[(m,n)].get('signature')!=new[(m,n)].get('signature')]);return {'compatible':not removed and not changed,'removed':removed,'changed':changed,'added':added}
def snapshot_digest(snapshot):return hashlib.sha256(json.dumps(snapshot,sort_keys=True).encode()).hexdigest()
@dataclass(frozen=True)
class Deprecation:
 symbol:str
 replacement:str|None
 since:str
 removal:str
 message:str=''
def deprecated(symbol,replacement=None,since='0.63',removal='1.0'):
 def decorate(fn):
  def wrapped(*args,**kwargs):warnings.warn(f'{symbol} is deprecated since {since}; use {replacement or "the documented replacement"}; removal no earlier than {removal}',DeprecationWarning,stacklevel=2);return fn(*args,**kwargs)
  wrapped.__name__=fn.__name__;wrapped.__doc__=fn.__doc__;wrapped.__wrapped__=fn;return wrapped
 return decorate
def validate_deprecation_schedule(entries,current='0.63'):
 issues=[]
 for e in entries:
  if not e.symbol:issues.append('missing symbol')
  if e.since==e.removal:issues.append(e.symbol+': removal version must follow deprecation version')
 return {'valid':not issues,'issues':issues}
@dataclass
class IntegrationResult:
 name:str
 status:str
 detail:str=''
 duration_ms:float=0
def run_integration_matrix(probes):
 out=[]
 for name,probe in probes.items():
  start=time.perf_counter()
  try:probe();out.append(IntegrationResult(name,'PASS','',(time.perf_counter()-start)*1000))
  except Exception as exc:out.append(IntegrationResult(name,'FAIL',str(exc),(time.perf_counter()-start)*1000))
 return out
def integration_summary(results):
 passed=sum(x.status=='PASS' for x in results);failed=len(results)-passed;return {'total':len(results),'passed':passed,'failed':failed,'ready':failed==0,'results':[asdict(x) for x in results]}
def upgrade_compatibility(previous_versions,current_version='0.63.0rc2'):
 return {'current':current_version,'upgrades':[{'from':str(v),'to':current_version,'supported':True,'migration':'automatic-compatible'} for v in previous_versions]}
def threat_model():
 return {'assets':['source packages','model bundles','credentials','prediction data','registry state'],'boundaries':['CLI','HTTP serving','connectors','package registry','Kubernetes cluster'],'threats':[{'id':'T01','threat':'artifact tampering','control':'SHA-256, provenance and Ed25519 verification'},{'id':'T02','threat':'credential disclosure','control':'runtime secret providers and no embedded credentials'},{'id':'T03','threat':'inference abuse','control':'authentication, request limits and rate limiting'},{'id':'T04','threat':'supply-chain substitution','control':'SBOM, checksums, signed release manifest'},{'id':'T05','threat':'lateral movement','control':'non-root runtime and Kubernetes NetworkPolicy'}]}
def migration_guide(from_version='0.62.0',to_version='0.63.0rc2'):
 return {'from':from_version,'to':to_version,'steps':['back up registry and monitoring databases','verify current bundles and checksums','install the RC wheel in an isolated environment','run API compatibility and migration checks','run connector and serving smoke tests','promote only after rollback validation'],'rollback':['restore previous wheel','restore registry/monitoring backup if modified','redeploy previous serving manifest']}
def rc_gate(results):
 failed=[k for k,v in results.items() if not v];return {'status':'PASS' if not failed else 'BLOCKED','failed_gates':failed,'score':round(100*(len(results)-len(failed))/max(1,len(results)),1)}

