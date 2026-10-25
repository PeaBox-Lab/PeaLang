
from pealang.data import DataFrame
from pealang.ml import LinearRegression
from pealang.mlops import create_model_bundle,audited_predict
model=LinearRegression([2],1,["x"])
create_model_bundle(model,"bundle",model_id="demo",version="1.0.0")
print(audited_predict(model,DataFrame([{"x":2}]))[0].to_dicts())

