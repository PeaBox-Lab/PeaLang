

"""PeaLang 0.61 Kubernetes security and release-candidate stabilization."""
from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
import json,time

@dataclass
class SecureKubernetesConfig:
 name:str='pealang-model';namespace:str='default';image:str='pealang/model:0.61.0';port:int=8000;replicas:int=2;service_account:str|None=None
 run_as_user:int=10001;run_as_group:int=10001;fs_group:int=10001;config_map:str|None=None;secret_name:str|None=None
 allowed_ingress_labels:dict=field(default_factory=lambda:{'app':'ingress'})
 topology_key:str='kubernetes.io/hostname';min_available:int=1

def secure_kubernetes_manifests(c=SecureKubernetesConfig()):
 labels={'app':c.name};env=[]
 if c.config_map:env.append({'configMapRef':{'name':c.config_map}})
 if c.secret_name:env.append({'secretRef':{'name':c.secret_name}})
 container={'name':'server','image':c.image,'ports':[{'name':'http','containerPort':c.port}],
 'securityContext':{'allowPrivilegeEscalation':False,'readOnlyRootFilesystem':True,'runAsNonRoot':True,'runAsUser':c.run_as_user,'runAsGroup':c.run_as_group,'capabilities':{'drop':['ALL']},'seccompProfile':{'type':'RuntimeDefault'}},
 'volumeMounts':[{'name':'tmp','mountPath':'/tmp'}],
 'startupProbe':{'httpGet':{'path':'/live','port':'http'},'failureThreshold':30,'periodSeconds':2},
 'readinessProbe':{'httpGet':{'path':'/ready','port':'http'},'periodSeconds':5},
 'livenessProbe':{'httpGet':{'path':'/live','port':'http'},'periodSeconds':10},
 'lifecycle':{'preStop':{'exec':{'command':['sh','-c','wget -qO- http://127.0.0.1:'+str(c.port)+'/drain || true; sleep 10']}}}}
 if env:container['envFrom']=env
 pod={'securityContext':{'runAsNonRoot':True,'runAsUser':c.run_as_user,'runAsGroup':c.run_as_group,'fsGroup':c.fs_group,'seccompProfile':{'type':'RuntimeDefault'}},'terminationGracePeriodSeconds':30,'containers':[container],'volumes':[{'name':'tmp','emptyDir':{}}],
 'topologySpreadConstraints':[{'maxSkew':1,'topologyKey':c.topology_key,'whenUnsatisfiable':'ScheduleAnyway','labelSelector':{'matchLabels':labels}}],
 'affinity':{'podAntiAffinity':{'preferredDuringSchedulingIgnoredDuringExecution':[{'weight':100,'podAffinityTerm':{'labelSelector':{'matchLabels':labels},'topologyKey':c.topology_key}}]}}}
 if c.service_account:pod['serviceAccountName']=c.service_account
 deployment={'apiVersion':'apps/v1','kind':'Deployment','metadata':{'name':c.name,'namespace':c.namespace,'labels':labels},'spec':{'replicas':c.replicas,'selector':{'matchLabels':labels},'template':{'metadata':{'labels':labels},'spec':pod}}}
 service={'apiVersion':'v1','kind':'Service','metadata':{'name':c.name,'namespace':c.namespace,'labels':labels},'spec':{'selector':labels,'ports':[{'name':'http','port':80,'targetPort':'http'}]}}
 pdb={'apiVersion':'policy/v1','kind':'PodDisruptionBudget','metadata':{'name':c.name,'namespace':c.namespace},'spec':{'minAvailable':c.min_available,'selector':{'matchLabels':labels}}}
 network={'apiVersion':'networking.k8s.io/v1','kind':'NetworkPolicy','metadata':{'name':c.name,'namespace':c.namespace},'spec':{'podSelector':{'matchLabels':labels},'policyTypes':['Ingress','Egress'],'ingress':[{'from':[{'podSelector':{'matchLabels':c.allowed_ingress_labels}}],'ports':[{'protocol':'TCP','port':c.port}]}],'egress':[{'to':[{'namespaceSelector':{}}],'ports':[{'protocol':'TCP','port':53},{'protocol':'UDP','port':53},{'protocol':'TCP','port':443}] }]}}
 return [deployment,service,pdb,network]
