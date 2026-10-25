


from pealang.cloud_connectors import odata,ODataQuery
c=odata("https://service.example.com/odata/")
rows=c.paginate("Users",ODataQuery(select=["id","name"],filter="active eq true"))



