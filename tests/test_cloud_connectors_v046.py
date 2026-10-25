


import io,json
from types import SimpleNamespace
from pealang.connectors import ConnectorConfig,ConnectorResponse,Transport
from pealang.cloud_connectors import *
class FakeHTTP(Transport):
 def __init__(self,rs):self.rs=list(rs);self.calls=[]
 def request(self,m,u,headers=None,body=None,timeout=30):self.calls.append((m,u));return self.rs.pop(0)
def R(x):return ConnectorResponse(200,{},x,'x')
class MemFile(io.BytesIO):
 def __exit__(self,*a):self.close()
class MemSFTP(SFTPBackend):
 def __init__(self):self.files={'/a.csv':b'id,name\n1,A\n'}
 def listdir(self,p):return [SimpleNamespace(filename=k.split('/')[-1],st_size=len(v),st_mtime=1,st_mode=0) for k,v in self.files.items()]
 def open(self,p,m='rb'):
  if 'r' in m:return MemFile(self.files[p])
  backend=self
  class W(MemFile):
   def close(self):backend.files[p]=self.getvalue();super().close()
  return W()
 def mkdir(self,p):pass
 def remove(self,p):del self.files[p]
 def rename(self,a,b):self.files[b]=self.files.pop(a)
def test_odata_query_options():
 f=FakeHTTP([R({'value':[{'id':1}]})]);c=ODataConnector(ConnectorConfig('http://x/'),f);q=ODataQuery(select=['id','name'],filter='active eq true',top=10,count=True);assert c.dataframe('Users',q).row_count==1 and '%24select=id%2Cname' in f.calls[0][1]
def test_odata_pagination():
 f=FakeHTTP([R({'value':[{'id':1}],'@odata.nextLink':'next'}),R({'value':[{'id':2}]})]);c=ODataConnector(ConnectorConfig('http://x/',max_pages=3),f);assert c.paginate('Users').row_count==2
def test_odata_count():
 c=ODataConnector(ConnectorConfig('http://x/'),FakeHTTP([R({'@odata.count':12,'value':[]})]));assert c.count('Users')==12
def test_sftp_list_read_write():
 b=MemSFTP();c=SFTPConnector(SFTPConfig('x'),b);assert c.list('/').row_count==1 and c.read_text('/a.csv').startswith('id');c.write_text('/b.txt','hello');assert c.read_text('/b.txt')=='hello'
def test_sftp_csv_frame():assert SFTPConnector(SFTPConfig('x'),MemSFTP()).read_csv_frame('/a.csv').to_dicts()==[{'id':'1','name':'A'}]
def test_sftp_json_frame():
 b=MemSFTP();b.files['/x.json']=json.dumps({'items':[{'id':2}]}).encode();assert SFTPConnector(SFTPConfig('x'),b).read_json_frame('/x.json','items').row_count==1
def test_sftp_rename_remove():
 b=MemSFTP();c=SFTPConnector(SFTPConfig('x'),b);c.rename('/a.csv','/b.csv');assert '/b.csv' in b.files;c.remove('/b.csv');assert not b.files
def test_registry_contains_odata():assert 'odata' in CONNECTORS.names()



