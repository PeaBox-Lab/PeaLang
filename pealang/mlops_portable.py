"""PeaLang 0.57 pipeline portability, monitoring backends and MLOps CLI services."""
from __future__ import annotations
from dataclasses import asdict
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,sqlite3
from .ml import StandardScaler,MinMaxScaler,LinearRegression,LogisticRegression,RidgeRegression,LassoRegression,ProductionPipeline
from .mlops import ModelRegistry,create_model_bundle,load_model_bundle
from .mlops_secure import AlertRule,evaluate_alerts,PromotionPolicy,can_promote,sign_bundle,verify_bundle_signature

PIPELINE_FORMAT='pealang.pipeline.v1'
def _transformer_record(t):
 if isinstance(t,StandardScaler):return {'type':'standard_scaler','means':t.means,'scales':t.scales}
 if isinstance(t,MinMaxScaler):return {'type':'minmax_scaler','mins':t.mins,'ranges':t.ranges}
 raise TypeError('Unsupported transformer: '+t.__class__.__name__)
def _model_record(m):
 d=m.to_dict();d['class']=m.__class__.__name__;return d
def save_pipeline(pipeline,path,metadata=None):
 doc={'format':PIPELINE_FORMAT,'created_at':datetime.now(timezone.utc).isoformat(),'features':pipeline.features,'target':pipeline.target,'transformers':[_transformer_record(t) for t in pipeline.fitted],'model':_model_record(pipeline.model),'metadata':metadata or {}}
 Path(path).write_text(json.dumps(doc,indent=2),encoding='utf-8');return doc
def load_pipeline(path):
 d=json.loads(Path(path).read_text(encoding='utf-8'))
 if d.get('format')!=PIPELINE_FORMAT:raise ValueError('Unsupported pipeline format: '+str(d.get('format')))
 transforms=[]
 for x in d['transformers']:
  if x['type']=='standard_scaler':t=StandardScaler(x['means'],x['scales'])
  elif x['type']=='minmax_scaler':t=MinMaxScaler(x['mins'],x['ranges'])
  else:raise ValueError('Unsupported transformer type: '+x['type'])
  transforms.append(t)
 classes={'LinearRegression':LinearRegression,'LogisticRegression':LogisticRegression,'RidgeRegression':RidgeRegression,'LassoRegression':LassoRegression};md=d['model'];m=classes[md['class']]();m.coefficients=md['coefficients'];m.intercept=md['intercept'];m.features=md['features']
 if hasattr(m,'threshold') and 'threshold' in md:m.threshold=md['threshold']
 p=ProductionPipeline([],m);p.fitted=transforms;p.features=d['features'];p.target=d['target'];return p,d
class SQLiteMonitoringStore:
 def __init__(self,path):
  self.path=str(path);self.db=sqlite3.connect(self.path);self.db.execute('create table if not exists events(event_id text primary key,model_id text,metric text,value real,timestamp text,dimensions text)');self.db.commit()
 def record(self,model_id,metric,value,dimensions=None,timestamp=None):
  import uuid
  ts=timestamp or datetime.now(timezone.utc).isoformat();eid=str(uuid.uuid4());self.db.execute('insert into events values(?,?,?,?,?,?)',(eid,model_id,metric,float(value),ts,json.dumps(dimensions or {})));self.db.commit();return {'event_id':eid,'model_id':model_id,'metric':metric,'value':float(value),'timestamp':ts,'dimensions':dimensions or {}}
 def query(self,model_id=None,metric=None,since=None):
  sql='select event_id,model_id,metric,value,timestamp,dimensions from events where 1=1';args=[]
  for clause,value in [(' and model_id=?',model_id),(' and metric=?',metric),(' and timestamp>=?',since)]:
   if value is not None:sql+=clause;args.append(value)
  return [{'event_id':a,'model_id':b,'metric':c,'value':d,'timestamp':e,'dimensions':json.loads(f)} for a,b,c,d,e,f in self.db.execute(sql,args)]
 def summary(self,model_id,metric,since=None):
  vals=[x['value'] for x in self.query(model_id,metric,since)];return {'count':len(vals),'min':min(vals) if vals else None,'max':max(vals) if vals else None,'mean':sum(vals)/len(vals) if vals else None}
def load_alert_policy(path):
 d=json.loads(Path(path).read_text());return [AlertRule(**x) for x in d.get('rules',[])]
def deployment_manifest(model_id,version,bundle_path,environment='production',replicas=1,resources=None):return {'apiVersion':'pealang.io/v1','kind':'ModelDeployment','metadata':{'name':model_id,'version':version},'spec':{'bundle':str(bundle_path),'environment':environment,'replicas':int(replicas),'resources':resources or {}}}
def cli(argv=None):
 parser=argparse.ArgumentParser(prog='pea-ml');sub=parser.add_subparsers(dest='command',required=True)
 p=sub.add_parser('bundle');p.add_argument('model');p.add_argument('output');p.add_argument('--model-id',default='model');p.add_argument('--version',default='1.0.0')
 p=sub.add_parser('verify');p.add_argument('bundle')
 p=sub.add_parser('register');p.add_argument('registry');p.add_argument('model_id');p.add_argument('version');p.add_argument('bundle')
 p=sub.add_parser('promote');p.add_argument('registry');p.add_argument('model_id');p.add_argument('version');p.add_argument('stage');p.add_argument('--approver')
 p=sub.add_parser('monitor');p.add_argument('store');p.add_argument('model_id');p.add_argument('metric');p.add_argument('value',type=float)
 p=sub.add_parser('alerts');p.add_argument('store');p.add_argument('model_id');p.add_argument('policy')
 a=parser.parse_args(argv)
 if a.command=='bundle':
  from .ml import load_model
  print(json.dumps(create_model_bundle(load_model(a.model),a.output,model_id=a.model_id,version=a.version),indent=2));return 0
 if a.command=='verify':load_model_bundle(a.bundle);print('PASS');return 0
 if a.command=='register':print(asdict(ModelRegistry(a.registry).register(a.model_id,a.version,a.bundle)));return 0
 if a.command=='promote':print(asdict(ModelRegistry(a.registry).transition(a.model_id,a.version,a.stage,a.approver)));return 0
 if a.command=='monitor':print(SQLiteMonitoringStore(a.store).record(a.model_id,a.metric,a.value));return 0
 if a.command=='alerts':
  events=[type('E',(),x) for x in SQLiteMonitoringStore(a.store).query(a.model_id)];print([asdict(x) for x in evaluate_alerts(a.model_id,events,load_alert_policy(a.policy))]);return 0
