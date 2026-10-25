

from pealang.data import DataFrame
from pealang.ml import LinearRegression
df=DataFrame([{"x":0,"y":1},{"x":1,"y":3},{"x":2,"y":5}])
model=LinearRegression().fit(df,["x"],"y")
print(model.predict(DataFrame([{"x":3}])).to_dicts())


