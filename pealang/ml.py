"""PeaLang 0.53 dependency-light machine learning foundations."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from math import exp,log,sqrt
import json,random
from .data import DataFrame

def _dot(a,b):return sum(x*y for x,y in zip(a,b))
def _features(frame,columns):return [[float(r.get(c,0) or 0) for c in columns] for r in frame.to_dicts()]
def _target(frame,column):return [float(r.get(column,0) or 0) for r in frame.to_dicts()]
def train_test_split(frame,test_size=.2,shuffle=False,seed=None):
 rows=frame.to_dicts()
 if shuffle:rows=list(rows);random.Random(seed).shuffle(rows)
 n=int(test_size) if isinstance(test_size,int) else max(1,int(round(len(rows)*float(test_size))));n=min(max(n,0),len(rows));return DataFrame(rows[:-n] if n else rows),DataFrame(rows[-n:] if n else [])
@dataclass
class StandardScaler:
 means:dict|None=None;scales:dict|None=None
 def fit(self,frame,columns):
  self.means={};self.scales={}
  for c in columns:
   v=[float(r[c]) for r in frame.to_dicts() if r.get(c) is not None];m=sum(v)/len(v) if v else 0;sd=sqrt(sum((x-m)**2 for x in v)/len(v)) if v else 1;self.means[c]=m;self.scales[c]=sd or 1
  return self
 def transform(self,frame):return DataFrame([{**r,**{c:((r.get(c)-self.means[c])/self.scales[c] if r.get(c) is not None else None) for c in self.means}} for r in frame.to_dicts()])
 def fit_transform(self,frame,columns):return self.fit(frame,columns).transform(frame)
@dataclass
class MinMaxScaler:
 mins:dict|None=None;ranges:dict|None=None
 def fit(self,frame,columns):
  self.mins={};self.ranges={}
  for c in columns:
   v=[float(r[c]) for r in frame.to_dicts() if r.get(c) is not None];lo=min(v) if v else 0;hi=max(v) if v else 1;self.mins[c]=lo;self.ranges[c]=(hi-lo) or 1
  return self
 def transform(self,frame):return DataFrame([{**r,**{c:((r.get(c)-self.mins[c])/self.ranges[c] if r.get(c) is not None else None) for c in self.mins}} for r in frame.to_dicts()])
def impute(frame,columns=None,strategy='mean',fill_value=None):
 cols=list(columns or frame.columns);fills={}
 for c in cols:
  v=[r.get(c) for r in frame.to_dicts() if r.get(c) is not None]
  if strategy=='mean':fills[c]=sum(v)/len(v) if v else fill_value
  elif strategy=='median':
   s=sorted(v);fills[c]=(s[len(s)//2] if len(s)%2 else (s[len(s)//2-1]+s[len(s)//2])/2) if s else fill_value
  elif strategy=='most_frequent':fills[c]=max(set(v),key=v.count) if v else fill_value
  elif strategy=='constant':fills[c]=fill_value
  else:raise ValueError('Unsupported imputation strategy: '+strategy)
 return DataFrame([{k:(fills.get(k) if v is None and k in fills else v) for k,v in r.items()} for r in frame.to_dicts()])
def one_hot_encode(frame,columns,drop_original=True):
 cats={c:sorted({str(r.get(c)) for r in frame.to_dicts() if r.get(c) is not None}) for c in columns};out=[]
 for r in frame.to_dicts():
  row={k:v for k,v in r.items() if not(drop_original and k in columns)}
  for c,values in cats.items():
   for v in values:row[c+'_'+v]=1 if str(r.get(c))==v else 0
  out.append(row)
 return DataFrame(out)
@dataclass
class LinearRegression:
 coefficients:list|None=None;intercept:float=0;features:list|None=None
 def fit(self,frame,features,target,epochs=2000,learning_rate=.01):
  self.features=list(features);X=_features(frame,self.features);y=_target(frame,target);self.coefficients=[0.0]*len(self.features);self.intercept=0.0;n=len(y)
  for _ in range(int(epochs)):
   pred=[self.intercept+_dot(self.coefficients,x) for x in X];errors=[p-a for p,a in zip(pred,y)];self.intercept-=learning_rate*2*sum(errors)/n
   for j in range(len(self.coefficients)):self.coefficients[j]-=learning_rate*2*sum(e*x[j] for e,x in zip(errors,X))/n
  return self
 def predict_rows(self,frame):return [self.intercept+_dot(self.coefficients,x) for x in _features(frame,self.features)]
 def predict(self,frame,name='prediction'):return DataFrame([{**r,name:p} for r,p in zip(frame.to_dicts(),self.predict_rows(frame))])
 def to_dict(self):return {'type':'linear_regression','coefficients':self.coefficients,'intercept':self.intercept,'features':self.features}
@dataclass
class LogisticRegression:
 coefficients:list|None=None;intercept:float=0;features:list|None=None;threshold:float=.5
 def fit(self,frame,features,target,epochs=2000,learning_rate=.1):
  self.features=list(features);X=_features(frame,self.features);y=_target(frame,target);self.coefficients=[0.0]*len(self.features);self.intercept=0;n=len(y)
  for _ in range(int(epochs)):
   probs=[1/(1+exp(-max(-30,min(30,self.intercept+_dot(self.coefficients,x))))) for x in X];errors=[p-a for p,a in zip(probs,y)];self.intercept-=learning_rate*sum(errors)/n
   for j in range(len(self.coefficients)):self.coefficients[j]-=learning_rate*sum(e*x[j] for e,x in zip(errors,X))/n
  return self
 def predict_proba(self,frame):return [1/(1+exp(-max(-30,min(30,self.intercept+_dot(self.coefficients,x))))) for x in _features(frame,self.features)]
 def predict(self,frame,name='prediction'):return DataFrame([{**r,name:int(p>=self.threshold),name+'_probability':p} for r,p in zip(frame.to_dicts(),self.predict_proba(frame))])
 def to_dict(self):return {'type':'logistic_regression','coefficients':self.coefficients,'intercept':self.intercept,'features':self.features,'threshold':self.threshold}
def regression_metrics(actual,predicted):
 pairs=list(zip(actual,predicted));n=len(pairs);errors=[a-p for a,p in pairs];mae=sum(abs(e) for e in errors)/n;mse=sum(e*e for e in errors)/n;ym=sum(actual)/n;den=sum((a-ym)**2 for a in actual);return {'mae':mae,'mse':mse,'rmse':sqrt(mse),'r2':1-sum(e*e for e in errors)/den if den else 0}
def classification_metrics(actual,predicted):
 tp=sum(a==1 and p==1 for a,p in zip(actual,predicted));tn=sum(a==0 and p==0 for a,p in zip(actual,predicted));fp=sum(a==0 and p==1 for a,p in zip(actual,predicted));fn=sum(a==1 and p==0 for a,p in zip(actual,predicted));n=tp+tn+fp+fn
 return {'accuracy':(tp+tn)/n if n else 0,'precision':tp/(tp+fp) if tp+fp else 0,'recall':tp/(tp+fn) if tp+fn else 0,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0,'confusion_matrix':{'tp':tp,'tn':tn,'fp':fp,'fn':fn}}
def kfold_indices(n,splits=5,shuffle=False,seed=None):
 idx=list(range(n));
 if shuffle:random.Random(seed).shuffle(idx)
 folds=[idx[i::splits] for i in range(splits)];return [([x for j,f in enumerate(folds) if j!=i for x in f],folds[i]) for i in range(splits)]
def save_model(model,path):
 with open(path,'w',encoding='utf-8') as f:json.dump(model.to_dict(),f,indent=2)
def load_model(path):
 with open(path,encoding='utf-8') as f:d=json.load(f)
 cls=LinearRegression if d['type']=='linear_regression' else LogisticRegression;m=cls();m.coefficients=d['coefficients'];m.intercept=d['intercept'];m.features=d['features']
 if hasattr(m,'threshold') and 'threshold' in d:m.threshold=d['threshold']
 return m
class Pipeline:
 def __init__(self,steps):self.steps=list(steps)
 def fit_transform(self,frame):
  out=frame
  for step,args in self.steps:out=step.fit_transform(out,*args) if hasattr(step,'fit_transform') else step(out,*args)
  return out
DataFrame.ml_split=lambda self,test_size=.2,shuffle=False,seed=None:train_test_split(self,test_size,shuffle,seed)
DataFrame.impute=lambda self,columns=None,strategy='mean',fill_value=None:impute(self,columns,strategy,fill_value)
DataFrame.one_hot_encode=lambda self,columns,drop_original=True:one_hot_encode(self,columns,drop_original)

# PeaLang 0.54 production ML, governance, cross-validation and tuning
from datetime import datetime,timezone
import hashlib

class LabelEncoder:
 def __init__(self):self.classes=[]
 def fit(self,values):self.classes=sorted(set(values));return self
 def transform(self,values):
  mapping={v:i for i,v in enumerate(self.classes)};return [mapping[v] for v in values]
 def inverse_transform(self,values):return [self.classes[int(v)] for v in values]
 def fit_transform(self,values):return self.fit(values).transform(values)

def stratified_split(frame,target,test_size=.2,seed=None):
 groups={}
 for r in frame.to_dicts():groups.setdefault(r.get(target),[]).append(r)
 train=[];test=[];rnd=random.Random(seed)
 for rows in groups.values():
  rows=list(rows);rnd.shuffle(rows);n=int(test_size) if isinstance(test_size,int) else max(1,int(round(len(rows)*float(test_size))));n=min(n,len(rows));test.extend(rows[:n]);train.extend(rows[n:])
 rnd.shuffle(train);rnd.shuffle(test);return DataFrame(train),DataFrame(test)

def log_loss(actual,probabilities,eps=1e-15):
 pairs=list(zip(actual,probabilities));
 if not pairs:return None
 return -sum(a*log(max(eps,min(1-eps,p)))+(1-a)*log(max(eps,min(1-eps,1-p))) for a,p in pairs)/len(pairs)
def roc_auc(actual,scores):
 pairs=sorted(zip(scores,actual));pos=sum(actual);neg=len(actual)-pos
 if not pos or not neg:return None
 rank_sum=sum(i+1 for i,(_,a) in enumerate(pairs) if a==1);return (rank_sum-pos*(pos+1)/2)/(pos*neg)

class RidgeRegression(LinearRegression):
 def fit(self,frame,features,target,epochs=2000,learning_rate=.01,alpha=1.0,tolerance=1e-8,patience=20):
  self.features=list(features);X=_features(frame,self.features);y=_target(frame,target);self.coefficients=[0.0]*len(self.features);self.intercept=0.0;n=len(y);best=float('inf');stale=0;self.training_history=[]
  for epoch in range(int(epochs)):
   pred=[self.intercept+_dot(self.coefficients,x) for x in X];errors=[p-a for p,a in zip(pred,y)];loss=sum(e*e for e in errors)/n+alpha*sum(w*w for w in self.coefficients)
   self.training_history.append(loss)
   if best-loss<tolerance:stale+=1
   else:best=loss;stale=0
   if stale>=patience:break
   self.intercept-=learning_rate*2*sum(errors)/n
   for j in range(len(self.coefficients)):self.coefficients[j]-=learning_rate*(2*sum(e*x[j] for e,x in zip(errors,X))/n+2*alpha*self.coefficients[j])
  self.epochs_run=len(self.training_history);return self
 def to_dict(self):return {**super().to_dict(),'type':'ridge_regression','epochs_run':getattr(self,'epochs_run',None)}
class LassoRegression(LinearRegression):
 def fit(self,frame,features,target,epochs=2000,learning_rate=.01,alpha=.01):
  self.features=list(features);X=_features(frame,self.features);y=_target(frame,target);self.coefficients=[0.0]*len(self.features);self.intercept=0.0;n=len(y)
  for _ in range(int(epochs)):
   pred=[self.intercept+_dot(self.coefficients,x) for x in X];errors=[p-a for p,a in zip(pred,y)];self.intercept-=learning_rate*2*sum(errors)/n
   for j,w in enumerate(self.coefficients):self.coefficients[j]-=learning_rate*(2*sum(e*x[j] for e,x in zip(errors,X))/n+alpha*(1 if w>0 else -1 if w<0 else 0))
  return self
 def to_dict(self):return {**super().to_dict(),'type':'lasso_regression'}
class MulticlassLogisticRegression:
 def __init__(self):self.models={};self.classes=[];self.features=[]
 def fit(self,frame,features,target,epochs=1000,learning_rate=.1):
  self.features=list(features);self.classes=sorted({r.get(target) for r in frame.to_dicts()});self.models={}
  for label in self.classes:
   binary=DataFrame([{**r,'__target__':int(r.get(target)==label)} for r in frame.to_dicts()]);self.models[label]=LogisticRegression().fit(binary,self.features,'__target__',epochs,learning_rate)
  return self
 def predict(self,frame,name='prediction'):
  rows=frame.to_dicts();probs={c:self.models[c].predict_proba(frame) for c in self.classes};return DataFrame([{**r,name:max(self.classes,key=lambda c:probs[c][i]),name+'_probabilities':{str(c):probs[c][i] for c in self.classes}} for i,r in enumerate(rows)])

def cross_validate(model_factory,frame,features,target,splits=5,task='regression',shuffle=True,seed=42,fit_options=None):
 rows=frame.to_dicts();scores=[]
 for train_idx,test_idx in kfold_indices(len(rows),splits,shuffle,seed):
  train=DataFrame([rows[i] for i in train_idx]);test=DataFrame([rows[i] for i in test_idx]);m=model_factory();m.fit(train,features,target,**(fit_options or {}))
  actual=[r[target] for r in test.to_dicts()]
  if task=='classification':pred=[r['prediction'] for r in m.predict(test).to_dicts()];scores.append(classification_metrics(actual,pred))
  else:scores.append(regression_metrics(actual,m.predict_rows(test)))
 return scores
def grid_search(model_factory,frame,features,target,param_grid,task='regression',splits=3,metric=None):
 import itertools
 keys=list(param_grid);results=[]
 for vals in itertools.product(*[param_grid[k] for k in keys]):
  params=dict(zip(keys,vals));scores=cross_validate(model_factory,frame,features,target,splits,task,fit_options=params)
  key=metric or ('accuracy' if task=='classification' else 'rmse');value=sum(s[key] for s in scores)/len(scores);results.append({'params':params,'score':value})
 reverse=key not in ('rmse','mse','mae','log_loss');results.sort(key=lambda x:x['score'],reverse=reverse);return {'best_params':results[0]['params'],'best_score':results[0]['score'],'results':results}
def coefficient_report(model):return DataFrame([{'feature':f,'coefficient':w,'absolute_importance':abs(w)} for f,w in sorted(zip(model.features,model.coefficients),key=lambda x:abs(x[1]),reverse=True)])
def prediction_schema(model):return {'required_features':list(model.features or []),'output':'prediction','model_type':model.__class__.__name__}
def validate_prediction_schema(model,frame):
 missing=[c for c in model.features if c not in frame.columns]
 if missing:raise ValueError('Missing prediction features: '+', '.join(missing))
 return True
def model_card(model,name,metrics=None,limitations=None,intended_use=None):
 return {'name':name,'model_type':model.__class__.__name__,'created_at':datetime.now(timezone.utc).isoformat(),'features':list(getattr(model,'features',[]) or []),'metrics':metrics or {},'intended_use':intended_use or '', 'limitations':limitations or [],'schema':prediction_schema(model)}
def reproducibility_manifest(frame,features,target,seed=None,parameters=None):
 payload=json.dumps(frame.to_dicts(),sort_keys=True,default=str).encode();return {'dataset_sha256':hashlib.sha256(payload).hexdigest(),'rows':frame.row_count,'features':list(features),'target':target,'seed':seed,'parameters':parameters or {}}
class ProductionPipeline:
 def __init__(self,transformers,model):self.transformers=list(transformers);self.model=model;self.fitted=[]
 def fit(self,frame,features,target,**model_options):
  data=frame;self.fitted=[]
  for transformer,args in self.transformers:data=transformer.fit_transform(data,*args);self.fitted.append(transformer)
  self.features=list(features);self.target=target;self.model.fit(data,self.features,target,**model_options);return self
 def predict(self,frame,name='prediction'):
  data=frame
  for transformer in self.fitted:data=transformer.transform(data)
  validate_prediction_schema(self.model,data);return self.model.predict(data,name)

DataFrame.stratified_split=lambda self,target,test_size=.2,seed=None:stratified_split(self,target,test_size,seed)

