

"""PeaLang 0.90 API-freeze and 1.0 compatibility contracts."""
from dataclasses import dataclass, asdict
import hashlib, json

@dataclass(frozen=True)
class FrozenSurface:
    name: str
    kind: str
    signature: str
    stability: str = "frozen"

class ApiFreezeManifest:
    def __init__(self, surfaces=()): self.surfaces={x.name:x for x in surfaces}
    def add(self, surface):
        if surface.name in self.surfaces: raise ValueError("duplicate frozen surface")
        self.surfaces[surface.name]=surface; return self
    def to_dict(self):
        return {"schema":1,"policy":"pealang-1.0-api-freeze","surfaces":[asdict(x) for x in sorted(self.surfaces.values(),key=lambda x:x.name)]}
    def digest(self): return hashlib.sha256(json.dumps(self.to_dict(),sort_keys=True,separators=(",",":")).encode()).hexdigest()
    def diff(self, baseline):
        current, old=self.surfaces, baseline.surfaces
        return {"added":sorted(set(current)-set(old)),"removed":sorted(set(old)-set(current)),"changed":sorted(k for k in set(current)&set(old) if current[k]!=old[k])}

@dataclass(frozen=True)
class FreezePolicy:
    allow_additive: bool=True
    syntax_frozen: bool=True
    runtime_api_frozen: bool=True
    package_api_frozen: bool=True
    diagnostics_frozen: bool=True
    bytecode_versioned: bool=True

class BreakingChangeLedger:
    def __init__(self): self.approvals={}
    def approve(self, change_id, reason, reviewer):
        if not change_id or not reason or not reviewer: raise ValueError("change id, reason and reviewer required")
        self.approvals[change_id]={"reason":reason,"reviewer":reviewer}; return change_id
    def approved(self, change_id): return change_id in self.approvals

def freeze_gate(diff, policy=FreezePolicy(), approved_breaks=()):
    approved=set(approved_breaks); violations=[]
    violations += ["removed:"+x for x in diff.get("removed",[]) if x not in approved]
    violations += ["changed:"+x for x in diff.get("changed",[]) if x not in approved]
    if not policy.allow_additive: violations += ["added:"+x for x in diff.get("added",[])]
    checks={"syntax":policy.syntax_frozen,"runtime_api":policy.runtime_api_frozen,"package_api":policy.package_api_frozen,"diagnostics":policy.diagnostics_frozen,"bytecode_versioned":policy.bytecode_versioned,"compatibility":not violations}
    return {"gate":"PASS" if all(checks.values()) else "FAIL","checks":checks,"violations":violations}

def compatibility_contract(manifest, diagnostic_codes=(), bytecode_version=None):
    return {"schema":1,"target":"1.0","api_digest":manifest.digest(),"diagnostic_codes":sorted(set(diagnostic_codes)),"bytecode_version":bytecode_version,"rules":{"breaking_changes":"approval-required","additions":"compatible-by-default","deprecations":"ledger-required"}}


