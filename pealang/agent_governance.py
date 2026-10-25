from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Callable
from .errors import PeaError

@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    requires_approval: bool = False
    reason: str = ""

class AgentPolicy:
    """Deterministic policy for agent tool execution."""
    def __init__(self, denied=None, approval_required=None, max_calls=32):
        self.denied=set(denied or [])
        self.approval_required=set(approval_required or [])
        self.max_calls=max(1,int(max_calls))
    def evaluate(self, tool_name:str, call_index:int=0):
        name=str(tool_name)
        if call_index >= self.max_calls:
            return PolicyDecision(False,False,"agent tool-call budget exhausted")
        if name in self.denied:
            return PolicyDecision(False,False,"tool denied by policy")
        if name in self.approval_required:
            return PolicyDecision(False,True,"tool requires approval")
        return PolicyDecision(True,False,"allowed")

class ApprovalGate:
    """Approval adapter. Approver receives a serializable request dictionary."""
    def __init__(self, approver:Callable[[dict],bool] | None=None): self.approver=approver
    def request(self, request:dict):
        return bool(self.approver(request)) if self.approver else False

def plan_tool_call(agent:dict,name:str,args=None,policy:AgentPolicy|None=None,call_index:int=0):
    if not isinstance(agent,dict): raise PeaError("agent must be a dictionary")
    tools=set(agent.get("tools",[])); name=str(name)
    if name not in tools: raise PeaError(f"Tool '{name}' is not permitted for this agent")
    decision=(policy or AgentPolicy()).evaluate(name,call_index)
    return {"tool":name,"args":list(args or []),"decision":asdict(decision),"dry_run":True}
