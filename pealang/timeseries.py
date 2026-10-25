

"""PeaLang 0.51 grouped analytics and time-series operations."""
from __future__ import annotations
from datetime import datetime,date,timedelta
from collections import defaultdict
from math import isnan
from .data import DataFrame
from .analytics import mean,stddev,describe

def parse_datetime(value,formats=None):
 if value is None or isinstance(value,datetime):return value
 if isinstance(value,date):return datetime.combine(value,datetime.min.time())
 text=str(value)
 for fmt in list(formats or [])+['%Y-%m-%dT%H:%M:%S','%Y-%m-%d %H:%M:%S','%Y-%m-%d','%d/%m/%Y','%m/%d/%Y']:
  try:return datetime.strptime(text,fmt)
  except ValueError:pass
 try:return datetime.fromisoformat(text.replace('Z','+00:00'))
 except ValueError:raise ValueError('Unable to parse datetime: '+text)
def with_datetime(frame,column,name=None,formats=None):return DataFrame([{**r,(name or column):parse_datetime(r.get(column),formats)} for r in frame.to_dicts()])
def date_parts(frame,column,prefix=None):
 p=prefix or column;out=[]
 for r in frame.to_dicts():
  d=parse_datetime(r.get(column));parts={} if d is None else {p+'_year':d.year,p+'_quarter':(d.month-1)//3+1,p+'_month':d.month,p+'_week':d.isocalendar().week,p+'_day':d.day,p+'_weekday':d.weekday(),p+'_hour':d.hour,p+'_minute':d.minute}
  out.append({**r,**parts})
 return DataFrame(out)
def _bucket(d,freq):
 d=parse_datetime(d)
 if freq in ('minute','min'):return d.replace(second=0,microsecond=0)
 if freq in ('hour','h'):return d.replace(minute=0,second=0,microsecond=0)
 if freq in ('day','d'):return d.replace(hour=0,minute=0,second=0,microsecond=0)
 if freq in ('week','w'):return (d-timedelta(days=d.weekday())).replace(hour=0,minute=0,second=0,microsecond=0)
 if freq in ('month','m'):return d.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
 if freq in ('quarter','q'):return d.replace(month=((d.month-1)//3)*3+1,day=1,hour=0,minute=0,second=0,microsecond=0)
 if freq in ('year','y'):return d.replace(month=1,day=1,hour=0,minute=0,second=0,microsecond=0)
 raise ValueError('Unsupported frequency: '+str(freq))
def resample(frame,time_column,freq,value_column=None,op='count',name=None):
 groups=defaultdict(list)
 for r in frame.to_dicts():
  if r.get(time_column) is not None:groups[_bucket(r[time_column],freq)].append(r)
 out=[]
 for period,rows in sorted(groups.items()):
  vals=[r.get(value_column) for r in rows if value_column and r.get(value_column) is not None]
  if op=='count':v=len(rows)
  elif op=='sum':v=sum(vals)
  elif op in ('mean','avg'):v=mean(vals)
  elif op=='min':v=min(vals) if vals else None
  elif op=='max':v=max(vals) if vals else None
  else:raise ValueError('Unsupported resample operation: '+op)
  out.append({time_column:period,(name or (op+'_'+(value_column or 'rows'))):v})
 return DataFrame(out)
def lag(frame,column,periods=1,name=None,default=None):
 rows=frame.to_dicts();n=int(periods);return DataFrame([{**r,(name or 'lag_'+column):(rows[i-n].get(column) if i>=n else default)} for i,r in enumerate(rows)])
def lead(frame,column,periods=1,name=None,default=None):
 rows=frame.to_dicts();n=int(periods);return DataFrame([{**r,(name or 'lead_'+column):(rows[i+n].get(column) if i+n<len(rows) else default)} for i,r in enumerate(rows)])
def difference(frame,column,periods=1,name=None):
 rows=frame.to_dicts();n=int(periods);out=[]
 for i,r in enumerate(rows):
  prev=rows[i-n].get(column) if i>=n else None;cur=r.get(column);v=None if prev is None or cur is None else cur-prev;out.append({**r,(name or 'diff_'+column):v})
 return DataFrame(out)
def pct_change(frame,column,periods=1,name=None):
 rows=frame.to_dicts();n=int(periods);out=[]
 for i,r in enumerate(rows):
  prev=rows[i-n].get(column) if i>=n else None;cur=r.get(column);v=None if prev in (None,0) or cur is None else (cur-prev)/prev;out.append({**r,(name or 'pct_change_'+column):v})
 return DataFrame(out)
def expanding(frame,column,op='mean',min_periods=1,name=None):
 vals=[];out=[]
 for r in frame.to_dicts():
  if r.get(column) is not None:vals.append(r[column])
  v=None
  if len(vals)>=min_periods:
   if op=='mean':v=mean(vals)
   elif op=='sum':v=sum(vals)
   elif op=='min':v=min(vals)
   elif op=='max':v=max(vals)
   elif op=='std':v=stddev(vals)
   else:raise ValueError('Unsupported expanding operation: '+op)
  out.append({**r,(name or 'expanding_'+op+'_'+column):v})
 return DataFrame(out)
def ewm(frame,column,alpha=None,span=None,name=None):
 if alpha is None:
  if span is None:raise ValueError('alpha or span is required')
  alpha=2/(float(span)+1)
 if not 0<alpha<=1:raise ValueError('alpha must be in (0, 1]')
 state=None;out=[]
 for r in frame.to_dicts():
  v=r.get(column)
  if v is not None:state=v if state is None else alpha*v+(1-alpha)*state
  out.append({**r,(name or 'ewm_'+column):state})
 return DataFrame(out)
def interpolate(frame,column,method='linear',name=None):
 rows=frame.to_dicts();vals=[r.get(column) for r in rows];result=list(vals)
 if method!='linear':raise ValueError('Only linear interpolation is supported')
 for i,v in enumerate(vals):
  if v is not None:continue
  left=next((j for j in range(i-1,-1,-1) if vals[j] is not None),None);right=next((j for j in range(i+1,len(vals)) if vals[j] is not None),None)
  if left is not None and right is not None:result[i]=vals[left]+(vals[right]-vals[left])*(i-left)/(right-left)
 for i,r in enumerate(rows):rows[i]={**r,(name or column):result[i]}
 return DataFrame(rows)
def grouped_describe(frame,by,columns=None):
 keys=[by] if isinstance(by,str) else list(by);groups=defaultdict(list)
 for r in frame.to_dicts():groups[tuple(r.get(k) for k in keys)].append(r)
 out=[]
 for key,rows in groups.items():
  for stat in describe(DataFrame(rows),columns).to_dicts():out.append({**dict(zip(keys,key)),**stat})
 return DataFrame(out)
def grouped_rolling(frame,by,column,window,op='mean',name=None):
 keys=[by] if isinstance(by,str) else list(by);states=defaultdict(list);out=[]
 for r in frame.to_dicts():
  k=tuple(r.get(x) for x in keys);states[k].append(r.get(column));vals=[x for x in states[k][-int(window):] if x is not None]
  if op=='mean':v=mean(vals)
  elif op=='sum':v=sum(vals)
  elif op=='min':v=min(vals)
  elif op=='max':v=max(vals)
  else:raise ValueError('Unsupported grouped rolling operation: '+op)
  out.append({**r,(name or 'group_rolling_'+op+'_'+column):v})
 return DataFrame(out)
DataFrame.with_datetime=lambda self,column,name=None,formats=None:with_datetime(self,column,name,formats)
DataFrame.date_parts=lambda self,column,prefix=None:date_parts(self,column,prefix)
DataFrame.resample=lambda self,time_column,freq,value_column=None,op='count',name=None:resample(self,time_column,freq,value_column,op,name)
DataFrame.lag=lambda self,column,periods=1,name=None,default=None:lag(self,column,periods,name,default)
DataFrame.lead=lambda self,column,periods=1,name=None,default=None:lead(self,column,periods,name,default)
DataFrame.difference=lambda self,column,periods=1,name=None:difference(self,column,periods,name)
DataFrame.pct_change=lambda self,column,periods=1,name=None:pct_change(self,column,periods,name)
DataFrame.expanding=lambda self,column,op='mean',min_periods=1,name=None:expanding(self,column,op,min_periods,name)
DataFrame.ewm=lambda self,column,alpha=None,span=None,name=None:ewm(self,column,alpha,span,name)
DataFrame.interpolate=lambda self,column,method='linear',name=None:interpolate(self,column,method,name)
DataFrame.grouped_describe=lambda self,by,columns=None:grouped_describe(self,by,columns)
DataFrame.grouped_rolling=lambda self,by,column,window,op='mean',name=None:grouped_rolling(self,by,column,window,op,name)


