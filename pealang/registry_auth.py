"""Registry credential handling without storing plaintext tokens in lockfiles."""
from __future__ import annotations
import os
from .errors import PeaError
def registry_token(name,env=None):
 env=env or os.environ;key='PEALANG_REGISTRY_'+name.upper().replace('-','_')+'_TOKEN';value=env.get(key)
 if not value:raise PeaError(f'Missing registry credential in {key}')
 return value
def bearer_headers(name,env=None):return {'Authorization':'Bearer '+registry_token(name,env),'User-Agent':'PeaLang/0.34.0'}
