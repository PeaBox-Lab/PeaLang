from __future__ import annotations
import json, os, urllib.request, urllib.error
from dataclasses import dataclass
from typing import Any
from .errors import PeaError

@dataclass
class AIConfig:
    provider:str='mock'; model:str='mock'; base_url:str=''; api_key_env:str=''; timeout:float=30.0

class AIService:
    def __init__(self):self.config=AIConfig()
    def configure(self, options=None):
        o=dict(options or {});self.config=AIConfig(str(o.get('provider','mock')),str(o.get('model','mock')),str(o.get('base_url','')),str(o.get('api_key_env','')),float(o.get('timeout',30)))
        return self.info()
    def info(self):
        c=self.config;return {'provider':c.provider,'model':c.model,'base_url':c.base_url,'api_key_env':c.api_key_env,'timeout':c.timeout}
    def _key(self):
        if not self.config.api_key_env:return None
        value=os.environ.get(self.config.api_key_env)
        if not value:raise PeaError(f"Required AI credential environment variable '{self.config.api_key_env}' is not set")
        return value
    def ask(self,prompt,options=None):
        o=dict(options or {});provider=str(o.get('provider',self.config.provider));model=str(o.get('model',self.config.model));timeout=float(o.get('timeout',self.config.timeout));base=str(o.get('base_url',self.config.base_url))
        if provider=='mock':return {'text':str(prompt),'provider':'mock','model':model,'usage':None,'raw':None}
        if provider=='openai-compatible':
            if not base:raise PeaError('AI base_url is required for openai-compatible provider')
            key=self._key();body={'model':model,'messages':[{'role':'user','content':str(prompt)}]}
            req=urllib.request.Request(base.rstrip('/')+'/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+key} if key else {})},method='POST')
            try:
                with urllib.request.urlopen(req,timeout=timeout) as r:data=json.loads(r.read().decode('utf-8'))
            except Exception as ex:raise PeaError(f'AI request failed: {ex}') from ex
            try:text=data['choices'][0]['message']['content']
            except Exception as ex:raise PeaError('AI response did not contain choices[0].message.content') from ex
            return {'text':text,'provider':provider,'model':model,'usage':data.get('usage'),'raw':data}
        raise PeaError(f"Unknown AI provider '{provider}'")
    def extract(self,text,schema,options=None):
        if self.config.provider=='mock' or (options and options.get('provider')=='mock'):
            # Deterministic local extraction useful for tests and prototyping: dictionary input is projected to schema keys.
            if isinstance(text,dict):return {k:text.get(k) for k in schema.keys()}
            raise PeaError('mock ai.extract expects a dictionary input')
        prompt='Return only valid JSON matching this schema: '+json.dumps(schema)+'\nInput:\n'+str(text)
        result=self.ask(prompt,options);raw=result['text']
        try:data=json.loads(raw)
        except Exception as ex:raise PeaError('AI structured output was not valid JSON') from ex
        return validate_schema(data,schema)

def validate_schema(data,schema):
    if not isinstance(data,dict):raise PeaError('Structured AI output must be a dictionary')
    output={}
    for key,kind in schema.items():
        if key not in data:raise PeaError(f"Structured AI output is missing '{key}'")
        value=data[key];name=str(kind)
        checks={'string':str,'number':(int,float),'boolean':bool,'list':list,'dictionary':dict,'any':object}
        expected=checks.get(name)
        if expected is None:raise PeaError(f"Unknown schema type '{name}' for '{key}'")
        if not isinstance(value,expected) or (name=='number' and isinstance(value,bool)):raise PeaError(f"Field '{key}' must be {name}")
        output[key]=value
    return output

def build_ai_namespace():
    service=AIService()
    return {'configure':service.configure,'info':service.info,'ask':service.ask,'extract':service.extract,'validate':validate_schema},service

