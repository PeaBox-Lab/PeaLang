
"""PeaLang 0.48 enterprise connectors, secrets and certification."""
from __future__ import annotations
from dataclasses import dataclass,field,asdict
import json,os,urllib.parse
from .data import DataFrame
from .connectors import ConnectorConfig,RESTConnector,_records

class SecretError(RuntimeError):pass
class SecretProvider:
    name='base'
    def get(self,name):raise NotImplementedError
class EnvironmentSecrets(SecretProvider):
    name='environment'
    def __init__(self,prefix=''):self.prefix=prefix
    def get(self,name):
        key=self.prefix+str(name);value=os.environ.get(key)
        if value is None:raise SecretError('Secret not found: '+key)
        return value
class MappingSecrets(SecretProvider):
    name='mapping'
    def __init__(self,values):self.values=dict(values)
    def get(self,name):
        if name not in self.values:raise SecretError('Secret not found: '+str(name))
        return self.values[name]
class AzureKeyVaultSecrets(SecretProvider):
    name='azure-key-vault'
    def __init__(self,vault_url,client=None,credential=None):
        if client is None:
            try:
                from azure.identity import DefaultAzureCredential
                from azure.keyvault.secrets import SecretClient
            except ImportError as exc:raise RuntimeError('Azure Key Vault requires azure-identity and azure-keyvault-secrets') from exc
            client=SecretClient(vault_url=vault_url,credential=credential or DefaultAzureCredential())
        self.client=client
    def get(self,name):return self.client.get_secret(name).value
class AWSSecretsManager(SecretProvider):
    name='aws-secrets-manager'
    def __init__(self,client=None,region=None):
        if client is None:
            try:import boto3
            except ImportError as exc:raise RuntimeError('AWS Secrets Manager requires boto3') from exc
            client=boto3.client('secretsmanager',region_name=region)
        self.client=client
    def get(self,name):
        r=self.client.get_secret_value(SecretId=name);return r.get('SecretString') if 'SecretString' in r else r.get('SecretBinary')
@dataclass(frozen=True)
class SecretRef:
    provider:str
    name:str
class SecretRegistry:
    def __init__(self):self.providers={}
    def register(self,provider):self.providers[provider.name]=provider;return self
    def resolve(self,ref):
        if isinstance(ref,str):return ref
        if ref.provider not in self.providers:raise SecretError('Unknown secret provider: '+ref.provider)
        return self.providers[ref.provider].get(ref.name)
SECRETS=SecretRegistry().register(EnvironmentSecrets())

@dataclass(frozen=True)
class ConnectorCapability:
    name:str
    operations:tuple[str,...]
    auth:tuple[str,...]=()
    pagination:bool=False
    dataframe:bool=False
@dataclass
class CertificationResult:
    connector:str
    passed:bool
    checks:dict[str,bool]=field(default_factory=dict)
def certify(name,connector,capability):
    checks={op:hasattr(connector,op) for op in capability.operations};checks['capability_name']=bool(capability.name);return CertificationResult(name,all(checks.values()),checks)
CAPABILITIES={
 'rest':ConnectorCapability('rest',('get','post','dataframe'),('bearer','api-key'),True,True),
 'graphql':ConnectorCapability('graphql',('execute','dataframe'),('bearer','api-key'),True,True),
 'odata':ConnectorCapability('odata',('query','dataframe','paginate'),('bearer','oauth2'),True,True),
 'sftp':ConnectorCapability('sftp',('list','read_bytes','write_bytes'),('password','ssh-key'),False,True),
 'sharepoint':ConnectorCapability('sharepoint',('sites','drives','list_items','download'),('oauth2',),True,True),
}

class MicrosoftGraphConnector(RESTConnector):
    kind='microsoft-graph'
    def __init__(self,token=None,config=None,transport=None):
        config=config or ConnectorConfig('https://graph.microsoft.com/v1.0',headers={})
        if token:config.headers={**config.headers,'Authorization':'Bearer '+token}
        super().__init__(config,transport)
    def me(self):return self.get('me')
    def sites(self,search=None):return self.get('sites',{'search':search} if search else None)
    def site(self,site_id):return self.get('sites/'+site_id)
    def drives(self,site_id):return self.get(f'sites/{site_id}/drives')
    def drive_items(self,drive_id,item_id='root',children=True):return self.get(f'drives/{drive_id}/items/{item_id}/children' if children else f'drives/{drive_id}/items/{item_id}')
    def download(self,drive_id,item_id):return self.get(f'drives/{drive_id}/items/{item_id}/content')
    def list_items(self,site_id,list_id,expand_fields=True):return self.get(f'sites/{site_id}/lists/{list_id}/items',{'$expand':'fields'} if expand_fields else None)
    def list_items_frame(self,site_id,list_id):
        data=self.list_items(site_id,list_id,True);rows=[]
        for x in data.get('value',[]):rows.append({'id':x.get('id'),**x.get('fields',{})})
        return DataFrame(rows)
class SharePointConnector(MicrosoftGraphConnector):
    kind='sharepoint'
    def resolve_site(self,hostname,path):return self.get('sites/'+hostname+':/'+path.strip('/'))

def microsoft_graph(token=None,**kwargs):return MicrosoftGraphConnector(token,**kwargs)
def sharepoint(token=None,**kwargs):return SharePointConnector(token,**kwargs)
def _set_tp(self,p):self.token_provider=p;return self
def _headers49(self,extra=None):
 h=RESTConnector._headers(self,extra);p=getattr(self,'token_provider',None)
 if p:h['Authorization']='Bearer '+p.token()
 return h
def _paged(self,path,params=None):
 data=self.get(path,params);out=list(data.get('value',[])) if isinstance(data,dict) else []
 for _ in range(max(0,self.config.max_pages-1)):
  nxt=data.get('@odata.nextLink') if isinstance(data,dict) else None
  if not nxt:break
  data=self.get(nxt);out.extend(data.get('value',[]))
 return out
MicrosoftGraphConnector.set_token_provider=_set_tp;MicrosoftGraphConnector._headers=_headers49;MicrosoftGraphConnector.paged_values=_paged
def _all(self,site_id,list_id):
 return DataFrame([{'id':x.get('id'),**x.get('fields',{})} for x in self.paged_values(f'sites/{site_id}/lists/{list_id}/items',{'$expand':'fields'})])
SharePointConnector.list_items_all=_all
