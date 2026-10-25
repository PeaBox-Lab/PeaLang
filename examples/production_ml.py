
from pealang.data import DataFrame
from pealang.ml import StandardScaler,RidgeRegression,ProductionPipeline,model_card
df=DataFrame([{"x":0,"y":1},{"x":1,"y":3},{"x":2,"y":5}])
p=ProductionPipeline([(StandardScaler(),(["x"],))],RidgeRegression()).fit(df,["x"],"y")
print(p.predict(DataFrame([{"x":3}])).to_dicts())
print(model_card(p.model,"demo",limitations=["Baseline model"]))

