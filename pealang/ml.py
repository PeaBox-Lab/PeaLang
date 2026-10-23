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