def to_yaml(value,indent=0):
 space='  '*indent
 if isinstance(value,dict):
  lines=[]
  for k,v in value.items():
   if isinstance(v,(dict,list)):lines.append(space+str(k)+':');lines.extend(to_yaml(v,indent+1).splitlines())
   else:lines.append(space+str(k)+': '+_scalar(v))
  return '\n'.join(lines)
 if isinstance(value,list):
  lines=[]
  for item in value:
   if isinstance(item,dict):
    sub=to_yaml(item,indent+1).splitlines();lines.append(space+'- '+sub[0].lstrip());lines.extend(sub[1:])
   else:lines.append(space+'- '+_scalar(item))
  return '\n'.join(lines)
 return space+_scalar(value)
def _scalar(value):
 if value is None:return 'null'
 if value is True:return 'true'
 if value is False:return 'false'
 if isinstance(value,(int,float)):return str(value)
 text=str(value)
 if not text or any(x in text for x in ':#{}[],&*?|-<>=!%@`') or text.strip()!=text:return json.dumps(text)
 return text
def write_secure_manifests(directory,config=SecureKubernetesConfig(),format='yaml'):
 p=Path(directory);p.mkdir(parents=True,exist_ok=True);names=['deployment','service','pdb','networkpolicy'];paths=[]
 for name,doc in zip(names,secure_kubernetes_manifests(config)):
  target=p/(name+('.yaml' if format=='yaml' else '.json'));target.write_text((to_yaml(doc)+'\n') if format=='yaml' else json.dumps(doc,indent=2)+'\n');paths.append(str(target))
 return paths
def validate_manifests(documents):
 issues=[]
 required={'apiVersion','kind','metadata'}
 for i,d in enumerate(documents):
  missing=required-set(d)
  if missing:issues.append(f'document {i}: missing '+','.join(sorted(missing)))
  if d.get('kind')=='Deployment':
   containers=d.get('spec',{}).get('template',{}).get('spec',{}).get('containers',[])
   if not containers:issues.append('deployment: no containers')
   for c in containers:
    s=c.get('securityContext',{})
    if s.get('allowPrivilegeEscalation') is not False:issues.append('deployment: privilege escalation not disabled')
    if not s.get('readOnlyRootFilesystem'):issues.append('deployment: root filesystem is writable')
    if s.get('capabilities',{}).get('drop')!=['ALL']:issues.append('deployment: Linux capabilities not fully dropped')
 return {'valid':not issues,'issues':issues}
class DrainController:
 def __init__(self):self.draining=False;self.active=0
 def begin(self):
  if self.draining:raise RuntimeError('Runtime is draining')
  self.active+=1
 def end(self):self.active=max(0,self.active-1)
 def drain(self,timeout=30,clock=time.time,sleep=time.sleep):
  self.draining=True;start=clock()
  while self.active and clock()-start<timeout:sleep(.01)
  return self.active==0
@dataclass(frozen=True)
class CompatibilityCase:
 python:str;platform:str;status:str;notes:str=''
def rc_compatibility_matrix():return [CompatibilityCase('3.10','Windows','supported'),CompatibilityCase('3.11','Linux','supported'),CompatibilityCase('3.12','Linux','supported'),CompatibilityCase('3.13','Linux','experimental'),CompatibilityCase('3.11','macOS','supported')]
def soak_test(call,duration_seconds=.1,interval_seconds=0):
 start=time.perf_counter();calls=errors=0;latencies=[]
 while time.perf_counter()-start<duration_seconds:
  s=time.perf_counter()
  try:call(calls);calls+=1;latencies.append((time.perf_counter()-s)*1000)
  except Exception:errors+=1
  if interval_seconds:time.sleep(interval_seconds)
 return {'duration_seconds':time.perf_counter()-start,'calls':calls,'errors':errors,'max_latency_ms':max(latencies) if latencies else None,'status':'PASS' if errors==0 else 'FAIL'}


