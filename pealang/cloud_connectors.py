
"""PeaLang 0.46 cloud connectors: OData and SFTP."""
from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
from typing import Any
import io,json,urllib.parse
from .data import DataFrame
from .connectors import BaseConnector,ConnectorConfig,ConnectorRegistry,RESTConnector,REGISTRY as CONNECTORS,_dig,_records

class ODataError(RuntimeError):pass
class SFTPError(RuntimeError):pass

@dataclass
class ODataQuery:
    select:list[str]=field(default_factory=list)
    filter:str|None=None
    expand:list[str]=field(default_factory=list)
    orderby:list[str]=field(default_factory=list)
    top:int|None=None
    skip:int|None=None
    count:bool|None=None
    search:str|None=None
    custom:dict[str,Any]=field(default_factory=dict)
    def params(self):
        p={}
        if self.select:p['$select']=','.join(self.select)
        if self.filter:p['$filter']=self.filter
        if self.expand:p['$expand']=','.join(self.expand)
        if self.orderby:p['$orderby']=','.join(self.orderby)
        if self.top is not None:p['$top']=int(self.top)
        if self.skip is not None:p['$skip']=int(self.skip)
        if self.count is not None:p['$count']='true' if self.count else 'false'
        if self.search is not None:p['$search']=self.search
        return {**p,**self.custom}

class ODataConnector(RESTConnector):
    kind='odata'
    def query(self,entity_set,query:ODataQuery|None=None,params=None):
        merged={**((query or ODataQuery()).params()),**(params or {})}
        return self.get(entity_set,merged)
    def dataframe(self,entity_set,query:ODataQuery|None=None,params=None):
        data=self.query(entity_set,query,params);return DataFrame(_records(data,'value' if isinstance(data,dict) and 'value' in data else None))
    def paginate(self,entity_set,query:ODataQuery|None=None,params=None):
        data=self.query(entity_set,query,params);out=_records(data,'value' if isinstance(data,dict) else None)
        for _ in range(max(0,self.config.max_pages-1)):
            nxt=data.get('@odata.nextLink') if isinstance(data,dict) else None
            if not nxt:break
            data=self.get(nxt);out.extend(_records(data,'value' if isinstance(data,dict) else None))
        return DataFrame(out)
    def count(self,entity_set,query:ODataQuery|None=None):
        data=self.query(entity_set,query or ODataQuery(count=True,top=0));return data.get('@odata.count') if isinstance(data,dict) else None
    def metadata(self):return self.get('$metadata',headers={'Accept':'application/xml'})

@dataclass
class SFTPConfig:
    host:str
    port:int=22
    username:str|None=None
    password:str|None=None
    private_key:str|None=None
    private_key_passphrase:str|None=None
    known_hosts:str|None=None
    timeout:float=30.0
    allow_unknown_host:bool=False

class SFTPBackend:
    def listdir(self,path):raise NotImplementedError
    def stat(self,path):raise NotImplementedError
    def open(self,path,mode='rb'):raise NotImplementedError
    def mkdir(self,path):raise NotImplementedError
    def remove(self,path):raise NotImplementedError
    def rename(self,source,target):raise NotImplementedError
    def close(self):pass

class ParamikoSFTPBackend(SFTPBackend):
    def __init__(self,config:SFTPConfig):
        try:import paramiko
        except ImportError as exc:raise RuntimeError('SFTP support requires optional dependency: paramiko') from exc
        client=paramiko.SSHClient()
        if config.known_hosts:client.load_host_keys(config.known_hosts)
        else:client.load_system_host_keys()
        if config.allow_unknown_host:client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:client.set_missing_host_key_policy(paramiko.RejectPolicy())
        kwargs={'hostname':config.host,'port':config.port,'username':config.username,'password':config.password,'timeout':config.timeout,'look_for_keys':config.private_key is None}
        if config.private_key:kwargs['key_filename']=config.private_key
        if config.private_key_passphrase:kwargs['passphrase']=config.private_key_passphrase
        client.connect(**kwargs);self.client=client;self.sftp=client.open_sftp()
    def listdir(self,path):return self.sftp.listdir_attr(path)
    def stat(self,path):return self.sftp.stat(path)
    def open(self,path,mode='rb'):return self.sftp.open(path,mode)
    def mkdir(self,path):return self.sftp.mkdir(path)
    def remove(self,path):return self.sftp.remove(path)
    def rename(self,source,target):return self.sftp.rename(source,target)
    def close(self):self.sftp.close();self.client.close()

class SFTPConnector:
    kind='sftp'
    def __init__(self,config:SFTPConfig,backend:SFTPBackend|None=None):self.config=config;self.backend=backend or ParamikoSFTPBackend(config)
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def close(self):self.backend.close()
    def list(self,path='.'):
        out=[]
        for x in self.backend.listdir(path):out.append({'name':getattr(x,'filename',str(x)),'size':getattr(x,'st_size',None),'modified':getattr(x,'st_mtime',None),'mode':getattr(x,'st_mode',None)})
        return DataFrame(out)
    def read_bytes(self,path):
        with self.backend.open(path,'rb') as f:return f.read()
    def read_text(self,path,encoding='utf-8'):return self.read_bytes(path).decode(encoding)
    def write_bytes(self,path,data):
        with self.backend.open(path,'wb') as f:f.write(data)
        return path
    def write_text(self,path,text,encoding='utf-8'):return self.write_bytes(path,text.encode(encoding))
    def upload(self,local_path,remote_path):return self.write_bytes(remote_path,Path(local_path).read_bytes())
    def download(self,remote_path,local_path):Path(local_path).write_bytes(self.read_bytes(remote_path));return str(local_path)
    def remove(self,path):self.backend.remove(path)
    def rename(self,source,target):self.backend.rename(source,target)
    def mkdir(self,path):self.backend.mkdir(path)
    def read_json(self,path):return json.loads(self.read_text(path))
    def read_json_frame(self,path,records_path=None):return DataFrame(_records(self.read_json(path),records_path))
    def read_csv_frame(self,path,delimiter=','):
        import csv
        return DataFrame(list(csv.DictReader(io.StringIO(self.read_text(path)),delimiter=delimiter)))

CONNECTORS.register('odata',ODataConnector,replace=True)

def odata(base_url,headers=None,**options):return ODataConnector(ConnectorConfig(base_url,headers or {},**options))
def sftp(host,**options):return SFTPConnector(SFTPConfig(host,**options))

