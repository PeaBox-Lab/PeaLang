

"""PeaLang stable standard library registry (0.35)."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import csv as _csv, datetime as _dt, hashlib, hmac, json as _json, logging as _logging, math as _math, os, re as _re
import secrets, statistics, urllib.parse, urllib.request, urllib.error, concurrent.futures
from .errors import PeaError
class Namespace(dict):
    def __init__(self,*a,legacy_call=None,**k):super().__init__(*a,**k);self.legacy_call=legacy_call
    def __call__(self,*a):
        if self.legacy_call is None:raise PeaError('Namespace is not directly callable')
        return self.legacy_call(*a)
def _ns(legacy_call=None,**x):return Namespace(x,legacy_call=legacy_call)
@dataclass(frozen=True)
class StdModuleSpec:
    name:str; stability:str='Stable'; permissions:tuple[str,...]=(); description:str=''
STDLIB_VERSION='0.35'
MODULES={
 'std.collections':StdModuleSpec('std.collections',description='Collection transforms and queries'),
 'std.string':StdModuleSpec('std.string',description='Unicode string helpers'),
 'std.math':StdModuleSpec('std.math',description='Mathematics and statistics'),
 'std.datetime':StdModuleSpec('std.datetime',description='UTC-oriented date/time helpers'),
 'std.json':StdModuleSpec('std.json',description='JSON encode/decode'),
 'std.csv':StdModuleSpec('std.csv',permissions=('file.read','file.write'),description='CSV file IO'),
 'std.regex':StdModuleSpec('std.regex',description='Regular expressions'),
 'std.file':StdModuleSpec('std.file',permissions=('file.read','file.write'),description='Controlled filesystem IO'),
 'std.path':StdModuleSpec('std.path',description='Path manipulation'),
 'std.http':StdModuleSpec('std.http',permissions=('http.request',),description='HTTP client'),
 'std.crypto':StdModuleSpec('std.crypto',description='Hashing, HMAC and random tokens'),
 'std.logging':StdModuleSpec('std.logging',permissions=('log',),description='Host logging'),
 'std.testing':StdModuleSpec('std.testing',description='Assertions for libraries'),
 'std.concurrent':StdModuleSpec('std.concurrent',permissions=('concurrent',),description='Bounded parallel map'),
}

def stdlib_manifest():return {'version':STDLIB_VERSION,'modules':{k:{'stability':v.stability,'permissions':list(v.permissions),'description':v.description} for k,v in MODULES.items()}}
def _parent(p):Path(p).expanduser().parent.mkdir(parents=True,exist_ok=True)
def _text(v):return v if isinstance(v,str) else str(v)
def _file_read(p):return Path(p).expanduser().read_text(encoding='utf-8')
def _file_write(p,c):p=Path(p).expanduser();_parent(p);p.write_text(_text(c),encoding='utf-8');return str(p)
def _file_append(p,c):p=Path(p).expanduser();_parent(p);p.open('a',encoding='utf-8').write(_text(c));return str(p)
def _json_stringify(v,indent=2):return _json.dumps(v,ensure_ascii=False,indent=None if int(indent)==0 else int(indent))
def _http(method,url,body=None,headers=None,timeout=15):
 data=None; headers=dict(headers or {})
 if body is not None:data=(body if isinstance(body,bytes) else (_text(body) if isinstance(body,str) else _json.dumps(body))).encode();headers.setdefault('Content-Type','application/json')
 req=urllib.request.Request(str(url),data=data,headers={str(k):str(v) for k,v in headers.items()},method=str(method).upper())
 try:
  with urllib.request.urlopen(req,timeout=float(timeout)) as r:raw=r.read();return {'status':r.status,'ok':200<=r.status<300,'headers':dict(r.headers.items()),'text':raw.decode('utf-8','replace'),'url':r.geturl()}
 except urllib.error.HTTPError as e:return {'status':e.code,'ok':False,'headers':dict(e.headers.items()),'text':e.read().decode('utf-8','replace'),'url':e.geturl()}
def _module_values():
 return {
 'std.collections':_ns(first=lambda x,d=None:x[0] if x else d,last=lambda x,d=None:x[-1] if x else d,unique=lambda x:list(dict.fromkeys(x)),contains=lambda x,v:v in x,sort=lambda x:sorted(x),reverse=lambda x:list(reversed(x)),flatten=lambda x:[v for a in x for v in a],keys=lambda d:list(d.keys()),values=lambda d:list(d.values())),
 'std.string':_ns(length=lambda s:len(str(s)),upper=lambda s:str(s).upper(),lower=lambda s:str(s).lower(),trim=lambda s:str(s).strip(),split=lambda s,sep=None:str(s).split(sep),join=lambda sep,x:str(sep).join(map(str,x)),starts_with=lambda s,p:str(s).startswith(str(p)),ends_with=lambda s,p:str(s).endswith(str(p)),replace=lambda s,a,b:str(s).replace(str(a),str(b))),
 'std.math':_ns(abs=abs,min=min,max=max,round=round,sqrt=_math.sqrt,floor=_math.floor,ceil=_math.ceil,power=pow,mean=lambda x:statistics.mean(x),median=lambda x:statistics.median(x),pi=_math.pi),
 'std.datetime':_ns(now=lambda:_dt.datetime.now(_dt.timezone.utc).isoformat(),today=lambda:_dt.date.today().isoformat(),parse=lambda v:_dt.datetime.fromisoformat(str(v).replace('Z','+00:00')).isoformat(),format=lambda v,f:_dt.datetime.fromisoformat(str(v).replace('Z','+00:00')).strftime(str(f)),add_days=lambda v,n:(_dt.datetime.fromisoformat(str(v).replace('Z','+00:00'))+_dt.timedelta(days=float(n))).isoformat(),timestamp=lambda:_dt.datetime.now(_dt.timezone.utc).timestamp()),
 'std.json':_ns(legacy_call=lambda v:_json_stringify(v),parse=_json.loads,stringify=_json_stringify,read=lambda p:_json.loads(_file_read(p)),write=lambda p,v,indent=2:_file_write(p,_json_stringify(v,indent))),
 'std.csv':_ns(read=lambda p:list(_csv.DictReader(Path(p).open(newline='',encoding='utf-8-sig')))),
 'std.regex':_ns(match=lambda p,t:_re.search(str(p),str(t)) is not None,find=lambda p,t:_re.findall(str(p),str(t)),replace=lambda p,r,t,count=0:_re.sub(str(p),str(r),str(t),count=int(count)),split=lambda p,t:_re.split(str(p),str(t))),
 'std.file':_ns(read=_file_read,write=_file_write,append=_file_append,exists=lambda p:Path(p).exists(),list=lambda p='.':sorted(str(x) for x in Path(p).iterdir()),mkdir=lambda p:str(Path(p).mkdir(parents=True,exist_ok=True) or p),delete=lambda p:(Path(p).unlink(missing_ok=True) or True)),
 'std.path':_ns(join=lambda *x:str(Path(*map(str,x))),name=lambda p:Path(p).name,stem=lambda p:Path(p).stem,extension=lambda p:Path(p).suffix,parent=lambda p:str(Path(p).parent),absolute=lambda p:str(Path(p).expanduser().resolve())),
 'std.http':_ns(request=_http,get=lambda u,h=None,t=15:_http('GET',u,None,h,t),post=lambda u,b=None,h=None,t=15:_http('POST',u,b,h,t),json=lambda r:_json.loads(r['text']),urlencode=urllib.parse.urlencode),
 'std.crypto':_ns(sha256=lambda v:hashlib.sha256(_text(v).encode()).hexdigest(),hmac_sha256=lambda k,v:hmac.new(_text(k).encode(),_text(v).encode(),hashlib.sha256).hexdigest(),token_hex=lambda n=32:secrets.token_hex(int(n))),
 'std.logging':_ns(debug=lambda m:(_logging.getLogger('pealang').debug(_text(m)) or None),info=lambda m:(_logging.getLogger('pealang').info(_text(m)) or None),warning=lambda m:(_logging.getLogger('pealang').warning(_text(m)) or None),error=lambda m:(_logging.getLogger('pealang').error(_text(m)) or None)),
 'std.testing':_ns(expect=lambda c,m='Expectation failed': True if c else (_ for _ in ()).throw(PeaError(str(m))),equal=lambda a,b:a==b),
 'std.concurrent':_ns(map=lambda fn,items,workers=4:list(concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(32,int(workers)))).map(fn,list(items)))),
 }
def build_standard_library(allow_process=False,permissions=None):
 values=_module_values(); allowed=set(permissions or ())
 # stable std namespace; sensitive calls are absent unless capability is granted
 std={}
 for name,module_spec in MODULES.items():
  short=name.split('.',1)[1]; required=set(module_spec.permissions)
  std[short]=values[name] if required.issubset(allowed) else _guard(values[name],required-allowed,name)
 # Legacy names retained for 0.x compatibility. New code should use std.*.
 legacy={'file':std['file'],'path':std['path'],'json':std['json'],'csv':std['csv'],'datetime':std['datetime'],'regex':std['regex'],'http':std['http'],'task':std['concurrent']}
 return {'std':_ns(**std),**legacy}
def _guard(ns,missing,module):
 def denied(*a,**k):raise PeaError(f"Permission '{sorted(missing)[0]}' is required for '{module}'")
 return _ns(**{k:(denied if callable(v) else v) for k,v in ns.items()})


