import importlib.util
import pytest
from pealang import RuntimeOptions,VMRuntime,PeaPermissionError
from pealang.fastapi import PeaExtensionRegistry

def test_registry_load_and_call(tmp_path):
 p=tmp_path/'rules.pea';p.write_text('function add(x){return x+1}\nexport add');r=PeaExtensionRegistry();r.load('rules',p);assert r.call('rules','add',2)==3
def test_registry_status(tmp_path):
 p=tmp_path/'rules.pea';p.write_text('function f(){return 1}\nexport f');r=PeaExtensionRegistry();r.load('x',p);s=r.status()[0];assert s['loaded'] and s['name']=='x'
def test_semantic_rejection(tmp_path):
 p=tmp_path/'bad.pea';p.write_text('function f()->Int {\n return "bad"\n}\nexport f');r=PeaExtensionRegistry()
 with pytest.raises(Exception,match='Semantic validation'):r.load('bad',p)
def test_registry_permissions(tmp_path):
 p=tmp_path/'r.pea';p.write_text('function work(){return hr.secret()}\nexport work');runtime=VMRuntime().register_function('hr.secret',lambda:1,'hr.secret');r=PeaExtensionRegistry(runtime);r.load('x',p)
 with pytest.raises(PeaPermissionError):r.call('x','work')
def test_hot_reload(tmp_path):
 import os,time
 p=tmp_path/'r.pea';p.write_text('function f(){return 1}\nexport f');r=PeaExtensionRegistry(hot_reload=True);r.load('x',p);assert r.call('x','f')==1;time.sleep(.02);p.write_text('function f(){return 2}\nexport f');os.utime(p,None);assert r.call('x','f')==2
@pytest.mark.skipif(importlib.util.find_spec('fastapi') is None,reason='fastapi optional')
def test_router_openapi(tmp_path):
 from fastapi import FastAPI
 p=tmp_path/'r.pea';p.write_text('function f(x){return x}\nexport f');r=PeaExtensionRegistry();r.load('x',p);from pealang.fastapi import PeaRouter;router=PeaRouter(r).add('/f','x','f');app=FastAPI();app.include_router(router.router);op=app.openapi();assert op['paths']['/extensions/f']['post']['x-pealang-extension']=='x'

