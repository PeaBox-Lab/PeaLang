
from pealang.data import DataFrame
df=DataFrame([{"team":"A","score":10},{"team":"A","score":20},{"team":"B","score":30}])
print(df.describe().to_dicts())
print(df.rolling("score",2).to_dicts())
print(df.profile())
