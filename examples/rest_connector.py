from pealang.connectors import connector,bearer
api=connector("rest","https://api.example.com",headers=bearer("TOKEN"))
users=api.dataframe("/users",records_path="items")
print(users.to_dicts())
