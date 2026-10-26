



import pytest
from pealang.connectors import *
class Fake(Transport):
 def __init__(self,responses):self.responses=list(responses);self.calls=[]
 def request(self,method,url,headers=None,body=None,timeout=30):self.calls.append((method,url,headers,body));return self.responses.pop(0)
def R(data,status=200):return ConnectorResponse(status,{'Content-Type':'application/json'},data,'http://x')
def test_registry():assert {'graphql','rest'} <= set(REGISTRY.names())
def test_rest_get_params():
 f=Fake([R([{'id':1}])]);c=RESTConnector(ConnectorConfig('http://api/'),f);assert c.dataframe('users',{'active':True}).to_dicts()==[{'id':1}] and 'active=True' in f.calls[0][1]
def test_rest_post():
 f=Fake([R({'id':2})]);c=RESTConnector(ConnectorConfig('http://api'),f);assert c.post('/users',{'name':'A'})['id']==2 and b'"name": "A"' in f.calls[0][3]
def test_rest_pagination():
 f=Fake([R({'items':[{'id':1}],'next':'p2'}),R({'items':[{'id':2}],'next':None})]);c=RESTConnector(ConnectorConfig('http://api/',max_pages=5),f);assert c.paginate('users',items_path='items').row_count==2
def test_graphql_execute():
 f=Fake([R({'data':{'user':{'id':1}}})]);c=GraphQLConnector(ConnectorConfig('http://gql'),f);assert c.execute('query X { user { id } }')['user']['id']==1
def test_graphql_errors():
 c=GraphQLConnector(ConnectorConfig('http://gql'),Fake([R({'errors':[{'message':'bad'}]})]));
 with pytest.raises(ResponseError):c.execute('{x}')
def test_graphql_dataframe():
 c=GraphQLConnector(ConnectorConfig('http://gql'),Fake([R({'data':{'users':[{'id':1}]}})]));assert c.dataframe('{users{id}}',records_path='users').row_count==1
def test_graphql_cursor_pagination():
 a={'data':{'users':{'nodes':[{'id':1}],'pageInfo':{'hasNextPage':True,'endCursor':'C'}}}};b={'data':{'users':{'nodes':[{'id':2}],'pageInfo':{'hasNextPage':False,'endCursor':None}}}}
 c=GraphQLConnector(ConnectorConfig('http://gql'),Fake([R(a),R(b)]));assert c.paginate('query',records_path='users.nodes',page_info_path='users.pageInfo').row_count==2
def test_auth_failure():
 c=RESTConnector(ConnectorConfig('http://api',retries=0),Fake([R({},401)]));
 with pytest.raises(AuthenticationError):c.get('x')
def test_rate_limit():
 c=RESTConnector(ConnectorConfig('http://api',retries=0),Fake([R({},429)]));
 with pytest.raises(RateLimitError):c.get('x')
def test_retry_server_error():
 f=Fake([R({},500),R({'ok':True})]);c=RESTConnector(ConnectorConfig('http://api',retries=1,backoff=0),f);assert c.get('x')['ok']
def test_helpers():assert bearer('x')['Authorization']=='Bearer x' and api_key('X-Key','y')['X-Key']=='y'




