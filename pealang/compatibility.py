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

