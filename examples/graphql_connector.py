

from pealang.connectors import connector
gql=connector("graphql","https://api.example.com/graphql")
query="query Users($after:String){users(after:$after){nodes{id name} pageInfo{hasNextPage endCursor}}}"
users=gql.paginate(query,records_path="users.nodes",page_info_path="users.pageInfo")
print(users.to_dicts())


