from pealang.connector_runtime import *
from pealang.enterprise_connectors import *
from pealang.connectors import ConnectorResponse,Transport
class F(Transport):
 def __init__(self,d):self.d=list(d);self.calls=[]
 def request(self,m,u,headers=None,body=None,timeout=30):self.calls.append((m,u,headers));return ConnectorResponse(200,{},self.d.pop(0),u)
def test_cache():
 p=CachedTokenProvider(StaticTokenProvider('x'),10,lambda:0);assert p.token()=='x';p.invalidate();assert p.token()=='x'
def test_profile():assert ConnectorProfile('x','rest','https://x',max_pages=3).config().max_pages==3
def test_health():assert health_check('x',lambda:1).healthy and not health_check('x',lambda:(_ for _ in ()).throw(Exception('e'))).healthy
def test_cert():
 class C:
  def connect(self):pass
  def read(self):pass
 assert certify_matrix(C())['passed']
def test_token_provider():
 f=F([{'id':'me'}]);c=MicrosoftGraphConnector(transport=f).set_token_provider(StaticTokenProvider('abc'));c.me();assert f.calls[0][2]['Authorization']=='Bearer abc'
def test_paging_sp():
 f=F([{'value':[{'id':'1','fields':{'Title':'A'}}],'@odata.nextLink':'next'},{'value':[{'id':'2','fields':{'Title':'B'}}]}]);c=SharePointConnector('t',transport=f);assert c.list_items_all('s','l').row_count==2

