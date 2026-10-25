
from pealang.data import DataFrame
from pealang.distributed_compute import distributed
df=DataFrame([{"team":"A","value":2},{"team":"A","value":1}])
query=distributed(df).with_engine("local").sort("value").limit(10)
print(query.explain())
print(query.collect().to_dicts())

