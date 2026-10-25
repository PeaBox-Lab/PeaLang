

import io,datetime
from pealang.object_storage import *
class Body:
 def __init__(self,b):self.b=b
 def read(self):return self.b
class S3:
 def __init__(self):self.d={'a/x.csv':b'id,name\n1,A\n'}
 def list_objects_v2(self,**kw):return {'Contents':[{'Key':k,'Size':len(v)} for k,v in self.d.items() if k.startswith(kw.get('Prefix',''))],'IsTruncated':False}
 def get_object(self,**kw):return {'Body':Body(self.d[kw['Key']])}
 def put_object(self,**kw):self.d[kw['Key']]=kw['Body']
 def delete_object(self,**kw):del self.d[kw['Key']]
 def generate_presigned_url(self,*a,**kw):return 'signed'
class Blob:
 def __init__(self,n,b):self.name=n;self.size=len(b);self.last_modified=None;self.etag='e'
class DL:
 def __init__(self,b):self.b=b
 def readall(self):return self.b
class Container:
 def __init__(self):self.d={'x':b'1'}
 def list_blobs(self,name_starts_with=''):return [Blob(k,v) for k,v in self.d.items() if k.startswith(name_starts_with)]
 def download_blob(self,k):return DL(self.d[k])
 def upload_blob(self,k,d,overwrite=True):self.d[k]=d
 def delete_blob(self,k):del self.d[k]
class AzureSvc:
 def __init__(self):self.c=Container()
 def get_container_client(self,n):return self.c
class GBlob:
 def __init__(self,b,k):self.b=b;self.name=k;self.size=len(b.d.get(k,b''));self.updated=None;self.etag='e'
 def download_as_bytes(self):return self.b.d[self.name]
 def upload_from_string(self,d,content_type=None):self.b.d[self.name]=d
 def delete(self):del self.b.d[self.name]
class Bucket:
 def __init__(self):self.d={'a':b'1'}
 def list_blobs(self,prefix=''):return [GBlob(self,k) for k in self.d if k.startswith(prefix)]
 def blob(self,k):return GBlob(self,k)
class GClient:
 def __init__(self):self.b=Bucket()
 def bucket(self,n):return self.b
def test_s3_crud_csv():
 c=S3Connector('b',client=S3());assert c.list('a').row_count==1 and c.read_csv_frame('a/x.csv').row_count==1;c.write_text('b.txt','hi');assert c.read_text('b.txt')=='hi';c.delete('b.txt')
def test_s3_presign():assert S3Connector('b',client=S3()).presign('x')=='signed'
def test_azure_crud():
 c=AzureBlobConnector('c',service_client=AzureSvc());assert c.list().row_count==1;c.write_text('y','z');assert c.read_text('y')=='z';c.delete('y')
def test_gcs_crud():
 gc=GClient();c=GCSConnector('b',client=gc);assert c.list().row_count==1;c.write_bytes('x',b'2');assert c.read_bytes('x')==b'2';c.delete('x')
def test_json_frame():
 s=S3();s.d['j.json']=b'{"items":[{"id":2}]}' ;assert S3Connector('b',client=s).read_json_frame('j.json','items').row_count==1


