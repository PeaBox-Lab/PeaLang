

"""PeaLang 0.45 Connector SDK with REST and GraphQL connectors."""
from __future__ import annotations
from dataclasses import dataclass,field
from typing import Any,Callable
import json,time,urllib.parse,urllib.request,urllib.error
from .data import DataFrame

class ConnectorError(RuntimeError):pass
class AuthenticationError(ConnectorError):pass
class RateLimitError(ConnectorError):pass
class ResponseError(ConnectorError):pass

@dataclass
class ConnectorConfig:
    base_url:str
    headers:dict[str,str]=field(default_factory=dict)
    timeout:float=30.0
    retries:int=2
    backoff:float=0.25
    verify_tls:bool=True
    max_pages:int=100
    user_agent:str='PeaLang-ConnectorSDK/0.45.0'

@dataclass
class ConnectorResponse:
    status:int
    headers:dict[str,str]
    data:Any
    url:str

class Transport:
    def request(self,method,url,headers=None,body=None,timeout=30.0)->ConnectorResponse:raise NotImplementedError

class UrllibTransport(Transport):
    def request(self,method,url,headers=None,body=None,timeout=30.0):
        req=urllib.request.Request(url,data=body,headers=headers or {},method=method.upper())
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r:
                raw=r.read();ctype=r.headers.get('Content-Type','');data=json.loads(raw.decode()) if raw and ('json' in ctype or raw[:1] in (b'{',b'[')) else raw.decode(errors='replace')
                return ConnectorResponse(r.status,dict(r.headers.items()),data,r.geturl())
        except urllib.error.HTTPError as e:
            raw=e.read();
            try:data=json.loads(raw.decode())
            except Exception:data=raw.decode(errors='replace')
            return ConnectorResponse(e.code,dict(e.headers.items()),data,url)

class BaseConnector:
    kind='base'
    def __init__(self,config:ConnectorConfig,transport:Transport|None=None):self.config=config;self.transport=transport or UrllibTransport()
    def _headers(self,extra=None):return {'Accept':'application/json','User-Agent':self.config.user_agent,**self.config.headers,**(extra or {})}
    def _request(self,method,url,headers=None,payload=None):
        body=None if payload is None else json.dumps(payload).encode();attempts=max(1,self.config.retries+1)
        for attempt in range(attempts):
            response=self.transport.request(method,url,self._headers(headers),body,self.config.timeout)
            if response.status in (401,403):raise AuthenticationError(f'Authentication failed: HTTP {response.status}')
            if response.status==429:
                if attempt+1<attempts:time.sleep(self.config.backoff*(2**attempt));continue
                raise RateLimitError('Rate limit exceeded: HTTP 429')
            if response.status>=500 and attempt+1<attempts:time.sleep(self.config.backoff*(2**attempt));continue
            if response.status>=400:raise ResponseError(f'HTTP {response.status}: {response.data}')
            return response
        raise ResponseError('Connector request failed')
    def test_connection(self):return True

class RESTConnector(BaseConnector):
    kind='rest'
    def request(self,method='GET',path='',params=None,json_body=None,headers=None):
        url=urllib.parse.urljoin(self.config.base_url.rstrip('/')+'/',path.lstrip('/'))
        if params:url+='&' if '?' in url else '?';url+=urllib.parse.urlencode(params,doseq=True)
        h={'Content-Type':'application/json',**(headers or {})} if json_body is not None else headers
        return self._request(method,url,h,json_body).data
    def get(self,path='',params=None,headers=None):return self.request('GET',path,params,None,headers)
    def post(self,path='',json_body=None,params=None,headers=None):return self.request('POST',path,params,json_body,headers)
    def dataframe(self,path='',params=None,records_path=None):return DataFrame(_records(self.get(path,params),records_path))
    def paginate(self,path='',params=None,items_path=None,next_path='next',page_param='page',start_page=1):
        params=dict(params or {});out=[];page=start_page;next_url=None
        for _ in range(self.config.max_pages):
            data=self.get(next_url or path,None if next_url else {**params,page_param:page});out.extend(_records(data,items_path))
            nxt=_dig(data,next_path) if isinstance(data,dict) else None
            if not nxt:break
            next_url=str(nxt);page+=1
        return DataFrame(out)

class GraphQLConnector(BaseConnector):
    kind='graphql'
    def execute(self,query,variables=None,operation_name=None,headers=None):
        payload={'query':query,'variables':variables or {}}
        if operation_name:payload['operationName']=operation_name
        result=self._request('POST',self.config.base_url,{'Content-Type':'application/json',**(headers or {})},payload).data
        if not isinstance(result,dict):raise ResponseError('Invalid GraphQL response')
        if result.get('errors'):raise ResponseError('GraphQL errors: '+json.dumps(result['errors']))
        return result.get('data')
    def dataframe(self,query,variables=None,records_path=None,operation_name=None):return DataFrame(_records(self.execute(query,variables,operation_name),records_path))
    def paginate(self,query,variables=None,records_path=None,page_info_path=None,cursor_variable='after'):
        variables=dict(variables or {});out=[]
        for _ in range(self.config.max_pages):
            data=self.execute(query,variables);out.extend(_records(data,records_path));info=_dig(data,page_info_path) if page_info_path else None
            if not info or not info.get('hasNextPage'):break
            variables[cursor_variable]=info.get('endCursor')
        return DataFrame(out)

class ConnectorRegistry:
    def __init__(self):self._factories={}
    def register(self,name,factory,replace=False):
        key=name.lower()
        if key in self._factories and not replace:raise ValueError('Connector already registered: '+key)
        self._factories[key]=factory;return factory
    def create(self,name,config,**kwargs):
        key=name.lower()
        if key not in self._factories:raise KeyError('Unknown connector: '+key)
        return self._factories[key](config,**kwargs)
    def names(self):return sorted(self._factories)
REGISTRY=ConnectorRegistry();REGISTRY.register('rest',RESTConnector);REGISTRY.register('graphql',GraphQLConnector)

def connector(name,base_url,headers=None,**options):return REGISTRY.create(name,ConnectorConfig(base_url,headers or {},**options))
def bearer(token):return {'Authorization':'Bearer '+token}
def api_key(name,value):return {name:value}
def _dig(value,path):
    if path in (None,''):return value
    cur=value
    for part in str(path).split('.'):
        if isinstance(cur,dict):cur=cur.get(part)
        elif isinstance(cur,list) and part.isdigit():cur=cur[int(part)]
        else:return None
    return cur
def _records(data,path=None):
    value=_dig(data,path)
    if value is None:return []
    if isinstance(value,list):return [x if isinstance(x,dict) else {'value':x} for x in value]
    if isinstance(value,dict):return [value]
    return [{'value':value}]


