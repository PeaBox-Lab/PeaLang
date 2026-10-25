import pytest
from pealang.agent_safety_conformance import *
def test_isolation_approval_replay():
 p=ToolIsolationPolicy({"deploy"});t=ToolCapability("d",frozenset({"deploy"}),True);l=ApprovalLedger();q={"x":1};l.issue("a",q,"r");e=SafeAgentExecutor(p,l);assert e.execute("1",t,{"deploy"},q,lambda:42,"a")==42;assert agent_safety_gate(e)["gate"]=="PASS"
 with pytest.raises(PermissionError):e.execute("2",t,{"deploy"},q,lambda:42,"a")
def test_budget():
 b=BudgetTracker(ExecutionBudget(max_steps=1));b.charge()
 with pytest.raises(RuntimeError):b.charge()
