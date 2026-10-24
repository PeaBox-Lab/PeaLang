
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .errors import PeaError

@dataclass
class ToolSpec:
    name:str; handler:Any; description:str=''; permission:str='safe'

class ToolRegistry:
    def __init__(self,invoke=None):self.tools={};self.invoke=invoke
    def register(self,name,handler,description='',permission='safe'):
        if not callable(handler) and not (hasattr(handler,'params') and hasattr(handler,'body')):raise PeaError('Tool handler must be callable')
        self.tools[str(name)]=ToolSpec(str(name),handler,str(description),str(permission));return self.describe(name)
    def list(self):return sorted(self.tools)
    def describe(self,name):
        t=self.tools.get(str(name))
        if not t:raise PeaError(f"Tool '{name}' is not registered")
        return {'name':t.name,'description':t.description,'permission':t.permission}
    def call(self,name,args=None,allowed=None):
        t=self.tools.get(str(name))
        if not t:raise PeaError(f"Tool '{name}' is not registered")
        allowed=set(allowed or [])
        if t.name not in allowed:raise PeaError(f"Tool '{t.name}' is not permitted for this agent")
        values=list(args or [])
        try:
            if callable(t.handler):return t.handler(*values)
            if self.invoke:return self.invoke(t.handler,values)
            raise PeaError('Tool handler cannot be invoked')
        except PeaError:raise
        except Exception as ex:raise PeaError(f"Tool '{t.name}' failed: {ex}") from ex

class AgentRuntime:
    def __init__(self,ai_service,tools):self.ai=ai_service;self.tools=tools
    def define(self,name,instruction='',tools=None,model=None):
        return {'name':str(name),'instruction':str(instruction),'tools':list(tools or []),'model':model}
    def run(self,agent,input_value,options=None):
        if not isinstance(agent,dict):raise PeaError('agent.run expects an agent dictionary')
        opts=dict(options or {});prompt=str(agent.get('instruction',''))
        if prompt:prompt+='\n\n'
        prompt+='Input:\n'+str(input_value)
        aiopts={}
        if agent.get('model'):aiopts['model']=agent['model']
        aiopts.update(opts.get('ai',{}))
        answer=self.ai.ask(prompt,aiopts)
        return {'agent':agent.get('name'),'text':answer['text'],'provider':answer['provider'],'model':answer['model'],'tools':list(agent.get('tools',[]))}
    def tool(self,agent,name,args=None):
        if not isinstance(agent,dict):raise PeaError('agent.tool expects an agent dictionary')
        return self.tools.call(name,args,agent.get('tools',[]))
