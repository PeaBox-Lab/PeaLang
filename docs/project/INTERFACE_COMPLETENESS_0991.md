# Interface Completeness 0.99.1

All 26 `NotImplementedError` sites found by the audit are intentional base-interface contracts, not directly instantiable production backends. Concrete implementations are tested separately. The classified modules and methods are:

- `cloud_connectors.py` (6): — listdir, stat, open, mkdir, remove, rename
  - L70: `def listdir(self,path):raise NotImplementedError`
  - L71: `def stat(self,path):raise NotImplementedError`
  - L72: `def open(self,path,mode='rb'):raise NotImplementedError`
  - L73: `def mkdir(self,path):raise NotImplementedError`
  - L74: `def remove(self,path):raise NotImplementedError`
  - L75: `def rename(self,source,target):raise NotImplementedError`
- `connector_runtime.py` (1): — token
  - L11: `def token(self):raise NotImplementedError`
- `connectors.py` (1): — request
  - L36: `def request(self,method,url,headers=None,body=None,timeout=30.0)->ConnectorResponse:raise NotImplementedError`
- `distributed_compute.py` (1): — execute
  - L21: `def execute(self,plan,source):raise NotImplementedError`
- `distributed_serving.py` (3): — increment, get, set
  - L12: `def increment(self,key,window_seconds):raise NotImplementedError`
  - L13: `def get(self,key):raise NotImplementedError`
  - L14: `def set(self,key,value,ttl=None):raise NotImplementedError`
- `enterprise_connectors.py` (1): — get
  - L15: `def get(self,name):raise NotImplementedError`
- `integration_hardening.py` (1): — get
  - L21: `def get(self,name:str)->str|None: raise NotImplementedError`
- `object_storage.py` (4): — list, read_bytes, write_bytes, delete
  - L22: `def list(self,prefix='')->DataFrame: raise NotImplementedError`
  - L23: `def read_bytes(self,key): raise NotImplementedError`
  - L24: `def write_bytes(self,key,data,content_type=None): raise NotImplementedError`
  - L25: `def delete(self,key): raise NotImplementedError`
- `orchestration_state.py` (4): — begin, finish, successful, attempts
  - L44: `def begin(self,*a,**k): raise NotImplementedError`
  - L45: `def finish(self,*a,**k): raise NotImplementedError`
  - L46: `def successful(self,*a,**k): raise NotImplementedError`
  - L47: `def attempts(self,*a,**k): raise NotImplementedError`
- `serverless.py` (3): — CompilationTarget.compile, CompilationTarget.execute, PythonTarget.execute (intentional sandbox/runtime stubs)
  - L186: `raise NotImplementedError`
  - L193: `raise NotImplementedError`
  - L223: `raise NotImplementedError("PythonTarget.execute requires a sandboxed Python runtime that is not implemented in this release")`
- `sql.py` (1): — SQLite-only portable upsert; other dialects raise intentionally
  - L89: `if self.spec.scheme!='sqlite':raise NotImplementedError('Portable upsert is implemented for SQLite in 0.44; other adapters expose transactions/batching pending dialect-specific merge SQL')`

Release policy: unclassified `NotImplementedError` occurrences are forbidden. Regenerate with `pea audit --write-interface-doc` when intentional classified sites change.
