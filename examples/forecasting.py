
from pealang.forecasting import linear_trend,evaluate
model=linear_trend([100,110,120,130],2)
print(model["forecast"])
print(evaluate([120,130],model["fitted"][-2:]))

