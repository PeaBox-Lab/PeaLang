

from pathlib import Path
from pealang.agents import AgentRuntime,ToolRegistry
from pealang.agent_governance import AgentPolicy,GovernanceAuditStore,AuditedApprovalGate,approval_request_id

class AI:
    def ask(self,prompt,opts):return {'text':'ok','provider':'test','model':'test'}

def test_persistent_approval_and_execution_audit(tmp_path):
    registry=ToolRegistry();registry.register('deploy',lambda env:'deployed:'+env,'deploy','write')
    runtime=AgentRuntime(AI(),registry);agent=runtime.define('release',tools=['deploy']);store=GovernanceAuditStore(tmp_path/'audit.db')
    gate=AuditedApprovalGate(store,actor='release-manager',approver=lambda request:True)
    result=runtime.tool(agent,'deploy',['staging'],policy=AgentPolicy(approval_required=['deploy']),approval=gate)
    assert result=='deployed:staging'
    rid=approval_request_id('release','deploy',['staging']);assert store.approval(rid)['status']=='approved'
    assert len(store.events())==2
    # Reopen database and prove approval survived process/store recreation.
    reopened=GovernanceAuditStore(tmp_path/'audit.db');assert reopened.approval(rid)['actor']=='release-manager'

def test_denied_approval_persists(tmp_path):
    store=GovernanceAuditStore(tmp_path/'audit.db');gate=AuditedApprovalGate(store,actor='reviewer',approver=lambda request:False)
    assert gate.request({'agent':'a','tool':'delete','args':['x'],'reason':'sensitive'}) is False
    rid=approval_request_id('a','delete',['x']);assert store.approval(rid)['status']=='denied'


