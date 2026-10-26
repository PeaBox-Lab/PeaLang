



from dataclasses import dataclass,asdict
import hashlib,json,time
@dataclass(frozen=True)
class ToolCapability:name:str;capabilities:frozenset[str];requires_approval:bool=False
class ToolIsolationPolicy:
 def __init__(self,allowed=()):self.allowed=frozenset(allowed)
 def authorize(self,t,req):req=frozenset(req);return req<=t.capabilities and req<=self.allowed
class ApprovalLedger:
 def __init__(self):self.records={};self.consumed=set()
 def digest(self,x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 def issue(self,i,req,reviewer,decision="approved"):self.records[i]=(self.digest(req),reviewer,decision);return i
 def validate(self,i,req):
  if i in self.consumed:return False
  x=self.records.get(i)
  if not x or x[2]!="approved" or x[0]!=self.digest(req):return False
  self.consumed.add(i);return True
@dataclass(frozen=True)
class ExecutionBudget:max_steps:int=20;max_tool_calls:int=10;max_cost_units:float=100
class BudgetTracker:
 def __init__(self,b=ExecutionBudget()):self.b=b;self.steps=0;self.tools=0;self.cost=0
 def charge(self,cost=1):
  self.steps+=1;self.tools+=1;self.cost+=cost
  if self.steps>self.b.max_steps or self.tools>self.b.max_tool_calls or self.cost>self.b.max_cost_units:raise RuntimeError("budget exceeded")
class AgentAuditTrail:
 def __init__(self):self.steps=[]
 def append(self,a,t,s,req):
  prev=self.steps[-1]["digest"] if self.steps else "GENESIS";x={"action":a,"tool":t,"status":s,"request":hashlib.sha256(json.dumps(req,sort_keys=True).encode()).hexdigest(),"previous":prev};x["digest"]=hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest();self.steps.append(x)
 def verify(self):
  prev="GENESIS"
  for x in self.steps:
   d=x["digest"];y={k:v for k,v in x.items() if k!="digest"}
   if x["previous"]!=prev or hashlib.sha256(json.dumps(y,sort_keys=True).encode()).hexdigest()!=d:return False
   prev=d
  return True
class SafeAgentExecutor:
 def __init__(self,p,l,b=ExecutionBudget()):self.policy=p;self.ledger=l;self.budget=BudgetTracker(b);self.audit=AgentAuditTrail()
 def execute(self,a,t,caps,req,op,approval=None):
  if not self.policy.authorize(t,caps):self.audit.append(a,t.name,"denied",req);raise PermissionError()
  if t.requires_approval and not self.ledger.validate(approval,req):self.audit.append(a,t.name,"denied",req);raise PermissionError()
  self.budget.charge();
  try:v=op();self.audit.append(a,t.name,"completed",req);return v
  except Exception:self.audit.append(a,t.name,"failed",req);raise
def agent_safety_gate(e):return {"gate":"PASS" if e.audit.verify() else "FAIL","audit_steps":len(e.audit.steps)}




