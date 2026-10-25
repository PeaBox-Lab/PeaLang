

"""PeaLang 0.52 forecasting, evaluation and optional acceleration."""
from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from collections import defaultdict
from .data import DataFrame
from .analytics import mean,stddev

def mae(actual,predicted):
 p=[(a,b) for a,b in zip(actual,predicted) if a is not None and b is not None];return mean(abs(a-b) for a,b in p) if p else None
def mse(actual,predicted):
 p=[(a,b) for a,b in zip(actual,predicted) if a is not None and b is not None];return mean((a-b)**2 for a,b in p) if p else None
def rmse(actual,predicted):
 v=mse(actual,predicted);return sqrt(v) if v is not None else None
def mape(actual,predicted):
 p=[(a,b) for a,b in zip(actual,predicted) if a not in (None,0) and b is not None];return mean(abs((a-b)/a) for a,b in p)*100 if p else None
def evaluate(actual,predicted):return {'mae':mae(actual,predicted),'mse':mse(actual,predicted),'rmse':rmse(actual,predicted),'mape':mape(actual,predicted)}
def train_test_split(frame,test_size=.2):
 rows=frame.to_dicts();n=int(test_size) if isinstance(test_size,int) else max(1,int(round(len(rows)*float(test_size))));n=min(max(n,0),len(rows));return DataFrame(rows[:-n] if n else rows),DataFrame(rows[-n:] if n else [])
def linear_trend(values,periods,confidence=1.96):
 vals=[float(x) for x in values];n=len(vals)
 if n<2:raise ValueError('At least two values are required')
 xs=list(range(n));xm=mean(xs);ym=mean(vals);den=sum((x-xm)**2 for x in xs);slope=sum((x-xm)*(y-ym) for x,y in zip(xs,vals))/den;intercept=ym-slope*xm
 fitted=[intercept+slope*x for x in xs];res=[y-f for y,f in zip(vals,fitted)];sigma=stddev(res) or 0
 forecasts=[]
 for i in range(periods):
  x=n+i;v=intercept+slope*x;forecasts.append({'step':i+1,'forecast':v,'lower':v-confidence*sigma,'upper':v+confidence*sigma})
 return {'slope':slope,'intercept':intercept,'fitted':fitted,'forecast':forecasts}
def moving_average_forecast(values,periods,window=3):
 hist=[float(x) for x in values];out=[]
 if not hist:raise ValueError('Values are required')
 for i in range(periods):v=mean(hist[-int(window):]);hist.append(v);out.append({'step':i+1,'forecast':v})
 return out
def exponential_smoothing(values,periods,alpha=.3):
 if not 0<alpha<=1:raise ValueError('alpha must be in (0, 1]')
 vals=[float(x) for x in values]
 if not vals:raise ValueError('Values are required')
 level=vals[0];fitted=[level]
 for v in vals[1:]:level=alpha*v+(1-alpha)*level;fitted.append(level)
 return {'level':level,'fitted':fitted,'forecast':[{'step':i+1,'forecast':level} for i in range(periods)]}
def seasonal_decompose(values,period):
 vals=[float(x) for x in values];p=int(period)
 if p<2 or len(vals)<p*2:raise ValueError('At least two seasonal periods are required')
 trend=[]
 for i in range(len(vals)):
  lo=max(0,i-p//2);hi=min(len(vals),i+p//2+1);trend.append(mean(vals[lo:hi]))
 det=[v-t for v,t in zip(vals,trend)];season=[mean(det[i::p]) for i in range(p)];seasonal=[season[i%p] for i in range(len(vals))];residual=[v-t-s for v,t,s in zip(vals,trend,seasonal)]
 return {'trend':trend,'seasonal':seasonal,'residual':residual,'pattern':season}
def chart_series(frame,x,y,name=None):return {'name':name or y,'x':[r.get(x) for r in frame.to_dicts()],'y':[r.get(y) for r in frame.to_dicts()]}
def grouped_forecast(frame,by,value,periods,method='linear',**options):
 keys=[by] if isinstance(by,str) else list(by);groups=defaultdict(list)
 for r in frame.to_dicts():groups[tuple(r.get(k) for k in keys)].append(r.get(value))
 out=[]
 for key,vals in groups.items():
  if method=='linear':rows=linear_trend(vals,periods,options.get('confidence',1.96))['forecast']
  elif method=='moving_average':rows=moving_average_forecast(vals,periods,options.get('window',3))
  elif method in ('exp','exponential'):rows=exponential_smoothing(vals,periods,options.get('alpha',.3))['forecast']
  else:raise ValueError('Unsupported forecast method: '+method)
  out.extend([{**dict(zip(keys,key)),**r} for r in rows])
 return DataFrame(out)
def numpy_accelerated_mean(values):
 try:
  import numpy as np
  return float(np.mean(list(values)))
 except ImportError:return mean(values)
@dataclass(frozen=True)
class ForecastBenchmark:
 name:str;points:int;iterations:int;seconds:float;points_per_second:float
def benchmark_forecast(values,iterations=100):
 import time
 vals=list(values);start=time.perf_counter()
 for _ in range(int(iterations)):linear_trend(vals,1)
 elapsed=time.perf_counter()-start;points=len(vals)*int(iterations);return ForecastBenchmark('linear_trend',points,int(iterations),elapsed,points/elapsed if elapsed else float('inf'))
DataFrame.train_test_split=lambda self,test_size=.2:train_test_split(self,test_size)
DataFrame.grouped_forecast=lambda self,by,value,periods,method='linear',**options:grouped_forecast(self,by,value,periods,method,**options)
DataFrame.chart_series=lambda self,x,y,name=None:chart_series(self,x,y,name)


