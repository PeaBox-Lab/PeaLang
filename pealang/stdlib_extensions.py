"""Standard library modules for PeaLang v2.40+.

Additional standard library modules covering common use cases:
- std.sql: SQL query building
- std.cache: In-memory caching with TTL
- std.uuid: UUID generation
- std.cli: Command-line argument parsing
- std.config: Configuration file parsing (ini, yaml, toml, json)
- std.template: Simple template engine
- std.serialize: Serialization (json, csv, xml-like)
- std.graph: Graph data structures and algorithms
- std.queue: Queue and priority queue
- std.env: Environment variable handling
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json as _json
import csv as _csv
import hashlib
import os
import re as _re
import secrets
import string
import time
import urllib.parse
from collections import OrderedDict, deque
from heapq import heappush, heappop


# ============================================================================
# std.sql - SQL Query Builder
# ============================================================================

def _sql_select(table: str, columns: list[str] | str = '*', where: str | None = None,
                order_by: str | None = None, limit: int | None = None,
                offset: int | None = None, group_by: str | None = None,
                having: str | None = None) -> str:
    """Build a SELECT SQL query."""
    cols = columns if isinstance(columns, str) else ', '.join(columns)
    q = f"SELECT {cols} FROM {table}"
    if where:
        q += f" WHERE {where}"
    if group_by:
        q += f" GROUP BY {group_by}"
    if having:
        q += f" HAVING {having}"
    if order_by:
        q += f" ORDER BY {order_by}"
    if limit is not None:
        q += f" LIMIT {limit}"
    if offset is not None:
        q += f" OFFSET {offset}"
    return q


def _sql_insert(table: str, data: dict[str, Any]) -> str:
    """Build an INSERT SQL query."""
    cols = ', '.join(data.keys())
    vals = ', '.join(f"'{v}'" if isinstance(v, str) else str(v) for v in data.values())
    return f"INSERT INTO {table} ({cols}) VALUES ({vals})"


def _sql_update(table: str, data: dict[str, Any], where: str) -> str:
    """Build an UPDATE SQL query."""
    sets = ', '.join(f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}"
                     for k, v in data.items())
    return f"UPDATE {table} SET {sets} WHERE {where}"


def _sql_delete(table: str, where: str) -> str:
    """Build a DELETE SQL query."""
    return f"DELETE FROM {table} WHERE {where}"


def _sql_create_table(table: str, columns: dict[str, str]) -> str:
    """Build a CREATE TABLE SQL query."""
    cols = ', '.join(f"{c} {t}" for c, t in columns.items())
    return f"CREATE TABLE IF NOT EXISTS {table} ({cols})"


def _sql_drop_table(table: str) -> str:
    """Build a DROP TABLE SQL query."""
    return f"DROP TABLE IF EXISTS {table}"


# ============================================================================
# std.cache - In-memory cache with TTL
# ============================================================================

class _CacheEntry:
    def __init__(self, value: Any, ttl: int | None = None):
        self.value = value
        self.expiry = None if ttl is None else time.time() + ttl

    def is_expired(self) -> bool:
        if self.expiry is None:
            return False
        return time.time() > self.expiry


class _Cache:
    def __init__(self):
        self._store: dict[str, _CacheEntry] = {}

    def get(self, key: str, default: Any = None) -> Any:
        entry = self._store.get(key)
        if entry is None:
            return default
        if entry.is_expired():
            del self._store[key]
            return default
        return entry.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._store[key] = _CacheEntry(value, ttl)

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> None:
        self._store.clear()

    def has(self, key: str) -> bool:
        entry = self._store.get(key)
        if entry is None:
            return False
        if entry.is_expired():
            del self._store[key]
            return False
        return True

    def keys(self) -> list[str]:
        self._cleanup()
        return list(self._store.keys())

    def _cleanup(self):
        expired = [k for k, v in self._store.items() if v.is_expired()]
        for k in expired:
            del self._store[k]

    def size(self) -> int:
        self._cleanup()
        return len(self._store)


_cache_instance = _Cache()


def _cache_get(key: str, default: Any = None) -> Any:
    return _cache_instance.get(key, default)


def _cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    _cache_instance.set(key, value, ttl)


def _cache_delete(key: str) -> bool:
    return _cache_instance.delete(key)


def _cache_clear() -> None:
    _cache_instance.clear()


def _cache_has(key: str) -> bool:
    return _cache_instance.has(key)


def _cache_keys() -> list[str]:
    return _cache_instance.keys()


def _cache_size() -> int:
    return _cache_instance.size()


# ============================================================================
# std.uuid - UUID generation
# ============================================================================

def _uuid_v4() -> str:
    return str(secrets.token_hex(16)).replace('-', '')[:32]  # simplified
    # Actually use uuid4 properly


def _uuid_v4_full() -> str:
    import uuid as _uuid_mod
    return str(_uuid_mod.uuid4())


def _uuid_v1() -> str:
    import uuid as _uuid_mod
    return str(_uuid_mod.uuid1())


def _uuid_v3(namespace: str, name: str) -> str:
    import uuid as _uuid_mod
    return str(_uuid_mod.uuid3(_uuid_mod.UUID(namespace), name))


def _uuid_v5(namespace: str, name: str) -> str:
    import uuid as _uuid_mod
    return str(_uuid_mod.uuid5(_uuid_mod.UUID(namespace), name))


def _uuid_random() -> str:
    return str(secrets.token_hex(16))


# ============================================================================
# std.cli - Command-line argument parsing
# ============================================================================

def _cli_parse(args: list[str] | None = None) -> dict[str, Any]:
    """Parse command-line arguments into a dict.
    Supports --flag, --flag=value, -f value, --flag value formats."""
    import sys as _sys
    args = list(args) if args is not None else _sys.argv[1:]
    result: dict[str, Any] = {}
    positional: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('--'):
            if '=' in arg:
                key, val = arg[2:].split('=', 1)
                result[key] = val
            else:
                key = arg[2:]
                if i + 1 < len(args) and not args[i + 1].startswith('-'):
                    result[key] = args[i + 1]
                    i += 1
                else:
                    result[key] = True
        elif arg.startswith('-') and len(arg) == 2:
            key = arg[1]
            if i + 1 < len(args) and not args[i + 1].startswith('-'):
                result[key] = args[i + 1]
                i += 1
            else:
                result[key] = True
        else:
            positional.append(arg)
        i += 1
    result['_positional'] = positional
    return result


def _cli_has(flag: str) -> bool:
    import sys as _sys
    return flag in _sys.argv or f"--{flag}" in _sys.argv


def _cli_get(flag: str, default: Any = None) -> Any:
    import sys as _sys
    args = _sys.argv[1:]
    for i, a in enumerate(args):
        if a == f"--{flag}" and i + 1 < len(args):
            return args[i + 1]
        if a.startswith(f"--{flag}="):
            return a.split('=', 1)[1]
        if a == f"-{flag[0]}" and len(flag) == 1 and i + 1 < len(args):
            return args[i + 1]
    return default


# ============================================================================
# std.config - Configuration file parsing
# ============================================================================

def _config_parse_ini(path: str) -> dict[str, dict[str, str]]:
    """Parse an INI file into a nested dict."""
    import configparser as _cp
    parser = _cp.ConfigParser()
    parser.read(path)
    return {section: dict(parser[section]) for section in parser.sections()}


def _config_parse_json(path: str) -> dict[str, Any]:
    """Parse a JSON file."""
    import json as _json
    return _json.loads(Path(path).read_text(encoding='utf-8'))


def _config_parse_toml(path: str) -> dict[str, Any]:
    """Parse a TOML file."""
    try:
        import tomllib as _tomllib
    except ImportError:
        import tomli as _tomllib
    with open(path, 'rb') as f:
        return _tomllib.load(f)


def _config_parse_yaml(path: str) -> dict[str, Any]:
    """Parse a YAML file."""
    try:
        import yaml as _yaml
    except ImportError:
        raise PeaError("PyYAML is required for YAML parsing. Install with: pip install pyyaml")
    with open(path, 'r', encoding='utf-8') as f:
        return _yaml.safe_load(f)


def _config_get(config: dict, key: str, default: Any = None) -> Any:
    """Get a value from a nested config using dot notation."""
    keys = key.split('.')
    val = config
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            return default
    return val


# ============================================================================
# std.template - Simple template engine
# ============================================================================

def _template_render(template: str, context: dict[str, Any]) -> str:
    """Render a template with {{ variable }} and {% block %} support."""
    result = str(template)

    # Replace {{ variable }}
    def _replace_var(match):
        key = match.group(1).strip()
        parts = key.split('.')
        val = context
        try:
            for p in parts:
                val = val[p]
            return str(val)
        except (KeyError, TypeError, IndexError):
            return match.group(0)  # Leave unresolved

    result = _re.sub(r'\{\{\s*(.+?)\s*\}\}', _replace_var, result)

    # Replace {% if condition %}...{% endif %} blocks (simple)
    def _replace_if(match):
        condition = match.group(1).strip()
        body = match.group(2)
        # Simple truthiness check
        truthy = bool(context.get(condition, False))
        return body if truthy else ''

    result = _re.sub(r'\{\%\s*if\s+(\w+)\s*\%\}(.*?)\{\%\s*endif\s*\%\}', _replace_if, result, flags=_re.DOTALL)

    return result


def _template_render_file(path: str, context: dict[str, Any]) -> str:
    """Render a template file."""
    return _template_render(Path(path).read_text(encoding='utf-8'), context)


# ============================================================================
# std.serialize - Serialization helpers
# ============================================================================

def _serialize_json(obj: Any, indent: int | None = 2) -> str:
    return _json.dumps(obj, ensure_ascii=False, indent=indent)


def _serialize_json_loads(s: str) -> Any:
    return _json.loads(s)


def _serialize_csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ''
    import io as _io
    output = _io.StringIO()
    writer = _csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _serialize_csv_parse(s: str) -> list[dict[str, Any]]:
    import io as _io
    reader = _csv.DictReader(_io.StringIO(s))
    return [dict(row) for row in reader]


# ============================================================================
# std.graph - Graph data structures and algorithms
# ============================================================================

class _Graph:
    def __init__(self, directed: bool = False):
        self._adj: dict[str, list[str]] = {}
        self._directed = directed

    def add_node(self, node: str) -> None:
        if node not in self._adj:
            self._adj[node] = []

    def add_edge(self, u: str, v: str) -> None:
        self.add_node(u)
        self.add_node(v)
        self._adj[u].append(v)
        if not self._directed:
            self._adj[v].append(u)

    def nodes(self) -> list[str]:
        return list(self._adj.keys())

    def neighbors(self, node: str) -> list[str]:
        return list(self._adj.get(node, []))

    def has_node(self, node: str) -> bool:
        return node in self._adj

    def has_edge(self, u: str, v: str) -> bool:
        return v in self._adj.get(u, [])

    def bfs(self, start: str) -> list[str]:
        from collections import deque as _deque
        visited = set()
        queue = _deque([start])
        visited.add(start)
        order = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in self._adj.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return order

    def dfs(self, start: str) -> list[str]:
        visited = set()
        order = []

        def _dfs(node: str):
            visited.add(node)
            order.append(node)
            for neighbor in self._adj.get(node, []):
                if neighbor not in visited:
                    _dfs(neighbor)

        _dfs(start)
        return order

    def shortest_path(self, start: str, end: str) -> list[str] | None:
        from collections import deque as _deque
        if start == end:
            return [start]
        visited = {start}
        queue = _deque([(start, [start])])
        while queue:
            node, path = queue.popleft()
            for neighbor in self._adj.get(node, []):
                if neighbor == end:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None


def _graph_create(directed: bool = False) -> _Graph:
    return _Graph(directed)


# ============================================================================
# std.queue - Queue and Priority Queue
# ============================================================================

class _Queue:
    def __init__(self):
        self._items: deque = deque()

    def enqueue(self, item: Any) -> None:
        self._items.append(item)

    def dequeue(self) -> Any:
        if not self._items:
            raise PeaError("Queue is empty")
        return self._items.popleft()

    def peek(self) -> Any:
        if not self._items:
            raise PeaError("Queue is empty")
        return self._items[0]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def size(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()


class _PriorityQueue:
    def __init__(self):
        self._heap: list = []
        self._counter = 0

    def push(self, item: Any, priority: int = 0) -> None:
        heappush(self._heap, (-priority, self._counter, item))
        self._counter += 1

    def pop(self) -> Any:
        if not self._heap:
            raise PeaError("Priority queue is empty")
        return heappop(self._heap)[2]

    def peek(self) -> Any:
        if not self._heap:
            raise PeaError("Priority queue is empty")
        return self._heap[0][2]

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def size(self) -> int:
        return len(self._heap)


def _queue_create() -> _Queue:
    return _Queue()


def _priority_queue_create() -> _PriorityQueue:
    return _PriorityQueue()


# ============================================================================
# std.env - Environment variable handling
# ============================================================================

def _env_get(name: str, default: Any = None) -> Any:
    return os.environ.get(name, default)


def _env_set(name: str, value: str) -> None:
    os.environ[name] = str(value)


def _env_unset(name: str) -> None:
    os.environ.pop(name, None)


def _env_has(name: str) -> bool:
    return name in os.environ


def _env_keys() -> list[str]:
    return list(os.environ.keys())
