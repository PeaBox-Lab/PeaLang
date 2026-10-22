"""FastAPI integration for PeaLang extensions. FastAPI is an optional dependency."""
from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
import time
from typing import Any,Callable
from .type_system import SemanticAnalyzer
from .vm_embedding import VMRuntime
from .embedding import RuntimeOptions,PeaPermissionError,PeaResourceLimitError
from .errors import PeaError

@dataclass
class ExtensionStatus:
 name:str;path:str;loaded:bool=False;error:str|None=None;loaded_at:float|None=None;mtime:float|None=None
@dataclass
class RouteSpec:
 path:str;method:str;extension:str;function:str;status_code:int=200;tags:list[str]=field(default_factory=lambda:['PeaLang'])
class PeaExtensionRegistry:
 def __init__(self,runtime=None,semantic=True,hot_reload=False):
  self.runtime=runtime or VMRuntime(RuntimeOptions());self.semantic=semantic;self.hot_reload=hot_reload;self.modules={};self.statuses={}
 def load(self,name,path):
  p=Path(path).resolve();status=ExtensionStatus(name,str(p));self.statuses[name]=status
  try:
   source=p.read_text(encoding='utf-8')
   if self.semantic:
    result=SemanticAnalyzer().analyze(source,str(p));errors=[x for x in result.diagnostics if x.severity=='error']
    if errors:raise PeaError('Semantic validation failed: '+'; '.join(str(x) for x in errors[:10]))
   self.modules[name]=self.runtime.load(source,str(p));status.loaded=True;status.loaded_at=time.time();status.mtime=p.stat().st_mtime
  except Exception as e:status.error=str(e);raise
  return self.modules[name]
 def get(self,name):
  if name not in self.modules:raise KeyError(f"Unknown extension '{name}'")
  if self.hot_reload:
   st=self.statuses[name];p=Path(st.path)
   if p.stat().st_mtime!=(st.mtime or 0):self.load(name,p)
  return self.modules[name]
 def call(self,name,function,*args,**kwargs):return self.get(name).call(function,*args,**kwargs)
 def status(self):return [vars(x) for x in self.statuses.values()]

def _fastapi():
 try:
  from fastapi import APIRouter,HTTPException,Request
  from fastapi.responses import JSONResponse
  return APIRouter,HTTPException,Request,JSONResponse
 except ImportError as e:raise RuntimeError('FastAPI integration requires: pip install pealang[fastapi]') from e

def map_exception(exc):
 APIRouter,HTTPException,Request,JSONResponse=_fastapi()
 if isinstance(exc,PeaPermissionError):return HTTPException(status_code=403,detail={'code':'PEA_PERMISSION_DENIED','message':str(exc)})
 if isinstance(exc,PeaResourceLimitError):return HTTPException(status_code=429,detail={'code':'PEA_RESOURCE_LIMIT','message':str(exc)})
 if isinstance(exc,(PeaError,ValueError,KeyError)):return HTTPException(status_code=400,detail={'code':'PEA_EXTENSION_ERROR','message':str(exc)})
 return HTTPException(status_code=500,detail={'code':'PEA_INTERNAL_ERROR','message':'Extension execution failed'})

class PeaRouter:
 def __init__(self,registry:PeaExtensionRegistry,prefix='/extensions'):
  APIRouter,_,_,_=_fastapi();self.registry=registry;self.router=APIRouter(prefix=prefix);self.routes=[]
 def add(self,path,extension,function,method='POST',status_code=200,tags=None):
  spec=RouteSpec(path,method.upper(),extension,function,status_code,tags or ['PeaLang']);self.routes.append(spec)
  async def endpoint(payload:dict):
   try:return self.registry.call(extension,function,payload)
   except Exception as e:raise map_exception(e)
  endpoint.__name__=f'pea_{extension}_{function}_{len(self.routes)}'
  self.router.add_api_route(path,endpoint,methods=[spec.method],status_code=status_code,tags=spec.tags,summary=f'PeaLang: {extension}.{function}',openapi_extra={'x-pealang-extension':extension,'x-pealang-function':function})
  return self
 def include_status(self,path='/_status'):
  async def status():return {'extensions':self.registry.status()}
  self.router.add_api_route(path,status,methods=['GET'],tags=['PeaLang'],summary='PeaLang extension status');return self

def create_validation_dependency(registry,extension,function):
 async def dependency(payload:dict):
  try:
   result=registry.call(extension,function,payload)
   if result is True or result is None:return payload
   if isinstance(result,list) and not result:return payload
   raise map_exception(ValueError(str(result)))
  except Exception as e:
   if getattr(e,'status_code',None):raise
   raise map_exception(e)
 return dependency

def install_exception_handlers(app):
 _,_,_,JSONResponse=_fastapi()
 @app.exception_handler(PeaPermissionError)
 async def permission_handler(request,exc):return JSONResponse(status_code=403,content={'code':'PEA_PERMISSION_DENIED','message':str(exc)})
 @app.exception_handler(PeaResourceLimitError)
 async def budget_handler(request,exc):return JSONResponse(status_code=429,content={'code':'PEA_RESOURCE_LIMIT','message':str(exc)})
 return app
