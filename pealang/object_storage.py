# AUDIT-CLOSURE: intentional interface contract; concrete backends must override the methods documented in docs/project/INTERFACE_COMPLETENESS_0991.md.



"""PeaLang 0.47 cloud object storage connectors."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import csv,io,json
from .data import DataFrame

class ObjectStorageError(RuntimeError): pass
@dataclass(frozen=True)
class ObjectInfo:
    key:str
    size:int|None=None
    modified:object=None
    etag:str|None=None

class ObjectStorageConnector:
    kind='object-storage'
    def list(self,prefix='')->DataFrame: raise NotImplementedError
    def read_bytes(self,key): raise NotImplementedError
    def write_bytes(self,key,data,content_type=None): raise NotImplementedError
    def delete(self,key): raise NotImplementedError
    def read_text(self,key,encoding='utf-8'): return self.read_bytes(key).decode(encoding)
    def write_text(self,key,text,encoding='utf-8',content_type='text/plain'): return self.write_bytes(key,text.encode(encoding),content_type)
    def upload(self,local_path,key): return self.write_bytes(key,Path(local_path).read_bytes())
    def download(self,key,local_path): Path(local_path).write_bytes(self.read_bytes(key)); return str(local_path)
    def read_json_frame(self,key,records_path=None):
        value=json.loads(self.read_text(key))
        for part in str(records_path).split('.') if records_path else []: value=value.get(part) if isinstance(value,dict) else None
        if value is None:return DataFrame([])
        if not isinstance(value,list):value=[value]
        return DataFrame([x if isinstance(x,dict) else {'value':x} for x in value])
    def read_csv_frame(self,key,delimiter=','): return DataFrame(list(csv.DictReader(io.StringIO(self.read_text(key)),delimiter=delimiter)))
    def read_parquet_frame(self,key):
        try: import pyarrow.parquet as pq
        except ImportError as exc: raise RuntimeError('Parquet ingestion requires optional dependency: pyarrow') from exc
        table=pq.read_table(io.BytesIO(self.read_bytes(key))); return DataFrame(table.to_pylist())

class S3Connector(ObjectStorageConnector):
    kind='s3'
    def __init__(self,bucket,client=None,region=None,endpoint_url=None,**client_options):
        self.bucket=bucket
        if client is None:
            try: import boto3
            except ImportError as exc: raise RuntimeError('S3 support requires optional dependency: boto3') from exc
            client=boto3.client('s3',region_name=region,endpoint_url=endpoint_url,**client_options)
        self.client=client
    def list(self,prefix=''):
        token=None;out=[]
        while True:
            kw={'Bucket':self.bucket,'Prefix':prefix};
            if token:kw['ContinuationToken']=token
            r=self.client.list_objects_v2(**kw)
            for x in r.get('Contents',[]):out.append({'key':x['Key'],'size':x.get('Size'),'modified':x.get('LastModified'),'etag':str(x.get('ETag','')).strip('"')})
            if not r.get('IsTruncated'):break
            token=r.get('NextContinuationToken')
        return DataFrame(out)
    def read_bytes(self,key):return self.client.get_object(Bucket=self.bucket,Key=key)['Body'].read()
    def write_bytes(self,key,data,content_type=None):
        kw={'Bucket':self.bucket,'Key':key,'Body':data};
        if content_type:kw['ContentType']=content_type
        self.client.put_object(**kw);return key
    def delete(self,key):self.client.delete_object(Bucket=self.bucket,Key=key)
    def presign(self,key,expires=3600):return self.client.generate_presigned_url('get_object',Params={'Bucket':self.bucket,'Key':key},ExpiresIn=int(expires))

class AzureBlobConnector(ObjectStorageConnector):
    kind='azure-blob'
    def __init__(self,container,service_client=None,connection_string=None,account_url=None,credential=None):
        self.container_name=container
        if service_client is None:
            try: from azure.storage.blob import BlobServiceClient
            except ImportError as exc: raise RuntimeError('Azure Blob support requires optional dependency: azure-storage-blob') from exc
            service_client=BlobServiceClient.from_connection_string(connection_string) if connection_string else BlobServiceClient(account_url=account_url,credential=credential)
        self.container=service_client.get_container_client(container)
    def list(self,prefix=''): return DataFrame([{'key':x.name,'size':getattr(x,'size',None),'modified':getattr(x,'last_modified',None),'etag':getattr(x,'etag',None)} for x in self.container.list_blobs(name_starts_with=prefix)])
    def read_bytes(self,key):return self.container.download_blob(key).readall()
    def write_bytes(self,key,data,content_type=None):self.container.upload_blob(key,data,overwrite=True);return key
    def delete(self,key):self.container.delete_blob(key)

class ADLSConnector(ObjectStorageConnector):
    kind='adls'
    def __init__(self,file_system,service_client=None,account_url=None,credential=None):
        if service_client is None:
            try: from azure.storage.filedatalake import DataLakeServiceClient
            except ImportError as exc: raise RuntimeError('ADLS support requires optional dependency: azure-storage-file-datalake') from exc
            service_client=DataLakeServiceClient(account_url=account_url,credential=credential)
        self.fs=service_client.get_file_system_client(file_system)
    def list(self,prefix=''):return DataFrame([{'key':x.name,'size':getattr(x,'content_length',None),'modified':getattr(x,'last_modified',None),'etag':getattr(x,'etag',None)} for x in self.fs.get_paths(path=prefix or None) if not getattr(x,'is_directory',False)])
    def read_bytes(self,key):return self.fs.get_file_client(key).download_file().readall()
    def write_bytes(self,key,data,content_type=None):self.fs.get_file_client(key).upload_data(data,overwrite=True);return key
    def delete(self,key):self.fs.get_file_client(key).delete_file()

class GCSConnector(ObjectStorageConnector):
    kind='gcs'
    def __init__(self,bucket,client=None,project=None,credentials=None):
        if client is None:
            try: from google.cloud import storage
            except ImportError as exc: raise RuntimeError('GCS support requires optional dependency: google-cloud-storage') from exc
            client=storage.Client(project=project,credentials=credentials)
        self.bucket=client.bucket(bucket)
    def list(self,prefix=''):return DataFrame([{'key':x.name,'size':getattr(x,'size',None),'modified':getattr(x,'updated',None),'etag':getattr(x,'etag',None)} for x in self.bucket.list_blobs(prefix=prefix)])
    def read_bytes(self,key):return self.bucket.blob(key).download_as_bytes()
    def write_bytes(self,key,data,content_type=None):self.bucket.blob(key).upload_from_string(data,content_type=content_type);return key
    def delete(self,key):self.bucket.blob(key).delete()

def s3(bucket,**options):return S3Connector(bucket,**options)
def azure_blob(container,**options):return AzureBlobConnector(container,**options)
def adls(file_system,**options):return ADLSConnector(file_system,**options)
def gcs(bucket,**options):return GCSConnector(bucket,**options)



