from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json,math,os,time
from concurrent.futures import ThreadPoolExecutor
from .ast_nodes import *
from .environment import Env
from .errors import PeaError
from .parser import parse_source

CURRENT_INTERPRETER = None

def set_current_interpreter(interp):
    global CURRENT_INTERPRETER
    CURRENT_INTERPRETER = interp
from .stdlib import build_standard_library
from .ai import build_ai_namespace
from .skills import SkillRegistry
from .project import load_manifest, resolve_module
from .agents import ToolRegistry,AgentRuntime
class ReturnSignal(Exception):
    def __init__(self,v):self.value=v
class BreakSignal(Exception):pass
class ContinueSignal(Exception):pass
@dataclass
class UserFunction:params:list;body:list[Stmt];closure:Env
class Interpreter:
    def __init__(self,output=None,base_dir=None,allow_process=False,project_root=None,dependencies=None,debug_hook=None,permissions=None):
        self.output=output or print;self.debug_hook=debug_hook;self.call_stack=[];self.global_env=Env();self.env=self.global_env;self.module_exports=None;self.base_dir=Path(base_dir or '.').resolve();self.source_name='<input>';self.imported=set();self.project_root=Path(project_root).resolve() if project_root else self.base_dir;self.dependencies=dependencies or {}
        def _enumerate(iterable,start=0): return [[i,v] for i,v in enumerate(iterable,int(start))]
        def _zip(*args): return [list(x) for x in zip(*args)]
        def _sorted(iterable,key=None,reverse=False):
            if key is None: return sorted(iterable,reverse=reverse)
            return sorted(iterable,key=lambda x: self.invoke_user_function(key,[x]) if isinstance(key,UserFunction) else key(x),reverse=reverse)
        def _reversed(iterable): return list(reversed(list(iterable)))
        def _map(fn,iterable): return [self.invoke_user_function(fn,[x]) if isinstance(fn,UserFunction) else fn(x) for x in iterable]
        def _filter(fn,iterable): return [x for x in iterable if (self.invoke_user_function(fn,[x]) if isinstance(fn,UserFunction) else fn(x))]
        def _any(iterable): return any(iterable)
        def _all(iterable): return all(iterable)
        def _get(obj,key,default=None):
            try:
                if isinstance(obj,dict): return obj.get(key,default)
                return obj[key]
            except Exception: return default
        def _has(obj,key):
            try: return key in obj
            except Exception: return False
        def _merge(*objs):
            r={}
            for o in objs:
                if isinstance(o,dict): r.update(o)
            return r
        def _pop(obj,key=None):
            try:
                if isinstance(obj,list): return obj.pop() if key is None else obj.pop(int(key))
                if isinstance(obj,dict): return obj.pop(key,None)
            except Exception: return None
        def _push(obj,val): 
            if isinstance(obj,list): obj.append(val); return obj
            return obj
        def _slice(obj,start=None,end=None,step=None): return obj[start:end:step]
        def _contains(obj,val):
            try: return val in obj
            except Exception: return False

        def _chunk(seq, n):
            seq=list(seq); n=max(1,int(n)); return [seq[i:i+n] for i in range(0,len(seq),n)]
        def _flatten(seq, depth=1):
            out=[]
            for x in seq:
                if depth!=0 and isinstance(x,(list,tuple)): out.extend(_flatten(list(x), depth-1 if isinstance(depth,int) else depth))
                else: out.append(x)
            return out
        def _uniq(seq):
            seen=[]; 
            for x in seq:
                if x not in seen: seen.append(x)
            return seen
        def _pick(d, keys): return {k:d.get(k) for k in keys if isinstance(d,dict)}
        def _omit(d, keys): return {k:v for k,v in d.items()} if not isinstance(d,dict) else {k:v for k,v in d.items() if k not in set(keys)}
        def _clamp(x, lo, hi): return max(lo, min(hi, x))
        def _uuid(): import uuid as _u; return str(_u.uuid4())
        def _randint(a,b=0):
            import random as _r
            if b==0 and a!=0: a,b=0,a
            return _r.randint(int(a),int(b))
        def _b64e(s): import base64 as _b; return _b.b64encode(str(s).encode()).decode()
        def _b64d(s): import base64 as _b; return _b.b64decode(str(s)).decode('utf-8','replace')
        def _coalesce(*args):
            for a in args:
                if a is not None: return a
            return None
        def _repeat(val, n): return [val for _ in range(int(n))]
        def _times(n, fn):
            out=[]
            for i in range(int(n)):
                out.append(self.invoke_user_function(fn,[i]) if isinstance(fn,UserFunction) else fn(i))
            return out
        def _find(seq, fn):
            for x in seq:
                if self.invoke_user_function(fn,[x]) if isinstance(fn,UserFunction) else fn(x): return x
            return None
        def _find_index(seq, fn):
            for i,x in enumerate(seq):
                if self.invoke_user_function(fn,[x]) if isinstance(fn,UserFunction) else fn(x): return i
            return -1
        def _pluck(seq, key): return [x.get(key) if isinstance(x,dict) else getattr(x,key,None) for x in seq]
        def _index_by(seq, key): return {(x.get(key) if isinstance(x,dict) else getattr(x,key,None)): x for x in seq}
        def _sort_by(seq, key, reverse=False):
            def kf(x): return x.get(key) if isinstance(x,dict) else getattr(x,key,None)
            return sorted(list(seq), key=kf, reverse=reverse)
        def _now_iso():
            from datetime import datetime, timezone
            return datetime.now(timezone.utc).isoformat()
        def _is_null(x): return x is None
        def _is_list(x): return isinstance(x, list)
        def _is_dict(x): return isinstance(x, dict)
        def _is_string(x): return isinstance(x, str)
        def _is_number(x): return isinstance(x, (int,float)) and not isinstance(x,bool)
        def _is_bool(x): return isinstance(x, bool)
        def _identity(x): return x
        def _tap(x, fn=None):
            if fn is not None:
                if isinstance(fn,UserFunction): self.invoke_user_function(fn,[x])
                else: fn(x)
            return x
        def _pad_start(s, n, ch=' '): return str(s).rjust(int(n), str(ch)[:1] or ' ')
        def _pad_end(s, n, ch=' '): return str(s).ljust(int(n), str(ch)[:1] or ' ')
        def _lines(s): return str(s).splitlines()
        def _words(s): return str(s).split()
        def _floor(x): import math as _m; return _m.floor(x)
        def _ceil(x): import math as _m; return _m.ceil(x)
        def _log(x, base=None): import math as _m; return _m.log(x) if base is None else _m.log(x, base)
        def _exp(x): import math as _m; return _m.exp(x)
        def _pow(a,b): return a**b
        def _get_path(obj, path, default=None):
            cur = obj
            for part in str(path).split('.'):
                try:
                    if isinstance(cur, dict): cur = cur[part] if part in cur else cur.get(int(part) if part.isdigit() else part, default)
                    elif isinstance(cur, list): cur = cur[int(part)]
                    else: return default
                except Exception: return default
            return cur
        def _deep_merge(a, b):
            if isinstance(a, dict) and isinstance(b, dict):
                r = dict(a)
                for k,v in b.items(): r[k] = _deep_merge(r[k], v) if k in r else v
                return r
            return b
        def _take(seq, n): return list(seq)[:int(n)]
        def _drop(seq, n): return list(seq)[int(n):]
        def _partition(seq, fn):
            a,b=[],[]
            for x in seq:
                ok = self.invoke_user_function(fn,[x]) if isinstance(fn,UserFunction) else fn(x)
                (a if ok else b).append(x)
            return [a,b]
        def _count_by(seq, fn=None):
            from collections import Counter
            if fn is None: return dict(Counter(seq))
            vals=[self.invoke_user_function(fn,[x]) if isinstance(fn,UserFunction) else (x.get(fn) if isinstance(x,dict) and isinstance(fn,str) else fn(x)) for x in seq]
            return dict(Counter(vals))
        def _first(seq, default=None): return list(seq)[0] if seq else default
        def _last(seq, default=None): return list(seq)[-1] if seq else default
        def _is_empty(x):
            if x is None: return True
            try: return len(x)==0
            except Exception: return False
        def _compact(seq): return [x for x in seq if x is not None and x is not False and x != '' and x != 0]
        def _defaults(d, *defs):
            r=dict(d) if isinstance(d,dict) else {}
            for df in defs:
                if isinstance(df,dict):
                    for k,v in df.items():
                        if k not in r or r[k] is None: r[k]=v
            return r
        def _invert(d): return {v:k for k,v in d.items()} if isinstance(d,dict) else {}
        def _to_pairs(d): return [[k,v] for k,v in d.items()] if isinstance(d,dict) else list(d)
        def _from_pairs(pairs): return {k:v for k,v in pairs}
        def _sum_by(seq, key):
            return sum((x.get(key) if isinstance(x,dict) else getattr(x,key,0)) or 0 for x in seq)
        def _avg(seq):
            s=list(seq); return (sum(s)/len(s)) if s else None
        def _capitalize(s): t=str(s); return t[:1].upper()+t[1:] if t else t
        def _snake_case(s):
            import re as _re; t=str(s).replace('-',' ').replace(' ','_')
            t=_re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', t); return t.lower()
        def _kebab_case(s): return _snake_case(s).replace('_','-')
        def _slugify(s):
            import re as _re
            t=str(s)
            t=_re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', t)
            t=t.lower()
            t=_re.sub(r'[^a-z0-9]+','-', t)
            return t.strip('-')
        def _truncate(s, n, suffix='...'):
            t=str(s); n=int(n)
            return t if len(t)<=n else t[:max(0,n-len(suffix))]+suffix
        def _union(*seqs):
            out=[]
            for seq in seqs:
                for x in seq:
                    if x not in out: out.append(x)
            return out
        def _intersection(a,b): bset=list(b); return [x for x in a if x in bset]
        def _difference(a,b): bset=list(b); return [x for x in a if x not in bset]


        def _has_path(obj, path):
            _sentinel = object()
            return _get_path(obj, path, _sentinel) is not _sentinel
        def _set_path(obj, path, value):
            import copy
            parts=str(path).split('.')
            if not parts: return value
            root=copy.deepcopy(obj) if isinstance(obj,(dict,list)) else {}
            cur=root
            for part in parts[:-1]:
                key=int(part) if isinstance(cur,list) and str(part).lstrip('-').isdigit() else part
                if isinstance(cur,dict):
                    if key not in cur or not isinstance(cur[key],(dict,list)): cur[key]={}
                    cur=cur[key]
                elif isinstance(cur,list):
                    idx=int(part)
                    while len(cur)<=idx: cur.append(None)
                    if not isinstance(cur[idx],(dict,list)): cur[idx]={}
                    cur=cur[idx]
                else: return root
            last=parts[-1]
            if isinstance(cur,dict): cur[last]=value
            elif isinstance(cur,list):
                idx=int(last)
                while len(cur)<=idx: cur.append(None)
                cur[idx]=value
            return root
        def _map_values(d, fn):
            if not isinstance(d,dict): return d
            return {k:(self.invoke_user_function(fn,[v,k]) if isinstance(fn,UserFunction) else fn(v)) for k,v in d.items()}
        def _map_keys(d, fn):
            if not isinstance(d,dict): return d
            return {(self.invoke_user_function(fn,[k,v]) if isinstance(fn,UserFunction) else fn(k)):v for k,v in d.items()}
        def _pick_by(d, fn):
            if not isinstance(d,dict): return {}
            return {k:v for k,v in d.items() if (self.invoke_user_function(fn,[v,k]) if isinstance(fn,UserFunction) else fn(v))}
        def _omit_by(d, fn):
            if not isinstance(d,dict): return {}
            return {k:v for k,v in d.items() if not (self.invoke_user_function(fn,[v,k]) if isinstance(fn,UserFunction) else fn(v))}
        def _shuffle(seq):
            import random; r=list(seq); random.shuffle(r); return r
        def _product(seq):
            p=1
            for x in seq: p*=x
            return p
        def _median(seq):
            s=sorted(list(seq)); n=len(s)
            if not n: return None
            m=n//2
            return (s[m-1]+s[m])/2 if n%2==0 else s[m]
        def _parse_int(x, default=None):
            try: return int(float(str(x).strip()))
            except Exception: return default
        def _parse_float(x, default=None):
            try: return float(str(x).strip())
            except Exception: return default
        def _strip_prefix(s, prefix): t=str(s); p=str(prefix); return t[len(p):] if t.startswith(p) else t
        def _strip_suffix(s, suffix): t=str(s); p=str(suffix); return t[:-len(p)] if p and t.endswith(p) else t
        def _sha256(s): import hashlib; return hashlib.sha256(str(s).encode()).hexdigest()
        def _url_encode(s): import urllib.parse; return urllib.parse.quote(str(s), safe='')
        def _url_decode(s): import urllib.parse; return urllib.parse.unquote(str(s))
        def _html_escape(s): import html; return html.escape(str(s))
        def _title_case(s): return str(s).title()
        def _center(s, n, ch=' '): return str(s).center(int(n), str(ch)[:1] or ' ')

        def _min_by(seq, fn):
            items=list(seq)
            if not items: return None
            def k(x):
                return self.invoke_user_function(fn,[x]) if isinstance(fn,UserFunction) else (x.get(fn) if isinstance(x,dict) and isinstance(fn,str) else fn(x))
            return min(items, key=k)
        def _max_by(seq, fn):
            items=list(seq)
            if not items: return None
            def k(x):
                return self.invoke_user_function(fn,[x]) if isinstance(fn,UserFunction) else (x.get(fn) if isinstance(x,dict) and isinstance(fn,str) else fn(x))
            return max(items, key=k)
        def _without(seq, *vals): vs=set(vals); return [x for x in seq if x not in vs]
        def _xor(a,b): sa, sb=list(a), list(b); return [x for x in sa if x not in sb]+[x for x in sb if x not in sa]
        def _zip_object(keys, vals): return {k:v for k,v in zip(keys, vals)}
        def _ensure_list(x): return [] if x is None else (list(x) if isinstance(x,(list,tuple)) else [x])
        def _ensure_dict(x): return {} if x is None else (dict(x) if isinstance(x,dict) else {'value':x})
        def _size(x):
            try: return len(x)
            except Exception: return 0
        def _random_choice(seq): import random; s=list(seq); return random.choice(s) if s else None
        def _clone(x):
            import copy; return copy.copy(x)
        def _deep_clone(x):
            import copy; return copy.deepcopy(x)
        def _deep_equal(a,b): return a==b
        def _nth(seq, n, default=None):
            try: s=list(seq); i=int(n); return s[i] if -len(s)<=i<len(s) else default
            except Exception: return default
        def _initial(seq): s=list(seq); return s[:-1] if s else []
        def _rest(seq): return list(seq)[1:]
        def _sample_list(seq, n=1):
            import random; s=list(seq); n=min(int(n),len(s)); return random.sample(s,n) if n else []

        def _group_by(seq, fn):
            out={}
            for x in seq:
                k = self.invoke_user_function(fn,[x]) if isinstance(fn,UserFunction) else (x.get(fn) if isinstance(x,dict) and isinstance(fn,str) else fn(x))
                if isinstance(k,(dict,list)): k=str(k)
                out.setdefault(k,[]).append(x)
            return out
        def _scan(seq, fn, initial=None):
            out=[]; acc=initial
            for i,x in enumerate(seq):
                if i==0 and initial is None: acc=x; out.append(acc); continue
                acc = self.invoke_user_function(fn,[acc,x]) if isinstance(fn,UserFunction) else fn(acc,x)
                out.append(acc)
            return out
        def _hex_encode(s): return str(s).encode().hex()
        def _hex_decode(s): return bytes.fromhex(str(s)).decode('utf-8','replace')
        def _ensure_str(x, default=''): return default if x is None else str(x)
        def _ensure_int(x, default=0): 
            try: return int(float(x))
            except Exception: return default
        def _ensure_float(x, default=0.0):
            try: return float(x)
            except Exception: return default
        def _pipe(value, *fns):
            v=value
            for fn in fns:
                v = self.invoke_user_function(fn,[v]) if isinstance(fn,UserFunction) else fn(v)
            return v
        def _apply_fn(fn, args=None):
            a=args if isinstance(args,list) else ([] if args is None else [args])
            return self.invoke_user_function(fn,a) if isinstance(fn,UserFunction) else fn(*a)
        def _pairs_to_dict(seq): return {k:v for k,v in seq}

        def _gcd(a,b):
            import math as _m; return _m.gcd(int(a), int(b))
        def _lcm(a,b):
            import math as _m; a,b=int(a),int(b)
            return abs(a*b)//_m.gcd(a,b) if a and b else 0
        def _sign(x):
            try: x=float(x); return 0 if x==0 else (1 if x>0 else -1)
            except Exception: return 0
        def _is_even(x): return int(x) % 2 == 0
        def _is_odd(x): return int(x) % 2 != 0
        def _lerp(a,b,t): return a + (b-a)*float(t)
        def _rotate(seq, n=1):
            s=list(seq)
            if not s: return s
            n=int(n)%len(s); return s[-n:]+s[:-n] if n else s
        def _interleave(*seqs):
            out=[]
            for items in zip(*seqs):
                for x in items: out.append(x)
            return out
        def _window_list(seq, size, step=1):
            s=list(seq); size=int(size); step=max(1,int(step)); out=[]
            for i in range(0, max(0, len(s)-size+1), step): out.append(s[i:i+size])
            return out
        def _dedupe_by(seq, fn):
            seen=set(); out=[]
            for x in seq:
                k = self.invoke_user_function(fn,[x]) if isinstance(fn,UserFunction) else (x.get(fn) if isinstance(x,dict) and isinstance(fn,str) else fn(x))
                try: sk=k
                except Exception: sk=str(k)
                if sk not in seen: seen.add(sk); out.append(x)
            return out
        def _assoc(d, key, value):
            r=dict(d) if isinstance(d,dict) else {}; r[key]=value; return r
        def _dissoc(d, *keys):
            r=dict(d) if isinstance(d,dict) else {}; 
            for k in keys: r.pop(k,None)
            return r
        def _rename_keys(d, mapping):
            if not isinstance(d,dict): return d
            return { (mapping.get(k,k)): v for k,v in d.items() }
        def _format_number(x, decimals=2):
            try: return f"{float(x):.{int(decimals)}f}"
            except Exception: return str(x)
        def _between_val(x, lo, hi): 
            try: x=float(x); return float(lo)<=x<=float(hi)
            except Exception: return False
        def _safe(fn,default=None):
            try:
                if isinstance(fn,UserFunction): return self.invoke_user_function(fn,[])
                return fn()
            except Exception: return default
        builtins={'range':lambda *a:list(range(*map(int,a))),'len':len,'str':lambda x:self.stringify(x),'bool':bool,'number':lambda x:float(x),'int':lambda x:int(float(x)),'float':lambda x:float(x),'type':lambda x:type(x).__name__,'upper':lambda x:str(x).upper(),'lower':lambda x:str(x).lower(),'trim':lambda x:str(x).strip(),'split':lambda x,s=None:str(x).split(s),'join':lambda s,x:str(s).join(map(str,x)),'replace':lambda s,a,b:str(s).replace(str(a),str(b)),'starts_with':lambda s,p:str(s).startswith(str(p)),'ends_with':lambda s,p:str(s).endswith(str(p)),'contains':_contains,'append':self._append,'push':_push,'pop':_pop,'get':_get,'has':_has,'merge':_merge,'slice':_slice,'keys':lambda d:list(d.keys()) if isinstance(d,dict) else list(range(len(d))),'values':lambda d:list(d.values()) if isinstance(d,dict) else list(d),'items':lambda d:[[k,v] for k,v in d.items()] if isinstance(d,dict) else _enumerate(d),'read':lambda p:Path(p).read_text(encoding='utf-8'),'write':self._write,'exists':os.path.exists,'sqrt':math.sqrt,'abs':abs,'round':round,'min':min,'max':max,'sum':lambda x,start=0:sum(x,start),'sleep':time.sleep,'enumerate':_enumerate,'zip':_zip,'sorted':_sorted,'reversed':_reversed,'map':_map,'filter':_filter,'any':_any,'all':_all,'list':lambda x=None:list(x) if x is not None else [],'dict':lambda x=None:dict(x) if x is not None else {},'json_parse':lambda s:json.loads(s),'json_dump':lambda x,indent=None:json.dumps(x,indent=indent,ensure_ascii=False,default=str),'safe':_safe,'now_ms':lambda:int(time.time()*1000),'chunk':_chunk,'flatten':_flatten,'uniq':_uniq,'pick':_pick,'omit':_omit,'clamp':_clamp,'uuid':_uuid,'randint':_randint,'b64encode':_b64e,'b64decode':_b64d,'now_iso':_now_iso,'coalesce':_coalesce,'repeat':_repeat,'times':_times,'find':_find,'find_index':_find_index,'pluck':_pluck,'index_by':_index_by,'sort_by':_sort_by,'is_null':_is_null,'is_list':_is_list,'is_dict':_is_dict,'is_string':_is_string,'is_number':_is_number,'is_bool':_is_bool,'identity':_identity,'tap':_tap,'pad_start':_pad_start,'pad_end':_pad_end,'lines':_lines,'words':_words,'floor':_floor,'ceil':_ceil,'log':_log,'exp':_exp,'pow':_pow,'get_path':_get_path,'deep_merge':_deep_merge,'take':_take,'drop':_drop,'partition':_partition,'count_by':_count_by,'first':_first,'last':_last,'is_empty':_is_empty,'compact':_compact,'defaults':_defaults,'invert':_invert,'to_pairs':_to_pairs,'from_pairs':_from_pairs,'sum_by':_sum_by,'avg':_avg,'capitalize':_capitalize,'snake_case':_snake_case,'kebab_case':_kebab_case,'slugify':_slugify,'truncate':_truncate,'union':_union,'intersection':_intersection,'difference':_difference,'has_path':_has_path,'set_path':_set_path,'map_values':_map_values,'map_keys':_map_keys,'pick_by':_pick_by,'omit_by':_omit_by,'shuffle':_shuffle,'product':_product,'median':_median,'parse_int':_parse_int,'parse_float':_parse_float,'strip_prefix':_strip_prefix,'strip_suffix':_strip_suffix,'sha256':_sha256,'url_encode':_url_encode,'url_decode':_url_decode,'html_escape':_html_escape,'title_case':_title_case,'center':_center,'min_by':_min_by,'max_by':_max_by,'without':_without,'xor':_xor,'zip_object':_zip_object,'ensure_list':_ensure_list,'ensure_dict':_ensure_dict,'size':_size,'random_choice':_random_choice,'sample_list':_sample_list,'clone':_clone,'deep_clone':_deep_clone,'deep_equal':_deep_equal,'nth':_nth,'initial':_initial,'rest':_rest,'group_by':_group_by,'frequencies':_count_by,'scan':_scan,'hex_encode':_hex_encode,'hex_decode':_hex_decode,'ensure_str':_ensure_str,'ensure_int':_ensure_int,'ensure_float':_ensure_float,'pipe':_pipe,'apply':_apply_fn,'gcd':_gcd,'lcm':_lcm,'sign':_sign,'is_even':_is_even,'is_odd':_is_odd,'lerp':_lerp,'rotate':_rotate,'interleave':_interleave,'windows':_window_list,'dedupe_by':_dedupe_by,'assoc':_assoc,'dissoc':_dissoc,'rename_keys':_rename_keys,'format_number':_format_number,'between':_between_val}
        for k,v in builtins.items():self.global_env.define(k,v,True)
        for k,v in build_standard_library(allow_process=allow_process,permissions=permissions).items():self.global_env.define(k,v,True)
        ai_ns,self.ai_service=build_ai_namespace();self.global_env.define('ai',ai_ns,True)
        from .web import build_web_namespace
        from .analysis import build_analysis_namespace
        from .interop import build_interop_namespace
        from .ux import build_ux_namespace
        from .numerics import build_stats_namespace
        self.web_namespace=build_web_namespace(self);self.global_env.define('web',self.web_namespace,True)
        self.analysis_namespace=build_analysis_namespace();self.global_env.define('analysis',self.analysis_namespace,True)
        self.interop_namespace=build_interop_namespace();self.global_env.define('interop',self.interop_namespace,True)
        self.ux_namespace=build_ux_namespace();self.global_env.define('ux',self.ux_namespace,True)
        self.stats_namespace=build_stats_namespace();self.global_env.define('stats',self.stats_namespace,True)
        self.tool_registry=ToolRegistry(self.invoke_user_function);self.agent_runtime=AgentRuntime(self.ai_service,self.tool_registry);self.global_env.define('tool',{'register':self.tool_registry.register,'list':self.tool_registry.list,'describe':self.tool_registry.describe,'call':self.tool_registry.call},True);self.global_env.define('agent',{'define':self.agent_runtime.define,'run':self.agent_runtime.run,'tool':self.agent_runtime.tool},True)
        self.skill_registry=SkillRegistry(self.base_dir);self.global_env.define('skill',{'load':self.skill_registry.load,'list':self.skill_registry.list,'get':self.skill_registry.get,'render':self.skill_registry.render},True)
    def _append(self,a,v):a.append(v);return a
    def _write(self,p,c):Path(p).write_text(str(c),encoding='utf-8');return p
    def stringify(self,v):
        if v is None:return 'null'
        if v is True:return 'true'
        if v is False:return 'false'
        if isinstance(v,float) and v.is_integer():return str(int(v))
        if isinstance(v,(list,dict)):return json.dumps(v,ensure_ascii=False)
        return str(v)
    def run(self,program,source_name='<input>'):
        old=self.source_name;self.source_name=source_name
        try:
            from .web import set_current_interpreter as set_web_current
            set_web_current(self)
            set_current_interpreter(self)
            result=None
            for stmt in program.statements:result=self.exec_stmt(stmt)
            return result
        finally:self.source_name=old
    def exec_block(self,body,env=None):
        old=self.env;self.env=env or Env(old)
        try:
            r=None
            for s in body:r=self.exec_stmt(s)
            return r
        finally:self.env=old
    def exec_stmt(self,s):
        if self.debug_hook:self.debug_hook(self,s)
        try:
            if isinstance(s,VarDecl):self.env.define(s.name,self.eval(s.value),s.constant);return None
            if isinstance(s,DestructureDecl):
                value=self.eval(s.value);self.bind_pattern(s.pattern,value,self.env,s.constant);return None
            if isinstance(s,MatchStmt):
                value=self.eval(s.value)
                for case in s.cases:
                    env=Env(self.env)
                    if not self.match_pattern(case.pattern,value,env):continue
                    if case.guard is not None:
                        old=self.env;self.env=env
                        try:
                            if not self.truth(self.eval(case.guard)):continue
                        finally:self.env=old
                    old=self.env;self.env=env
                    try:return self.exec_block(case.body,env)
                    finally:self.env=old
                return None
            if isinstance(s,Assign):
                val=self.eval(s.value)
                if s.op!='=':val=self.apply(s.op[0],self.read_target(s.target),val,s)
                return self.write_target(s.target,val,s)
            if isinstance(s,PrintStmt):self.output(self.stringify(self.eval(s.value)));return None
            if isinstance(s,ExprStmt):return self.eval(s.value)
            if isinstance(s,IfStmt):return self.exec_block(s.then_body if self.truth(self.eval(s.condition)) else (s.else_body or []))
            if isinstance(s,WhileStmt):
                while self.truth(self.eval(s.condition)):
                    try:self.exec_block(s.body)
                    except ContinueSignal:continue
                    except BreakSignal:break
                return None
            if isinstance(s,ForStmt):
                for v in self.eval(s.iterable):
                    e=Env(self.env)
                    if getattr(s,'pattern',None):self.bind_pattern(s.pattern,v,e)
                    else:e.define(s.name,v)
                    try:self.exec_block(s.body,e)
                    except ContinueSignal:continue
                    except BreakSignal:break
                return None
            if isinstance(s,FunctionStmt):self.env.define(s.name,UserFunction(s.params,s.body,self.env),True);return None
            if isinstance(s,ReturnStmt):raise ReturnSignal(self.eval(s.value) if s.value else None)
            if isinstance(s,BreakStmt):raise BreakSignal()
            if isinstance(s,ContinueStmt):raise ContinueSignal()
            if isinstance(s,ImportStmt):return self.import_file(s.path,s,s.alias)
            if isinstance(s,ExportStmt):
                if self.module_exports is None:raise PeaError('export is only valid inside an imported module',s.span,self.source_name)
                self.module_exports.add(s.name);return None
            if isinstance(s,AssertStmt):
                if not self.truth(self.eval(s.condition)):
                    message=self.stringify(self.eval(s.message)) if s.message else 'Assertion failed'
                    raise PeaError(message,s.span,self.source_name)
                return None
            if isinstance(s,ThrowStmt):raise PeaError(self.stringify(self.eval(s.value)),s.span,self.source_name)
            if isinstance(s,TryStmt):
                try:return self.exec_block(s.try_body)
                except PeaError as ex:
                    if s.catch_body is None:raise
                    catchenv=Env(self.env)
                    if s.catch_name:catchenv.define(s.catch_name,{'message':ex.message,'source':ex.source_name,'line':ex.span.line if ex.span else None,'column':ex.span.col if ex.span else None},True)
                    return self.exec_block(s.catch_body,catchenv)
                finally:
                    if s.finally_body is not None:self.exec_block(s.finally_body)
            raise PeaError(f'Unknown statement {type(s).__name__}',s.span,self.source_name)
        except (PeaError,ReturnSignal,BreakSignal,ContinueSignal):raise
        except Exception as ex:raise PeaError(str(ex),s.span,self.source_name) from ex
    def import_file(self,name,node,alias=None):
        path=resolve_module(name,self.base_dir,self.project_root,self.dependencies)
        if not path.is_file():raise PeaError(f"Module not found: {name}",node.span,self.source_name)
        if alias is None:
            if path in self.imported:return None
            self.imported.add(path);src=path.read_text(encoding='utf-8');oldbase=self.base_dir;oldskill=self.skill_registry.base_dir;self.base_dir=path.parent;self.skill_registry.base_dir=path.parent
            try:return self.run(parse_source(src,str(path)),str(path))
            finally:self.base_dir=oldbase;self.skill_registry.base_dir=oldskill
        src=path.read_text(encoding='utf-8');module_env=Env(self.global_env);oldenv=self.env;oldbase=self.base_dir;oldskill=self.skill_registry.base_dir;oldexports=self.module_exports
        self.env=module_env;self.base_dir=path.parent;self.skill_registry.base_dir=path.parent;self.module_exports=set()
        try:
            self.run(parse_source(src,str(path)),str(path));names=self.module_exports;values={n:module_env.values[n] for n in names if n in module_env.values};self.global_env.define(alias,values,True);return values
        finally:self.env=oldenv;self.base_dir=oldbase;self.skill_registry.base_dir=oldskill;self.module_exports=oldexports

    def invoke_user_function(self, f, args):
        required=sum(1 for p in f.params if getattr(p,'default',None) is None)
        if len(args)<required or len(args)>len(f.params):raise PeaError(f'Expected {required} to {len(f.params)} arguments, got {len(args)}')
        env=Env(f.closure);old=self.env;self.env=env
        try:
            for i,p in enumerate(f.params):
                value=args[i] if i<len(args) else self.eval(p.default)
                env.define(p.name,value)
            try:return self.exec_block(f.body,env)
            except ReturnSignal as result:return result.value
        finally:self.env=old

    def match_pattern(self, pattern, value, env):
        from .ast_nodes import WildcardPattern, LiteralPattern, VariablePattern, ListPattern, DictPattern, OrPattern
        if isinstance(pattern, WildcardPattern):
            return True
        if isinstance(pattern, LiteralPattern):
            return value == pattern.value
        if isinstance(pattern, VariablePattern):
            env.define(pattern.name, value, False)
            return True
        if isinstance(pattern, OrPattern):
            for p in pattern.patterns:
                trial = Env(env.parent if hasattr(env,'parent') else self.env)
                # bind into trial then copy? Simpler: try binding in a child env of env's parent
                saved = dict(env.values)
                ok = self.match_pattern(p, value, env)
                if ok:
                    return True
                env.values.clear(); env.values.update(saved)
            return False
        if isinstance(pattern, ListPattern):
            if not isinstance(value, list):
                return False
            if pattern.rest is None:
                if len(value) != len(pattern.elements):
                    return False
            else:
                if len(value) < len(pattern.elements):
                    return False
            for i, p in enumerate(pattern.elements):
                if not self.match_pattern(p, value[i], env):
                    return False
            if pattern.rest is not None:
                env.define(pattern.rest, value[len(pattern.elements):], False)
            return True
        if isinstance(pattern, DictPattern):
            if not isinstance(value, dict):
                return False
            for key, p in pattern.fields:
                if key not in value:
                    return False
                if not self.match_pattern(p, value[key], env):
                    return False
            return True
        return False

    def bind_pattern(self, pattern, value, env, const=False):
        from .ast_nodes import WildcardPattern, LiteralPattern, VariablePattern, ListPattern, DictPattern
        if isinstance(pattern, WildcardPattern):
            return
        if isinstance(pattern, LiteralPattern):
            return
        if isinstance(pattern, VariablePattern):
            env.define(pattern.name, value, const)
            return
        if isinstance(pattern, ListPattern):
            if not isinstance(value, list):
                return
            for i, p in enumerate(pattern.elements):
                if i < len(value):
                    self.bind_pattern(p, value[i], env, const)
            if pattern.rest is not None:
                env.define(pattern.rest, value[len(pattern.elements):], const)
            return
        if isinstance(pattern, DictPattern):
            if not isinstance(value, dict):
                return
            for key, p in pattern.fields:
                self.bind_pattern(p, value.get(key), env, const)
            return

    def run_parallel(self, expressions, node):
        # Parallel blocks are intentionally limited to expressions. Shared PeaLang
        # environment mutation inside the block is not supported in v0.5.0.
        if not expressions:return []
        def evaluate(expr):return self.eval(expr)
        try:
            with ThreadPoolExecutor(max_workers=min(8,len(expressions))) as pool:
                futures=[pool.submit(evaluate,e) for e in expressions]
                return [f.result() for f in futures]
        except PeaError:raise
        except Exception as ex:raise PeaError(str(ex),node.span,self.source_name) from ex

    def read_target(self,t):return self.eval(t)
    def write_target(self,t,v,node):
        if isinstance(t,Variable):return self.env.set(t.name,v,t.span,self.source_name)
        if isinstance(t,Index):
            target=self.eval(t.target);key=self.eval(t.index);target[key]=v;return v
        if isinstance(t,Property):
            target=self.eval(t.target)
            if isinstance(target,dict):target[t.name]=v;return v
            setattr(target,t.name,v);return v
        raise PeaError('Invalid assignment target',getattr(t,'span',node.span),self.source_name)
    def truth(self,v):return bool(v)
    def apply(self,op,a,b,node=None):
        try:
            return {'+':lambda:a+b,'-':lambda:a-b,'*':lambda:a*b,'/':lambda:a/b,'%':lambda:a%b,'**':lambda:a**b,'==':lambda:a==b,'!=':lambda:a!=b,'<':lambda:a<b,'<=':lambda:a<=b,'>':lambda:a>b,'>=':lambda:a>=b,'in':lambda:a in b,'not in':lambda:a not in b}[op]()
        except KeyError:raise PeaError(f'Unknown operator {op}',getattr(node,'span',None),self.source_name)
        except Exception as ex:raise PeaError(str(ex),getattr(node,'span',None),self.source_name) from ex
    def eval(self,e):
        if isinstance(e,Literal):return e.value
        if isinstance(e,FunctionExpr):return UserFunction(e.params,e.body,self.env)
        if isinstance(e,ComprehensionExpr):
            result=[]
            for value in self.eval(e.iterable):
                env=Env(self.env)
                if getattr(e,'pattern',None):self.bind_pattern(e.pattern,value,env)
                else:env.define(e.name,value)
                old=self.env;self.env=env
                try:
                    if e.condition is None or self.truth(self.eval(e.condition)):result.append(self.eval(e.value))
                finally:self.env=old
            return result
        if isinstance(e,DictComprehensionExpr):
            result={}
            for value in self.eval(e.iterable):
                env=Env(self.env)
                if getattr(e,'pattern',None):self.bind_pattern(e.pattern,value,env)
                else:env.define(e.name,value)
                old=self.env;self.env=env
                try:
                    if e.condition is None or self.truth(self.eval(e.condition)):result[self.eval(e.key)]=self.eval(e.value)
                finally:self.env=old
            return result
        if isinstance(e,MatchExpr):
            value=self.eval(e.value)
            for case in e.cases:
                env=Env(self.env)
                if not self.match_pattern(case.pattern,value,env):continue
                if case.guard is not None:
                    old=self.env;self.env=env
                    try:
                        if not self.truth(self.eval(case.guard)):continue
                    finally:self.env=old
                old=self.env;self.env=env
                try:
                    if getattr(case,'value',None) is not None:return self.eval(case.value)
                    if case.body:
                        r=None
                        for s in case.body:r=self.exec_stmt(s)
                        return r
                    return None
                finally:self.env=old
            return None
        if isinstance(e,Variable):return self.env.get(e.name,e.span,self.source_name)
        if isinstance(e,ListExpr):return [self.eval(x) for x in e.items]
        if isinstance(e,DictExpr):return {self.eval(k):self.eval(v) for k,v in e.pairs}
        if isinstance(e,InterpolatedString):return ''.join(x if isinstance(x,str) else self.stringify(self.eval(x)) for x in e.parts)
        if isinstance(e,ParallelExpr):return self.run_parallel(e.expressions,e)
        if isinstance(e,Unary):
            v=self.eval(e.value);return -v if e.op=='-' else not self.truth(v)
        if isinstance(e,Binary):
            if e.op=='and':
                left=self.eval(e.left);return self.eval(e.right) if self.truth(left) else False
            if e.op=='or':
                left=self.eval(e.left);return left if self.truth(left) else self.eval(e.right)
            if e.op=='??':
                left=self.eval(e.left);return left if left is not None else self.eval(e.right)
            return self.apply(e.op,self.eval(e.left),self.eval(e.right),e)
        if isinstance(e,Index):
            try:return self.eval(e.target)[self.eval(e.index)]
            except Exception as ex:raise PeaError(str(ex),e.span,self.source_name) from ex
        if isinstance(e,Property):
            target=self.eval(e.target)
            try:return target[e.name] if isinstance(target,dict) else getattr(target,e.name)
            except (KeyError,AttributeError) as ex:raise PeaError(f"Property '{e.name}' not found",e.span,self.source_name) from ex
        if isinstance(e,Call):
            f=self.eval(e.callee);args=[self.eval(x) for x in e.args]
            if isinstance(f,UserFunction):return self.invoke_user_function(f,args)
            if callable(f):
                try:return f(*args)
                except PeaError:raise
                except Exception as ex:raise PeaError(str(ex),e.span,self.source_name) from ex
            raise PeaError('Value is not callable',e.span,self.source_name)
        if isinstance(e,OptionalProperty):
            target=self.eval(e.target)
            if target is None:return None
            try:return target[e.name] if isinstance(target,dict) else getattr(target,e.name)
            except (KeyError,AttributeError):return None
        if isinstance(e,OptionalIndex):
            target=self.eval(e.target)
            if target is None:return None
            try:return target[self.eval(e.index)]
            except Exception:return None
        if isinstance(e,OptionalCall):
            callee=self.eval(e.callee)
            if callee is None:return None
            args=[self.eval(x) for x in e.args]
            if isinstance(callee,UserFunction):return self.invoke_user_function(callee,args)
            if callable(callee):
                try:return callee(*args)
                except Exception:return None
            return None
        raise PeaError(f'Unknown expression {type(e).__name__}',getattr(e,'span',None),self.source_name)
