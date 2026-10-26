


"""Feature stability and compatibility contracts."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .errors import PeaError
class Stability(str,Enum):
 EXPERIMENTAL='Experimental';PREVIEW='Preview';STABLE='Stable';DEPRECATED='Deprecated';REMOVED='Removed'
@dataclass(frozen=True)
class Feature:
 name:str;since:str;stability:Stability;deprecated_since:str|None=None;replacement:str|None=None
FEATURES={
 'core.syntax':Feature('core.syntax','0.1',Stability.STABLE),
 'modules':Feature('modules','0.8',Stability.STABLE),
 'typing.optional':Feature('typing.optional','0.19',Stability.PREVIEW),
 'vm.peac':Feature('vm.peac','0.20',Stability.PREVIEW),
 'async.await':Feature('async.await','0.26',Stability.PREVIEW),
 'embedding.python':Feature('embedding.python','0.18',Stability.STABLE),
 'embedding.fastapi':Feature('embedding.fastapi','0.25',Stability.PREVIEW),
 'embedding.java.sidecar':Feature('embedding.java.sidecar','0.28',Stability.PREVIEW),
 'embedding.typescript':Feature('embedding.typescript','0.29',Stability.PREVIEW),
 'packages.signed':Feature('packages.signed','0.31',Stability.PREVIEW),
}
def feature_status(name):
 if name not in FEATURES:raise PeaError(f'Unknown PeaLang feature: {name}')
 return FEATURES[name]
def stable_features():return sorted(k for k,v in FEATURES.items() if v.stability==Stability.STABLE)
def validate_deprecation(feature,current_minor):
 f=feature_status(feature)
 if f.stability!=Stability.REMOVED:return True
 if not f.deprecated_since:raise PeaError(f'Removed feature {feature} has no deprecation history')
 dep=int(f.deprecated_since.split('.')[-1]);cur=int(str(current_minor).split('.')[-1])
 if cur-dep<2:raise PeaError(f'Feature {feature} removed before two-minor deprecation window')
 return True
from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib, inspect, json, re
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

_VERSION = re.compile(r"^\d+\.\d+(?:\.\d+)?(?:[a-z]+\d+)?$")
def _version_key(value: str) -> tuple[int, ...]:
    match = re.match(r"^(\d+)\.(\d+)(?:\.(\d+))?", value)
    if not match:
        raise ValueError(f"invalid version: {value}")
    return tuple(int(x or 0) for x in match.groups())

class DeprecationState(str, Enum):
    ACTIVE = "active"
    REMOVED = "removed"

@dataclass(frozen=True)
class Deprecation:
    feature: str
    deprecated_in: str
    remove_in: str
    replacement: str
    rationale: str
    state: DeprecationState = DeprecationState.ACTIVE

class DeprecationLedger:
    def __init__(self, entries: Iterable[Deprecation] = ()): self._entries = {x.feature: x for x in entries}
    def add(self, entry: Deprecation) -> None:
        if entry.feature in self._entries: raise ValueError(f"duplicate deprecation: {entry.feature}")
        if _version_key(entry.remove_in) <= _version_key(entry.deprecated_in): raise ValueError("remove_in must follow deprecated_in")
        if not entry.replacement.strip(): raise ValueError("replacement is required")
        self._entries[entry.feature] = entry
    def due(self, version: str) -> list[Deprecation]:
        return sorted((x for x in self._entries.values() if x.state is DeprecationState.ACTIVE and _version_key(x.remove_in) <= _version_key(version)), key=lambda x:x.feature)
    def validate_release(self, version: str) -> list[str]:
        return [f"{x.feature} reached removal version {x.remove_in}" for x in self.due(version)]
    def to_dict(self) -> dict[str, Any]: return {"schema": 1, "entries": [asdict(x) for x in sorted(self._entries.values(), key=lambda x:x.feature)]}
    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DeprecationLedger":
        return cls(Deprecation(**{**x, "state": DeprecationState(x.get("state","active"))}) for x in data.get("entries", []))

@dataclass(frozen=True)
class Migration:
    migration_id: str
    from_version: str
    to_version: str
    upgrade: Callable[[dict[str, Any]], dict[str, Any]]
    downgrade: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    description: str = ""

@dataclass(frozen=True)
class MigrationEvent:
    migration_id: str
    direction: str
    checksum_before: str
    checksum_after: str

@dataclass(frozen=True)
class MigrationResult:
    document: dict[str, Any]
    events: tuple[MigrationEvent, ...]

class MigrationRegistry:
    def __init__(self): self._migrations: dict[tuple[str,str], Migration] = {}
    def register(self, migration: Migration) -> None:
        key=(migration.from_version,migration.to_version)
        if key in self._migrations: raise ValueError(f"duplicate migration path: {key}")
        if _version_key(migration.to_version) <= _version_key(migration.from_version): raise ValueError("migration must move forward")
        self._migrations[key]=migration
    @staticmethod
    def _checksum(doc: Mapping[str, Any]) -> str:
        return hashlib.sha256(json.dumps(doc,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
    def plan(self, current: str, target: str) -> list[Migration]:
        if current==target:return []
        reverse=_version_key(target)<_version_key(current); cursor=current; plan=[]; seen=set()
        while cursor!=target:
            if cursor in seen: raise RuntimeError("migration cycle detected")
            seen.add(cursor)
            options=[]
            for (start,end),mig in self._migrations.items():
                if not reverse and start==cursor and _version_key(end)<=_version_key(target):options.append((end,mig))
                if reverse and end==cursor and mig.downgrade and _version_key(start)>=_version_key(target):options.append((start,mig))
            if not options: raise LookupError(f"no migration path from {cursor} to {target}")
            options.sort(key=lambda x:_version_key(x[0]), reverse=not reverse)
            cursor,mig=options[0];plan.append(mig)
        return plan
    def migrate(self, document: Mapping[str, Any], current: str, target: str, applied: Iterable[str]=()) -> MigrationResult:
        doc=json.loads(json.dumps(document));events=[];done=set(applied);reverse=_version_key(target)<_version_key(current)
        for migration in self.plan(current,target):
            marker=f"{'down' if reverse else 'up'}:{migration.migration_id}"
            if marker in done: continue
            before=self._checksum(doc);fn=migration.downgrade if reverse else migration.upgrade
            if fn is None: raise RuntimeError(f"migration {migration.migration_id} is not reversible")
            updated=fn(json.loads(json.dumps(doc)))
            if not isinstance(updated,dict): raise TypeError("migration must return a dictionary")
            doc=updated;events.append(MigrationEvent(migration.migration_id,"down" if reverse else "up",before,self._checksum(doc)))
        return MigrationResult(doc,tuple(events))

@dataclass(frozen=True)
class ApiSymbol:
    name: str
    kind: str
    signature: str

@dataclass(frozen=True)
class ApiDiff:
    added: tuple[str,...]=(); removed: tuple[str,...]=(); changed: tuple[str,...]=()
    @property
    def breaking(self) -> bool: return bool(self.removed or self.changed)

class PublicApiSnapshot:
    def __init__(self, symbols: Iterable[ApiSymbol]): self.symbols={x.name:x for x in symbols}
    @classmethod
    def capture(cls, module: Any) -> "PublicApiSnapshot":
        names=getattr(module,"__all__",[n for n in vars(module) if not n.startswith("_")]);symbols=[]
        for name in sorted(names):
            value=getattr(module,name);kind="class" if inspect.isclass(value) else "function" if callable(value) else "value"
            try:signature=str(inspect.signature(value)) if callable(value) else type(value).__name__
            except (TypeError,ValueError):signature="unknown"
            symbols.append(ApiSymbol(name,kind,signature))
        return cls(symbols)
    def diff(self, baseline: "PublicApiSnapshot") -> ApiDiff:
        current=set(self.symbols);old=set(baseline.symbols);common=current&old
        return ApiDiff(tuple(sorted(current-old)),tuple(sorted(old-current)),tuple(sorted(n for n in common if self.symbols[n]!=baseline.symbols[n])))
    def to_dict(self): return {"schema":1,"symbols":[asdict(x) for x in sorted(self.symbols.values(),key=lambda x:x.name)]}
    @classmethod
    def from_dict(cls,data): return cls(ApiSymbol(**x) for x in data.get("symbols",[]))

class CompatibilityGate:
    def evaluate(self, diff: ApiDiff, approved_breaks: Iterable[str]=()) -> list[str]:
        approved=set(approved_breaks);issues=[]
        for name in diff.removed:
            if name not in approved:issues.append(f"unapproved removed API: {name}")
        for name in diff.changed:
            if name not in approved:issues.append(f"unapproved changed API: {name}")
        return issues

def load_json(path: str|Path) -> dict[str,Any]: return json.loads(Path(path).read_text(encoding="utf-8"))
def save_json(path: str|Path, value: Mapping[str,Any]) -> Path:
    target=Path(path);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8");return target



