



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

# v0.75 durable governance and audit
@dataclass(frozen=True)
class AuditEvent:
    event_type:str
    agent:str|None
    tool:str|None
    decision:str
    actor:str|None=None
    reason:str=""
    timestamp:str=""
    details:dict[str,Any]|None=None

class GovernanceAuditStore:
    """Append-only SQLite audit and approval store."""
    def __init__(self,path=":memory:"):
        import sqlite3
        self.db=sqlite3.connect(str(path))
        self.db.execute("create table if not exists audit(id integer primary key autoincrement,event_type text,agent text,tool text,decision text,actor text,reason text,timestamp text,details text)")
        self.db.execute("create table if not exists approvals(id integer primary key autoincrement,request_id text unique,agent text,tool text,args text,status text,actor text,reason text,created_at text,resolved_at text)")
        self.db.commit()
    def record(self,event:AuditEvent):
        import json
        from datetime import datetime,timezone
        stamp=event.timestamp or datetime.now(timezone.utc).isoformat()
        self.db.execute("insert into audit(event_type,agent,tool,decision,actor,reason,timestamp,details) values(?,?,?,?,?,?,?,?)",(event.event_type,event.agent,event.tool,event.decision,event.actor,event.reason,stamp,json.dumps(event.details or {},default=str)));self.db.commit()
    def request_approval(self,request_id,agent,tool,args):
        import json
        from datetime import datetime,timezone
        self.db.execute("insert or ignore into approvals(request_id,agent,tool,args,status,created_at) values(?,?,?,?,?,?)",(request_id,agent,tool,json.dumps(list(args or []),default=str),"pending",datetime.now(timezone.utc).isoformat()));self.db.commit();return request_id
    def resolve(self,request_id,approved,actor,reason):
        from datetime import datetime,timezone
        status="approved" if approved else "denied"
        self.db.execute("update approvals set status=?,actor=?,reason=?,resolved_at=? where request_id=?",(status,actor,reason,datetime.now(timezone.utc).isoformat(),request_id));self.db.commit();return status
    def approval(self,request_id):
        row=self.db.execute("select request_id,agent,tool,args,status,actor,reason,created_at,resolved_at from approvals where request_id=?",(request_id,)).fetchone()
        if not row:return None
        keys=("request_id","agent","tool","args","status","actor","reason","created_at","resolved_at");return dict(zip(keys,row))
    def events(self):
        rows=self.db.execute("select event_type,agent,tool,decision,actor,reason,timestamp,details from audit order by id").fetchall();return rows

def approval_request_id(agent,tool,args):
    import hashlib,json
    raw=json.dumps([agent,tool,list(args or [])],sort_keys=True,default=str).encode();return hashlib.sha256(raw).hexdigest()

class AuditedApprovalGate(ApprovalGate):
    def __init__(self,store:GovernanceAuditStore,actor=None,approver=None):super().__init__(approver);self.store=store;self.actor=actor
    def request(self,request):
        rid=approval_request_id(request.get("agent"),request.get("tool"),request.get("args"));self.store.request_approval(rid,request.get("agent"),request.get("tool"),request.get("args"))
        existing=self.store.approval(rid)
        if existing and existing["status"] in {"approved","denied"}:return existing["status"]=="approved"
        approved=super().request(request)
        if self.approver is not None:self.store.resolve(rid,approved,self.actor or "host",request.get("reason", ""))
        self.store.record(AuditEvent("approval",request.get("agent"),request.get("tool"),"approved" if approved else "denied",self.actor,request.get("reason",""),details={"request_id":rid}))
        return approved




