from __future__ import annotations
import csv as _csv
import datetime as _dt
import json as _json
import os
import re as _re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from .errors import PeaError

class Namespace(dict):
    """Dictionary namespace exposed through PeaLang property access."""
    def __init__(self, *args, legacy_call=None, **kwargs):
        super().__init__(*args, **kwargs); self.legacy_call = legacy_call
    def __call__(self, *args):
        if self.legacy_call is None: raise PeaError('Namespace is not directly callable')
        return self.legacy_call(*args)

def _ns(legacy_call=None, **items): return Namespace(items, legacy_call=legacy_call)
def _text(value): return value if isinstance(value,str) else str(value)
def _ensure_parent(path): Path(path).expanduser().parent.mkdir(parents=True,exist_ok=True)

def _file_read(path): return Path(path).expanduser().read_text(encoding='utf-8')
def _file_write(path,content):
    p=Path(path).expanduser();_ensure_parent(p);p.write_text(_text(content),encoding='utf-8');return str(p)
def _file_append(path,content):
    p=Path(path).expanduser();_ensure_parent(p)
    with p.open('a',encoding='utf-8') as f:f.write(_text(content))
    return str(p)
def _file_copy(src,dst): _ensure_parent(dst);return str(shutil.copy2(src,dst))
def _file_move(src,dst): _ensure_parent(dst);return str(shutil.move(src,dst))
def _file_delete(path):
    p=Path(path).expanduser();
    if p.exists():p.unlink()
    return True
def _file_list(path='.'):
    return sorted(str(p) for p in Path(path).expanduser().iterdir())

def _path_join(*parts): return str(Path(*map(str,parts)))
def _path_name(path): return Path(path).name
def _path_stem(path): return Path(path).stem
def _path_extension(path): return Path(path).suffix
def _path_parent(path): return str(Path(path).parent)
def _path_absolute(path): return str(Path(path).expanduser().resolve())

def _json_parse(text): return _json.loads(text)
def _json_stringify(value,indent=2):
    level=int(indent);return _json.dumps(value,ensure_ascii=False,indent=None if level==0 else level)
def _json_read(path): return _json.loads(Path(path).read_text(encoding='utf-8'))
def _json_write(path,value,indent=2):
    p=Path(path);_ensure_parent(p);p.write_text(_json_stringify(value,indent),encoding='utf-8');return str(p)

def _csv_read(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f:return list(_csv.DictReader(f))
def _csv_write(path,rows,columns=None):
    rows=list(rows);p=Path(path);_ensure_parent(p)
    fields=list(columns) if columns else (list(rows[0].keys()) if rows else [])
    with p.open('w',newline='',encoding='utf-8') as f:
        writer=_csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    return str(p)

def _env_get(name,default=None): return os.environ.get(str(name),default)
def _env_has(name): return str(name) in os.environ
def _env_require(name):
    value=os.environ.get(str(name))
    if value is None: raise PeaError(f"Required environment variable '{name}' is not set")
    return value

def _dt_now(): return _dt.datetime.now(_dt.timezone.utc).isoformat()
def _dt_today(): return _dt.date.today().isoformat()
def _dt_parse(value): return _dt.datetime.fromisoformat(str(value).replace('Z','+00:00')).isoformat()
def _dt_format(value,fmt): return _dt.datetime.fromisoformat(str(value).replace('Z','+00:00')).strftime(str(fmt))
def _dt_add_days(value,days): return (_dt.datetime.fromisoformat(str(value).replace('Z','+00:00'))+_dt.timedelta(days=float(days))).isoformat()
def _dt_timestamp(): return _dt.datetime.now(_dt.timezone.utc).timestamp()

def _regex_match(pattern,text): return _re.search(str(pattern),str(text)) is not None
def _regex_find(pattern,text): return _re.findall(str(pattern),str(text))
def _regex_replace(pattern,replacement,text,count=0): return _re.sub(str(pattern),str(replacement),str(text),count=int(count))
def _regex_split(pattern,text): return _re.split(str(pattern),str(text))

def _http_request(method,url,body=None,headers=None,timeout=15):
    method=str(method).upper();headers=dict(headers or {})
    data=None
    if body is not None:
        if not isinstance(body,(str,bytes)):
            data=_json.dumps(body).encode('utf-8');headers.setdefault('Content-Type','application/json')
        else:data=body.encode('utf-8') if isinstance(body,str) else body
    req=urllib.request.Request(str(url),data=data,headers={str(k):str(v) for k,v in headers.items()},method=method)
    try:
        with urllib.request.urlopen(req,timeout=float(timeout)) as r:
            raw=r.read();text=raw.decode(r.headers.get_content_charset() or 'utf-8',errors='replace')
            return {'status':r.status,'ok':200<=r.status<300,'headers':dict(r.headers.items()),'text':text,'url':r.geturl()}
    except urllib.error.HTTPError as ex:
        raw=ex.read();text=raw.decode(ex.headers.get_content_charset() or 'utf-8',errors='replace')
        return {'status':ex.code,'ok':False,'headers':dict(ex.headers.items()),'text':text,'url':ex.geturl()}
def _http_json(response): return _json.loads(response['text'])
def _http_urlencode(values): return urllib.parse.urlencode(values)

def _process_runner(enabled):
    def run(command,args=None,timeout=30,cwd=None):
        if not enabled: raise PeaError('Process execution is disabled. Use --allow-process only for trusted programs.')
        argv=[str(command)]+[str(x) for x in (args or [])]
        result=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=float(timeout),shell=False)
        return {'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'ok':result.returncode==0}
    return run

def build_standard_library(allow_process=False):
    import shutil
    globals()['shutil']=shutil
    return {
      'file':_ns(read=_file_read,write=_file_write,append=_file_append,copy=_file_copy,move=_file_move,delete=_file_delete,exists=lambda p:Path(p).exists(),list=_file_list,mkdir=lambda p:str(Path(p).mkdir(parents=True,exist_ok=True) or p)),
      'path':_ns(join=_path_join,name=_path_name,stem=_path_stem,extension=_path_extension,parent=_path_parent,absolute=_path_absolute),
      'json':_ns(legacy_call=lambda value:_json_stringify(value,2),parse=_json_parse,stringify=_json_stringify,read=_json_read,write=_json_write),
      'csv':_ns(read=_csv_read,write=_csv_write),
      'env':_ns(get=_env_get,has=_env_has,require=_env_require),
      'datetime':_ns(now=_dt_now,today=_dt_today,parse=_dt_parse,format=_dt_format,add_days=_dt_add_days,timestamp=_dt_timestamp),
      'regex':_ns(match=_regex_match,find=_regex_find,replace=_regex_replace,split=_regex_split),
      'http':_ns(request=_http_request,get=lambda url,headers=None,timeout=15:_http_request('GET',url,None,headers,timeout),post=lambda url,body=None,headers=None,timeout=15:_http_request('POST',url,body,headers,timeout),json=_http_json,urlencode=_http_urlencode),
      'process':_ns(run=_process_runner(allow_process)),
    }
