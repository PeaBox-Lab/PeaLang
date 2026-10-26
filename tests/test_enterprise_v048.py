



import os
from pealang.enterprise_connectors import *
from pealang.connectors import ConnectorResponse,Transport,ConnectorConfig
class Fake(Transport):
 def __init__(self,data):self.data=list(data);self.calls=[]
 def request(self,m,u,headers=None,body=None,timeout=30):self.calls.append((m,u,headers));return ConnectorResponse(200,{},self.data.pop(0),u)
def test_env_secret(monkeypatch):monkeypatch.setenv('PEA_X','v');assert EnvironmentSecrets('PEA_').get('X')=='v'
def test_mapping_secret():assert MappingSecrets({'x':'y'}).get('x')=='y'
def test_registry_ref():assert SecretRegistry().register(MappingSecrets({'x':'y'})).resolve(SecretRef('mapping','x'))=='y'
def test_graph_sites():
 f=Fake([{'value':[{'id':'1'}]}]);c=MicrosoftGraphConnector('t',transport=f);assert c.sites()['value'][0]['id']=='1' and f.calls[0][2]['Authorization']=='Bearer t'
def test_sharepoint_list_frame():
 f=Fake([{'value':[{'id':'1','fields':{'Title':'A'}}]}]);c=SharePointConnector('t',transport=f);assert c.list_items_frame('s','l').to_dicts()==[{'id':'1','Title':'A'}]
def test_sharepoint_resolve():
 f=Fake([{'id':'s'}]);assert SharePointConnector('t',transport=f).resolve_site('contoso.sharepoint.com','sites/hr')['id']=='s'
def test_capabilities():assert CAPABILITIES['sharepoint'].dataframe and 'download' in CAPABILITIES['sharepoint'].operations
def test_certification():
 f=Fake([]);c=SharePointConnector('t',transport=f);r=certify('sharepoint',c,CAPABILITIES['sharepoint']);assert r.passed
def test_aws_secret_fake():
 class C:
  def get_secret_value(self,SecretId):return {'SecretString':'s'}
 assert AWSSecretsManager(C()).get('x')=='s'
def test_azure_secret_fake():
 class V:value='s'
 class C:
  def get_secret(self,n):return V()
 assert AzureKeyVaultSecrets('x',client=C()).get('x')=='s'




