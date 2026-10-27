"""PeaLang 0.88 developer tooling stabilization contracts."""
from dataclasses import dataclass,asdict
from enum import Enum
import hashlib,json
class Severity(str,Enum):ERROR='error';WARNING='warning';INFO='info';HINT='hint'
@dataclass(frozen=True)
class DiagnosticContract:
 code:str;severity:Severity;message_template:str;source:str='pealang'
class DiagnosticRegistry:
 def __init__(self):self._items={}
 def register(self,item):
  if item.code in self._items:raise ValueError('duplicate diagnostic code')
  self._items[item.code]=item;return self
 def validate(self,code,severity,message):
  item=self._items.get(code)
  return bool(item and item.severity==Severity(severity) and item.source and message)
 def snapshot(self):return {k:{**asdict(v),'severity':v.severity.value} for k,v in sorted(self._items.items())}
@dataclass(frozen=True)
class ToolProtocolProfile:
 tool:str;protocol:str;version:str;capabilities:frozenset[str]
class CompatibilityMatrix:
 def __init__(self):self.rows={}
 def register(self,profile):self.rows[(profile.tool,profile.protocol)]=profile;return self
 def supports(self,tool,protocol,required=()):
  p=self.rows.get((tool,protocol));return bool(p and frozenset(required)<=p.capabilities)
class EditorCapabilityNegotiator:
 def negotiate(self,server,client):return frozenset(server)&frozenset(client)
@dataclass(frozen=True)
class BreakpointFixture:file:str;line:int
@dataclass(frozen=True)
class DebugSnapshot:
 reason:str;file:str;line:int;function:str;variables:dict;stack:tuple[str,...]
class ReproducibleDebugSession:
 def __init__(self,breakpoints=()):self.breakpoints=tuple(breakpoints);self.snapshots=[]
 def record(self,reason,file,line,function,variables,stack):
  snap=DebugSnapshot(reason,file,int(line),function,dict(sorted(variables.items())),tuple(stack));self.snapshots.append(snap);return snap
 def fingerprint(self):return hashlib.sha256(json.dumps([asdict(x) for x in self.snapshots],sort_keys=True,separators=(',',':')).encode()).hexdigest()
 def breakpoint_hit(self,file,line):return any(x.file==file and x.line==line for x in self.breakpoints)
class DAPConformance:
 REQUIRED=frozenset({'initialize','launch','setBreakpoints','continue','next','stackTrace','scopes','variables','disconnect'})
 def certify(self,capabilities):
  missing=sorted(self.REQUIRED-frozenset(capabilities));return {'passed':not missing,'missing':missing}
class LSPConformance:
 REQUIRED=frozenset({'initialize','textDocument/publishDiagnostics','textDocument/hover','textDocument/completion','textDocument/definition'})
 def certify(self,capabilities):
  missing=sorted(self.REQUIRED-frozenset(capabilities));return {'passed':not missing,'missing':missing}
def tooling_certification_gate(*,lsp,dap,diagnostics_stable,debug_reproducible,editor_negotiation=True):
 checks={'lsp':bool(lsp.get('passed')),'dap':bool(dap.get('passed')),'diagnostics':bool(diagnostics_stable),'debugging':bool(debug_reproducible),'editor_negotiation':bool(editor_negotiation)}
 return {'gate':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'failed':[k for k,v in checks.items() if not v]}
