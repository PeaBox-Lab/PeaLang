
import pytest
from pealang.agents import AgentRuntime, ToolRegistry
from pealang.agent_governance import AgentPolicy
from pealang.errors import PeaError

class AI:
    def ask(self,prompt,opts): return {'text':'ok','provider':'test','model':'test'}

def runtime():
    tools=ToolRegistry(); tools.register('read',lambda x:x,'read','safe'); tools.register('write',lambda x:'w:'+x,'write','write')
    return AgentRuntime(AI(),tools)

def test_dry_run_does_not_execute():
    r=runtime(); a=r.define('a',tools=['read'])
    p=r.tool(a,'read',['x'],dry_run=True)
    assert p['dry_run'] and p['decision']['allowed'] and p['tool']=='read'

def test_denied_policy_blocks_call():
    r=runtime(); a=r.define('a',tools=['write'])
    with pytest.raises(PeaError,match='blocked'): r.tool(a,'write',['x'],policy=AgentPolicy(denied=['write']))

def test_approval_gate():
    r=runtime(); a=r.define('a',tools=['write']); policy=AgentPolicy(approval_required=['write'])
    assert r.tool(a,'write',['x'],policy=policy,approval=lambda req:req['tool']=='write')=='w:x'
    with pytest.raises(PeaError,match='approval denied'): r.tool(a,'write',['x'],policy=policy)

def test_call_budget():
    r=runtime(); a=r.define('a',tools=['read'])
    with pytest.raises(PeaError,match='budget'): r.tool(a,'read',['x'],policy=AgentPolicy(max_calls=1),call_index=1)

