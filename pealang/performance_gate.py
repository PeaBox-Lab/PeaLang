from dataclasses import dataclass
from .benchmark import benchmark_source
@dataclass(frozen=True)
class RegressionGate:
 max_regression_pct:float=10.0
def compare_benchmark(baseline,current,max_regression_pct=10.0,metric='median_ms'):
 b=float(baseline[metric]);c=float(current[metric]);pct=0.0 if b==0 and c==0 else (float('inf') if b==0 else ((c-b)/b)*100)
 return {'metric':metric,'baseline':b,'current':c,'regression_pct':pct,'threshold_pct':float(max_regression_pct),'ok':pct<=max_regression_pct}
def measure(source,iterations=20):return benchmark_source(source,iterations)

