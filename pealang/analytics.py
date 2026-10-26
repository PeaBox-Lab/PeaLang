



"""PeaLang 0.50 dependency-light DataFrame analytics and profiling."""
from __future__ import annotations
from collections import Counter,defaultdict
from dataclasses import dataclass
from math import sqrt
from .data import DataFrame

def _values(frame,column,numeric=False):
 values=[r.get(column) for r in frame.to_dicts() if r.get(column) is not None]
 return [float(v) for v in values if isinstance(v,(int,float)) and not isinstance(v,bool)] if numeric else values
def mean(values):
 v=list(values);return sum(v)/len(v) if v else None
def median(values):return quantile(values,.5)
def mode(values):
 c=Counter(values)
 if not c:return None
 m=max(c.values());return next(x for x in values if c[x]==m)
def quantile(values,q):
 v=sorted(values)
 if not v:return None
 if not 0<=q<=1:raise ValueError('q must be between 0 and 1')
 pos=(len(v)-1)*q;lo=int(pos);hi=min(lo+1,len(v)-1);return v[lo]+(v[hi]-v[lo])*(pos-lo)
def variance(values,sample=True):
 v=list(values);n=len(v)
 if n<(2 if sample else 1):return None
 m=mean(v);return sum((x-m)**2 for x in v)/(n-1 if sample else n)
def stddev(values,sample=True):
 v=variance(values,sample);return sqrt(v) if v is not None else None
def covariance(x,y,sample=True):
 pairs=[(a,b) for a,b in zip(x,y) if a is not None and b is not None];n=len(pairs)
 if n<(2 if sample else 1):return None
 mx=mean(a for a,_ in pairs);my=mean(b for _,b in pairs);return sum((a-mx)*(b-my) for a,b in pairs)/(n-1 if sample else n)
def correlation(x,y):
 sx=stddev(x);sy=stddev(y)
 return None if not sx or not sy else covariance(x,y)/(sx*sy)
def describe(frame,columns=None,percentiles=(.25,.5,.75)):
 cols=list(columns or frame.columns);out=[]
 for c in cols:
  raw=_values(frame,c);nums=_values(frame,c,True);row={'column':c,'count':len(raw),'missing':frame.row_count-len(raw),'unique':len(set(map(repr,raw)))}
  if nums:row.update({'mean':mean(nums),'std':stddev(nums),'min':min(nums),'max':max(nums),**{f'p{int(p*100)}':quantile(nums,p) for p in percentiles}})
  else:row.update({'mean':None,'std':None,'min':None,'max':None,**{f'p{int(p*100)}':None for p in percentiles}})
  out.append(row)
 return DataFrame(out)
def frequencies(frame,column,normalize=False):
 vals=_values(frame,column);c=Counter(vals);total=len(vals);return DataFrame([{'value':k,'count':v,'frequency':v/total if normalize and total else None} for k,v in c.most_common()])
def crosstab(frame,row,column,normalize=False):
 rows=frame.to_dicts();rvals=[];cvals=[]
 for x in rows:
  if x.get(row) not in rvals:rvals.append(x.get(row))
  if x.get(column) not in cvals:cvals.append(x.get(column))
 out=[]
 for rv in rvals:
  item={row:rv};subset=[x for x in rows if x.get(row)==rv];den=len(subset)
  for cv in cvals:
   n=sum(1 for x in subset if x.get(column)==cv);item[str(cv)]=n/den if normalize and den else n
  out.append(item)
 return DataFrame(out)
def rank(frame,column,descending=False,method='dense',name='rank'):
 vals=sorted({r.get(column) for r in frame.to_dicts() if r.get(column) is not None},reverse=descending);mapping={v:i+1 for i,v in enumerate(vals)}
 return DataFrame([{**r,name:mapping.get(r.get(column))} for r in frame.to_dicts()])
def cumulative(frame,column,op='sum',name=None):
 out=[];acc=None
 for r in frame.to_dicts():
  v=r.get(column)
  if v is not None:
   if acc is None:acc=v
   elif op=='sum':acc+=v
   elif op=='min':acc=min(acc,v)
   elif op=='max':acc=max(acc,v)
   else:raise ValueError('Unknown cumulative operation: '+op)
  out.append({**r,(name or 'cum_'+op+'_'+column):acc})
 return DataFrame(out)
def rolling(frame,column,window,op='mean',name=None,min_periods=1):
 vals=[];out=[]
 for r in frame.to_dicts():
  vals.append(r.get(column));current=[x for x in vals[-int(window):] if x is not None];value=None
  if len(current)>=min_periods:
   if op=='mean':value=mean(current)
   elif op=='sum':value=sum(current)
   elif op=='min':value=min(current)
   elif op=='max':value=max(current)
   elif op=='std':value=stddev(current)
   else:raise ValueError('Unknown rolling operation: '+op)
  out.append({**r,(name or f'rolling_{op}_{column}'):value})
 return DataFrame(out)
def outliers_iqr(frame,column,factor=1.5):
 vals=_values(frame,column,True);q1=quantile(vals,.25);q3=quantile(vals,.75)
 if q1 is None:return DataFrame([])
 lo=q1-factor*(q3-q1);hi=q3+factor*(q3-q1);return DataFrame([r for r in frame.to_dicts() if isinstance(r.get(column),(int,float)) and (r[column]<lo or r[column]>hi)])
def profile(frame):
 summaries=describe(frame).to_dicts();return {'rows':frame.row_count,'columns':len(frame.columns),'duplicate_rows':frame.row_count-frame.distinct().row_count,'missing_cells':sum(x['missing'] for x in summaries),'column_profiles':summaries}
def correlation_matrix(frame,columns=None):
 cols=list(columns or [c for c in frame.columns if _values(frame,c,True)]);rows=frame.to_dicts();out=[]
 for a in cols:
  item={'column':a}
  for b in cols:
   pairs=[(r.get(a),r.get(b)) for r in rows if isinstance(r.get(a),(int,float)) and isinstance(r.get(b),(int,float))];item[b]=correlation([x for x,_ in pairs],[y for _,y in pairs])
  out.append(item)
 return DataFrame(out)
DataFrame.describe=lambda self,columns=None,percentiles=(.25,.5,.75):describe(self,columns,percentiles)
DataFrame.frequencies=lambda self,column,normalize=False:frequencies(self,column,normalize)
DataFrame.crosstab=lambda self,row,column,normalize=False:crosstab(self,row,column,normalize)
DataFrame.rank=lambda self,column,descending=False,method='dense',name='rank':rank(self,column,descending,method,name)
DataFrame.cumulative=lambda self,column,op='sum',name=None:cumulative(self,column,op,name)
DataFrame.rolling=lambda self,column,window,op='mean',name=None,min_periods=1:rolling(self,column,window,op,name,min_periods)
DataFrame.outliers_iqr=lambda self,column,factor=1.5:outliers_iqr(self,column,factor)
DataFrame.profile=lambda self:profile(self)
DataFrame.correlation_matrix=lambda self,columns=None:correlation_matrix(self,columns)




