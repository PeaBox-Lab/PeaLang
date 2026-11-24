"""PeaLang stable standard library registry (0.35)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import csv as _csv
import datetime as _dt
import hashlib
import hmac
import json as _json
import logging as _logging
import math as _math
import os
import re as _re
import secrets
import statistics
import urllib.parse
import urllib.request
import urllib.error
import concurrent.futures
import warnings
from .errors import PeaError
from .extension_lifecycle import ExtensionLifecycleManager, create_lifecycle_manager
from .stdlib_extensions import (
    _sql_select, _sql_insert, _sql_update, _sql_delete, _sql_create_table, _sql_drop_table,
    _cache_get, _cache_set, _cache_delete, _cache_clear, _cache_has, _cache_keys, _cache_size,
    _uuid_v4, _uuid_v4_full, _uuid_v1, _uuid_v3, _uuid_v5, _uuid_random,
    _cli_parse, _cli_has, _cli_get,
    _config_parse_ini, _config_parse_json, _config_parse_toml, _config_parse_yaml, _config_get,
    _template_render, _template_render_file,
    _serialize_json, _serialize_json_loads, _serialize_csv, _serialize_csv_parse,
    _graph_create,
    _queue_create, _priority_queue_create,
    _env_get, _env_set, _env_unset, _env_has, _env_keys,
)


class Namespace(dict):
    def __init__(self, *a, legacy_call=None, **k):
        super().__init__(*a, **k)
        self.legacy_call = legacy_call

    def __getattribute__(self, name):
        # Private attributes go straight to normal lookup
        if name.startswith('_'):
            return super().__getattribute__(name)
        # Check if it's a key in our dict first
        if name in self:
            return self[name]
        # Fall back to normal attribute access (methods, etc.)
        return super().__getattribute__(name)

    def __call__(self, *a):
        if self.legacy_call is None:
            raise PeaError('Namespace is not directly callable')
        return self.legacy_call(*a)

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError(f"Namespace has no attribute '{name}'")


def _ns(legacy_call=None, **x):
    return Namespace(x, legacy_call=legacy_call)


@dataclass(frozen=True)
class StdModuleSpec:
    name: str
    stability: str = 'Stable'
    permissions: tuple[str, ...] = ()
    description: str = ''
    deprecated: bool = False
    since: str = '0.35'
    replacement: str | None = None


STDLIB_VERSION = '1.0'

MODULES = {
    'std.collections': StdModuleSpec('std.collections', description='Collection transforms and queries'),
    'std.string': StdModuleSpec('std.string', description='Unicode string helpers'),
    'std.math': StdModuleSpec('std.math', description='Mathematics and statistics'),
    'std.datetime': StdModuleSpec('std.datetime', description='UTC-oriented date/time helpers'),
    'std.json': StdModuleSpec('std.json', description='JSON encode/decode'),
    'std.csv': StdModuleSpec('std.csv', permissions=('file.read', 'file.write'), description='CSV file IO'),
    'std.regex': StdModuleSpec('std.regex', description='Regular expressions'),
    'std.file': StdModuleSpec('std.file', permissions=('file.read', 'file.write'), description='Controlled filesystem IO'),
    'std.path': StdModuleSpec('std.path', description='Path manipulation'),
    'std.http': StdModuleSpec('std.http', permissions=('http.request',), description='HTTP client'),
    'std.crypto': StdModuleSpec('std.crypto', description='Hashing, HMAC and random tokens'),
    'std.logging': StdModuleSpec('std.logging', permissions=('log',), description='Host logging'),
    'std.testing': StdModuleSpec('std.testing', description='Assertions for libraries'),
    'std.concurrent': StdModuleSpec('std.concurrent', permissions=('concurrent',), description='Bounded parallel map'),
    'std.web': StdModuleSpec('std.web', description='Web application toolkit'),
    'std.analysis': StdModuleSpec('std.analysis', description='Data analysis helpers'),
    'std.interop': StdModuleSpec('std.interop', description='Cross-language interoperability'),
    'std.ux': StdModuleSpec('std.ux', description='User-experience and diagnostics helpers'),
    'std.stats': StdModuleSpec('std.stats', description='Numerical, statistical and modelling toolkit'),
    'std.sql': StdModuleSpec('std.sql', description='SQL query builder'),
    'std.cache': StdModuleSpec('std.cache', description='In-memory cache with TTL support'),
    'std.uuid': StdModuleSpec('std.uuid', description='UUID generation'),
    'std.cli': StdModuleSpec('std.cli', description='Command-line argument parsing'),
    'std.config': StdModuleSpec('std.config', description='Configuration file parsing (ini, json, toml, yaml)'),
    'std.template': StdModuleSpec('std.template', description='Simple template engine'),
    'std.serialize': StdModuleSpec('std.serialize', description='Serialization (json, csv)'),
    'std.graph': StdModuleSpec('std.graph', description='Graph data structures and algorithms'),
    'std.queue': StdModuleSpec('std.queue', description='Queue and priority queue data structures'),
    'std.env': StdModuleSpec('std.env', description='Environment variable handling'),
}


def stdlib_manifest():
    return {
        'version': STDLIB_VERSION,
        'modules': {
            k: {
                'stability': v.stability,
                'permissions': list(v.permissions),
                'description': v.description,
                'deprecated': v.deprecated,
                'since': v.since,
                'replacement': v.replacement,
            }
            for k, v in MODULES.items()
        }
    }


def _parent(p):
    Path(p).expanduser().parent.mkdir(parents=True, exist_ok=True)


def _text(v):
    return v if isinstance(v, str) else str(v)


def _file_read(p):
    return Path(p).expanduser().read_text(encoding='utf-8')


def _file_write(p, c):
    p = Path(p).expanduser()
    _parent(p)
    p.write_text(_text(c), encoding='utf-8')
    return str(p)


def _file_append(p, c):
    p = Path(p).expanduser()
    _parent(p)
    p.open('a', encoding='utf-8').write(_text(c))
    return str(p)


def _json_stringify(v, indent=2):
    return _json.dumps(v, ensure_ascii=False, indent=None if int(indent) == 0 else int(indent))


def _http(method, url, body=None, headers=None, timeout=15):
    data = None
    headers = dict(headers or {})
    if body is not None:
        data = (body if isinstance(body, bytes) else (_text(body) if isinstance(body, str) else _json.dumps(body))).encode()
        headers.setdefault('Content-Type', 'application/json')
    req = urllib.request.Request(str(url), data=data, headers={str(k): str(v) for k, v in headers.items()}, method=str(method).upper())
    try:
        with urllib.request.urlopen(req, timeout=float(timeout)) as r:
            raw = r.read()
            return {'status': r.status, 'ok': 200 <= r.status < 300, 'headers': dict(r.headers.items()), 'text': raw.decode('utf-8', 'replace'), 'url': r.geturl()}
    except urllib.error.HTTPError as e:
        return {'status': e.code, 'ok': False, 'headers': dict(e.headers.items()), 'text': e.read().decode('utf-8', 'replace'), 'url': e.geturl()}


def _current_interpreter():
    try:
        from .interpreter import CURRENT_INTERPRETER
        return CURRENT_INTERPRETER
    except Exception:
        return None


def _invoke_if_user_function(fn, arg):
    try:
        from .interpreter import UserFunction
    except Exception:
        UserFunction = None
    interp = _current_interpreter()
    if UserFunction is not None and isinstance(fn, UserFunction) and interp is not None:
        return interp.invoke_user_function(fn, [arg])
    return fn(arg)


def _concurrent_map(fn, items, workers=4):
    from concurrent.futures import ThreadPoolExecutor
    vals = list(items)
    with ThreadPoolExecutor(max_workers=max(1, min(32, int(workers)))) as pool:
        return list(pool.map(lambda x: _invoke_if_user_function(fn, x), vals))


def _module_values():
    from .web import build_web_namespace
    from .analysis import build_analysis_namespace
    from .interop import build_interop_namespace
    from .ux import build_ux_namespace
    from .numerics import build_stats_namespace
    return {
        'std.collections': _ns(
            first=lambda x, d=None: x[0] if x else d,
            last=lambda x, d=None: x[-1] if x else d,
            unique=lambda x: list(dict.fromkeys(x)),
            contains=lambda x, v: v in x,
            sort=lambda x: sorted(x),
            reverse=lambda x: list(reversed(x)),
            flatten=lambda x: [v for a in x for v in a],
            keys=lambda d: list(d.keys()),
            values=lambda d: list(d.values()),
            map=lambda f, x: [_invoke_if_user_function(f, v) for v in x],
            filter=lambda f, x: [v for v in x if _invoke_if_user_function(f, v)],
            any=lambda x: any(x),
            all=lambda x: all(x),
            chunk=lambda x, n: [x[i:i+n] for i in range(0, len(x), n)],
            take=lambda x, n: x[:n],
            drop=lambda x, n: x[n:],
            partition=lambda f, x: ([v for v in x if _invoke_if_user_function(f, v)], [v for v in x if not _invoke_if_user_function(f, v)]),
        ),
        'std.string': _ns(
            length=lambda s: len(str(s)),
            upper=lambda s: str(s).upper(),
            lower=lambda s: str(s).lower(),
            trim=lambda s: str(s).strip(),
            split=lambda s, sep=None: str(s).split(sep),
            join=lambda sep, x: str(sep).join(map(str, x)),
            starts_with=lambda s, p: str(s).startswith(str(p)),
            ends_with=lambda s, p: str(s).endswith(str(p)),
            replace=lambda s, a, b: str(s).replace(str(a), str(b)),
            capitalize=lambda s: str(s).capitalize(),
            snake_case=lambda s: _re.sub(r'([A-Z])', r'_\1', str(s)).lower().lstrip('_'),
            kebab_case=lambda s: _re.sub(r'([A-Z])', r'-\1', str(s)).lower().lstrip('-'),
            slugify=lambda s: _re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-'),
            pad_start=lambda s, w, f=' ': str(s).rjust(w, f),
            pad_end=lambda s, w, f=' ': str(s).ljust(w, f),
            contains=lambda s, sub: sub in str(s),
        ),
        'std.math': _ns(
            abs=abs,
            min=min,
            max=max,
            round=round,
            sqrt=_math.sqrt,
            floor=_math.floor,
            ceil=_math.ceil,
            power=pow,
            mean=lambda x: statistics.mean(x),
            median=lambda x: statistics.median(x),
            pi=_math.pi,
            sin=_math.sin,
            cos=_math.cos,
            tan=_math.tan,
            log=_math.log,
            exp=_math.exp,
            clamp=lambda v, lo, hi: max(lo, min(v, hi)),
        ),
        'std.datetime': _ns(
            now=lambda: _dt.datetime.now(_dt.timezone.utc).isoformat(),
            today=lambda: _dt.date.today().isoformat(),
            parse=lambda v: _dt.datetime.fromisoformat(str(v).replace('Z', '+00:00')).isoformat(),
            format=lambda v, f: _dt.datetime.fromisoformat(str(v).replace('Z', '+00:00')).strftime(str(f)),
            add_days=lambda v, n: (_dt.datetime.fromisoformat(str(v).replace('Z', '+00:00')) + _dt.timedelta(days=float(n))).isoformat(),
            timestamp=lambda: _dt.datetime.now(_dt.timezone.utc).timestamp(),
        ),
        'std.json': _ns(
            legacy_call=lambda v: _json_stringify(v),
            parse=_json.loads,
            stringify=_json_stringify,
            read=lambda p: _json.loads(_file_read(p)),
            write=lambda p, v, indent=2: _file_write(p, _json_stringify(v, indent)),
        ),
        'std.csv': _ns(
            read=lambda p: list(_csv.DictReader(Path(p).open(newline='', encoding='utf-8-sig'))),
            write=lambda p, rows: _file_write(p, _csv.DictWriter(Path(p).open('w', newline='', encoding='utf-8'), fieldnames=rows[0].keys()).writerows(rows) if rows else ''),
        ),
        'std.regex': _ns(
            match=lambda p, t: _re.search(str(p), str(t)) is not None,
            find=lambda p, t: _re.findall(str(p), str(t)),
            replace=lambda p, r, t, count=0: _re.sub(str(p), str(r), str(t), count=int(count)),
            split=lambda p, t: _re.split(str(p), str(t)),
        ),
        'std.file': _ns(
            read=_file_read,
            write=_file_write,
            append=_file_append,
            exists=lambda p: Path(p).exists(),
            list=lambda p='.': sorted(str(x) for x in Path(p).iterdir()),
            mkdir=lambda p: str(Path(p).mkdir(parents=True, exist_ok=True) or p),
            delete=lambda p: (Path(p).unlink(missing_ok=True) or True),
            copy=lambda src, dst: (_parent(dst), Path(dst).write_bytes(Path(src).read_bytes())),
            size=lambda p: Path(p).stat().st_size,
        ),
        'std.path': _ns(
            join=lambda *x: str(Path(*map(str, x))),
            name=lambda p: Path(p).name,
            stem=lambda p: Path(p).stem,
            extension=lambda p: Path(p).suffix,
            parent=lambda p: str(Path(p).parent),
            absolute=lambda p: str(Path(p).expanduser().resolve()),
            relative=lambda p, base: str(Path(p).relative_to(Path(base))),
            normalize=lambda p: str(Path(p).resolve()),
        ),
        'std.http': _ns(
            request=_http,
            get=lambda u, h=None, t=15: _http('GET', u, None, h, t),
            post=lambda u, b=None, h=None, t=15: _http('POST', u, b, h, t),
            put=lambda u, b=None, h=None, t=15: _http('PUT', u, b, h, t),
            delete=lambda u, h=None, t=15: _http('DELETE', u, None, h, t),
            json=lambda r: _json.loads(r['text']),
            urlencode=urllib.parse.urlencode,
            parse_query=lambda s: dict(urllib.parse.parse_qsl(str(s))),
        ),
        'std.crypto': _ns(
            sha256=lambda v: hashlib.sha256(_text(v).encode()).hexdigest(),
            sha512=lambda v: hashlib.sha512(_text(v).encode()).hexdigest(),
            hmac_sha256=lambda k, v: hmac.new(_text(k).encode(), _text(v).encode(), hashlib.sha256).hexdigest(),
            token_hex=lambda n=32: secrets.token_hex(int(n)),
            token_urlsafe=lambda n=32: secrets.token_urlsafe(int(n)),
        ),
        'std.logging': _ns(
            debug=lambda m: (_logging.getLogger('pealang').debug(_text(m)) or None),
            info=lambda m: (_logging.getLogger('pealang').info(_text(m)) or None),
            warning=lambda m: (_logging.getLogger('pealang').warning(_text(m)) or None),
            error=lambda m: (_logging.getLogger('pealang').error(_text(m)) or None),
            critical=lambda m: (_logging.getLogger('pealang').critical(_text(m)) or None),
        ),
        'std.testing': _ns(
            expect=lambda c, m='Expectation failed': True if c else (_ for _ in ()).throw(PeaError(str(m))),
            equal=lambda a, b: a == b,
            assert_eq=lambda a, b, m='': None if a == b else (_ for _ in ()).throw(PeaError(f"{m}: {a} != {b}")),
            assert_ne=lambda a, b, m='': None if a != b else (_ for _ in ()).throw(PeaError(f"{m}: {a} == {b}")),
            assert_true=lambda v, m='': None if v else (_ for _ in ()).throw(PeaError(f"{m}: expected truthy")),
            assert_false=lambda v, m='': None if not v else (_ for _ in ()).throw(PeaError(f"{m}: expected falsy")),
            assert_raises=lambda f, exc_type=Exception: (lambda: f(), (_ for _ in ()).throw(PeaError("Expected exception")))[1] if True else None,
        ),
        'std.concurrent': _ns(
            map=_concurrent_map,
            gather=lambda *fns: [f() for f in fns],
        ),
        'std.web': build_web_namespace(None),
        'std.analysis': build_analysis_namespace(),
        'std.interop': build_interop_namespace(),
        'std.ux': build_ux_namespace(),
        'std.stats': build_stats_namespace(),
        'std.sql': _ns(
            select=_sql_select,
            insert=_sql_insert,
            update=_sql_update,
            delete=_sql_delete,
            create_table=_sql_create_table,
            drop_table=_sql_drop_table,
        ),
        'std.cache': _ns(
            get=_cache_get,
            set=_cache_set,
            delete=_cache_delete,
            clear=_cache_clear,
            has=_cache_has,
            keys=_cache_keys,
            size=_cache_size,
        ),
        'std.uuid': _ns(
            v4=_uuid_v4,
            v4_full=_uuid_v4_full,
            v1=_uuid_v1,
            v3=_uuid_v3,
            v5=_uuid_v5,
            random=_uuid_random,
        ),
        'std.cli': _ns(
            parse=_cli_parse,
            has=_cli_has,
            get=_cli_get,
        ),
        'std.config': _ns(
            parse_ini=_config_parse_ini,
            parse_json=_config_parse_json,
            parse_toml=_config_parse_toml,
            parse_yaml=_config_parse_yaml,
            get=_config_get,
        ),
        'std.template': _ns(
            render=_template_render,
            render_file=_template_render_file,
        ),
        'std.serialize': _ns(
            json_dumps=_serialize_json,
            json_loads=_serialize_json_loads,
            csv_dumps=_serialize_csv,
            csv_loads=_serialize_csv_parse,
        ),
        'std.graph': _ns(
            create=_graph_create,
        ),
        'std.queue': _ns(
            create=_queue_create,
            priority_create=_priority_queue_create,
        ),
        'std.env': _ns(
            get=_env_get,
            set=_env_set,
            unset=_env_unset,
            has=_env_has,
            keys=_env_keys,
        ),
    }


def build_standard_library(allow_process=False, permissions=None):
    values = _module_values()
    allowed = set(permissions or ())

    std = {}
    for name, module_spec in MODULES.items():
        short = name.split('.', 1)[1]
        required = set(module_spec.permissions)
        if module_spec.deprecated:
            warnings.warn(f"Module '{name}' is deprecated{f'; use {module_spec.replacement}' if module_spec.replacement else ''}", DeprecationWarning, stacklevel=2)
        std[short] = values[name] if required.issubset(allowed) else _guard(values[name], required - allowed, name)

    legacy = {
        'file': std['file'],
        'path': std['path'],
        'json': std['json'],
        'csv': std['csv'],
        'datetime': std['datetime'],
        'regex': std['regex'],
        'http': std['http'],
        'task': std['concurrent'],
    }
    return {'std': _ns(**std), **legacy}


def _guard(ns, missing, module):
    def denied(*a, **k):
        raise PeaError(f"Permission '{sorted(missing)[0]}' is required for '{module}'")
    return _ns(**{k: (denied if callable(v) else v) for k, v in ns.items()})