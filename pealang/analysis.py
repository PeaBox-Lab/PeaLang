"""Data analysis toolkit for PeaLang."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable


def _rows(data: Any) -> list[dict[str, Any]]:
    if data is None:
        return []
    if hasattr(data, "to_dicts"):
        try:
            return [dict(x) for x in data.to_dicts()]
        except Exception:
            pass
    if hasattr(data, "rows"):
        try:
            return [dict(x) for x in data.rows]
        except Exception:
            pass
    if isinstance(data, list):
        if all(isinstance(x, dict) for x in data):
            return [dict(x) for x in data]
        return [{"index": i, "value": x} for i, x in enumerate(data)]
    if isinstance(data, dict):
        keys = list(data.keys())
        if all(isinstance(v, (list, tuple)) for v in data.values()):
            n = max((len(v) for v in data.values()), default=0)
            out = []
            for i in range(n):
                out.append({k: (data[k][i] if i < len(data[k]) else None) for k in keys})
            return out
        return [dict(data)]
    return [{"value": data}]


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def columns(data: Any) -> list[str]:
    rows = _rows(data)
    seen = []
    for row in rows:
        for key in row:
            if key not in seen:
                seen.append(key)
    return seen


def profile(data: Any) -> dict[str, Any]:
    rows = _rows(data)
    cols = columns(rows)
    result = {"rows": len(rows), "columns": len(cols), "fields": {}}
    for col in cols:
        values = [row.get(col) for row in rows]
        nums = [v for v in (_numeric(x) for x in values) if v is not None]
        missing = sum(1 for v in values if v is None or v == "")
        field = {
            "missing": missing,
            "missing_rate": (missing / len(values)) if values else 0.0,
            "distinct": len(set(map(str, values))),
            "sample": values[:5],
        }
        if nums:
            field.update({
                "type": "number",
                "min": min(nums),
                "max": max(nums),
                "mean": mean(nums),
                "median": median(nums),
            })
        else:
            field["type"] = "string" if any(isinstance(v, str) for v in values) else "mixed"
            counts = Counter(str(v) for v in values if v is not None and v != "")
            field["top"] = counts.most_common(5)
        result["fields"][col] = field
    return result


def describe(data: Any, column: str | None = None) -> dict[str, Any]:
    rows = _rows(data)
    cols = [column] if column else columns(rows)
    out = {}
    for col in cols:
        nums = [v for v in (_numeric(r.get(col)) for r in rows) if v is not None]
        if not nums:
            out[col] = {"count": 0, "type": "non-numeric"}
            continue
        nums_sorted = sorted(nums)
        q1 = nums_sorted[len(nums_sorted) // 4] if nums_sorted else None
        q3 = nums_sorted[(3 * len(nums_sorted)) // 4] if nums_sorted else None
        out[col] = {
            "count": len(nums),
            "min": min(nums),
            "max": max(nums),
            "mean": mean(nums),
            "median": median(nums),
            "std": (sum((x - mean(nums)) ** 2 for x in nums) / len(nums)) ** 0.5,
            "q1": q1,
            "q3": q3,
        }
    return out


def correlation(data: Any, x: str, y: str) -> float | None:
    rows = _rows(data)
    xs = [v for v in (_numeric(r.get(x)) for r in rows) if v is not None]
    ys = [v for v in (_numeric(r.get(y)) for r in rows) if v is not None]
    n = min(len(xs), len(ys))
    if n < 2:
        return None
    xs, ys = xs[:n], ys[:n]
    mx, my = mean(xs), mean(ys)
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den = (sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys)) ** 0.5
    if den == 0:
        return None
    return num / den


def outliers(data: Any, column: str, method: str = "iqr", factor: float = 1.5) -> list[dict[str, Any]]:
    rows = _rows(data)
    nums = [(_numeric(r.get(column)), r) for r in rows]
    vals = [v for v in (_numeric(x) for x, _ in [(n, r) for n, r in nums]) if v is not None]
    vals = [n for n, _ in nums if n is not None]
    if not vals:
        return []
    s = sorted(vals)
    q1 = s[len(s) // 4]
    q3 = s[(3 * len(s)) // 4]
    iqr = q3 - q1
    lo, hi = q1 - factor * iqr, q3 + factor * iqr
    return [r for v, r in nums if v is not None and (v < lo or v > hi)]


def clean_missing(data: Any, strategy: str = "drop", fill: Any = None) -> list[dict[str, Any]]:
    rows = _rows(data)
    if strategy == "drop":
        return [r for r in rows if all(v is not None and v != "" for v in r.values())]
    if strategy == "fill":
        out = []
        for r in rows:
            nr = dict(r)
            for k, v in list(nr.items()):
                if v is None or v == "":
                    nr[k] = fill
            out.append(nr)
        return out
    raise ValueError(f"Unknown cleaning strategy: {strategy}")


def normalize(data: Any, column: str, method: str = "minmax") -> list[dict[str, Any]]:
    rows = _rows(data)
    vals = [v for v in (_numeric(r.get(column)) for r in rows) if v is not None]
    if not vals:
        return [dict(r) for r in rows]
    if method == "minmax":
        lo, hi = min(vals), max(vals)
        span = hi - lo if hi != lo else 1.0
        out = []
        for r in rows:
            nr = dict(r)
            v = _numeric(nr.get(column))
            if v is not None:
                nr[column] = (v - lo) / span
            out.append(nr)
        return out
    if method == "zscore":
        m = mean(vals)
        sd = (sum((x - m) ** 2 for x in vals) / len(vals)) ** 0.5 or 1.0
        out = []
        for r in rows:
            nr = dict(r)
            v = _numeric(nr.get(column))
            if v is not None:
                nr[column] = (v - m) / sd
            out.append(nr)
        return out
    raise ValueError(f"Unknown normalization method: {method}")


def pivot(data: Any, index: str, columns: str, values: str, agg: str = "sum") -> dict[str, Any]:
    rows = _rows(data)
    table = defaultdict(lambda: defaultdict(list))
    for r in rows:
        table[r.get(index)][r.get(columns)].append(r.get(values))
    result = {}
    for idx, cols in table.items():
        result[idx] = {}
        for col, vals in cols.items():
            if agg == "sum":
                result[idx][col] = sum(v for v in vals if _numeric(v) is not None)
            elif agg == "mean":
                nums = [v for v in (_numeric(v) for v in vals) if v is not None]
                result[idx][col] = mean(nums) if nums else None
            elif agg == "count":
                result[idx][col] = len(vals)
            else:
                result[idx][col] = vals
    return result


def top_values(data: Any, column: str, limit: int = 10) -> list[tuple[Any, int]]:
    rows = _rows(data)
    counts = Counter(r.get(column) for r in rows)
    return counts.most_common(int(limit))


def to_markdown(report: Any) -> str:
    if isinstance(report, dict) and "fields" in report:
        lines = ["# Data Profile", "", f"Rows: {report.get('rows')}", f"Columns: {report.get('columns')}", ""]
        lines.append("| Field | Type | Missing | Distinct |")
        lines.append("|---|---:|---:|---:|")
        for name, info in report["fields"].items():
            lines.append(f"| {name} | {info.get('type')} | {info.get('missing', 0)} | {info.get('distinct', 0)} |")
        return "\n".join(lines)
    return "```json\n" + _json(report) + "\n```"


def to_html(report: Any) -> str:
    import html as _html
    return "<!doctype html><html><head><meta charset='utf-8'><title>PeaLang Analysis</title></head><body><pre>" + _html.escape(str(report)) + "</pre></body></html>"


def _json(value: Any) -> str:
    import json
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def sort_by(data: Any, column: str, descending: bool = False) -> list[dict[str, Any]]:
    rows = _rows(data)

    def key(r):
        v = r.get(column)
        n = _numeric(v)
        return (0, n) if n is not None else (1, str(v))

    return sorted(rows, key=key, reverse=descending)


def select(data: Any, *columns: str) -> list[dict[str, Any]]:
    rows = _rows(data)
    cols = list(columns) if columns else columns(rows)
    return [{c: r.get(c) for c in cols} for r in rows]


def filter_rows(data: Any, predicate) -> list[dict[str, Any]]:
    CURRENT_INTERPRETER = None
    UserFunction = None
    try:
        from .interpreter import CURRENT_INTERPRETER as _CI, UserFunction as _UF
        CURRENT_INTERPRETER = _CI
        UserFunction = _UF
    except Exception:
        pass
    interp = CURRENT_INTERPRETER
    original = predicate
    if UserFunction is not None and isinstance(predicate, UserFunction):
        def predicate(row):
            return interp.invoke_user_function(original, [row]) if interp is not None else False
    rows = _rows(data)
    out = []
    for r in rows:
        try:
            if predicate(r):
                out.append(dict(r))
        except Exception:
            continue
    return out


def group_by(data: Any, column: str, value_column: str | None = None, agg: str = "count") -> dict[Any, Any]:
    rows = _rows(data)
    groups = defaultdict(list)
    for r in rows:
        groups[r.get(column)].append(r)
    result = {}
    for key, items in groups.items():
        if value_column is None or agg == "count":
            result[key] = len(items)
        else:
            vals = [v for v in (_numeric(r.get(value_column)) for r in items) if v is not None]
            if agg == "sum":
                result[key] = sum(vals)
            elif agg == "mean":
                result[key] = mean(vals) if vals else None
            elif agg == "min":
                result[key] = min(vals) if vals else None
            elif agg == "max":
                result[key] = max(vals) if vals else None
            else:
                result[key] = items
    return result


def value_counts(data: Any, column: str) -> list[tuple[Any, int]]:
    rows = _rows(data)
    return Counter(r.get(column) for r in rows).most_common()


def impute(data: Any, column: str, strategy: str = "mean", value: Any = None) -> list[dict[str, Any]]:
    rows = _rows(data)
    if strategy == "value":
        fill = value
    else:
        vals = [v for v in (_numeric(r.get(column)) for r in rows) if v is not None]
        if strategy == "median":
            fill = median(vals) if vals else None
        elif strategy == "mode":
            fill = Counter(r.get(column) for r in rows).most_common(1)[0][0] if rows else None
        else:
            fill = mean(vals) if vals else None
    out = []
    for r in rows:
        nr = dict(r)
        v = nr.get(column)
        if v is None or v == "":
            nr[column] = fill
        out.append(nr)
    return out


def join(left: Any, right: Any, on: str, how: str = "inner") -> list[dict[str, Any]]:
    lrows = _rows(left)
    rrows = _rows(right)
    right_index = defaultdict(list)
    for r in rrows:
        right_index[r.get(on)].append(r)
    out = []
    for lr in lrows:
        matches = right_index.get(lr.get(on), [])
        if matches:
            for rr in matches:
                merged = dict(lr)
                for k, v in rr.items():
                    if k != on or k not in merged:
                        merged[k] = v
                out.append(merged)
        elif how in ("left", "outer"):
            out.append(dict(lr))
    if how == "outer":
        left_keys = {r.get(on) for r in lrows}
        for rr in rrows:
            if rr.get(on) not in left_keys:
                out.append(dict(rr))
    return out


def to_csv(data: Any) -> str:
    rows = _rows(data)
    cols = columns(rows)
    lines = [",".join(cols)]
    for r in rows:
        lines.append(",".join(str(r.get(c, "")).replace(",", ";") for c in cols))
    return "\n".join(lines)


def head(data: Any, n: int = 5) -> list[dict[str, Any]]:
    return _rows(data)[:int(n)]


def tail(data: Any, n: int = 5) -> list[dict[str, Any]]:
    rows = _rows(data)
    return rows[-int(n):] if n else []


def bar_chart(data: Any, label: str = "", value: str = "", width: int = 40) -> str:
    rows = _rows(data)
    if not rows:
        return ""
    if not label:
        label = columns(rows)[0]
    if not value:
        nums_cols = [c for c in columns(rows) if any(_numeric(r.get(c)) is not None for r in rows)]
        value = nums_cols[-1] if nums_cols else columns(rows)[-1]
    pairs = [(str(r.get(label)), _numeric(r.get(value)) or 0.0) for r in rows]
    maxv = max((v for _, v in pairs), default=1.0) or 1.0
    lines = []
    for name, v in pairs:
        bar = "#" * int((v / maxv) * width)
        lines.append(f"{name:>12} | {bar} {v:g}")
    return "\n".join(lines)


def line_chart(data: Any, value: str = "", width: int = 60) -> str:
    rows = _rows(data)
    if not rows:
        return ""
    if not value:
        nums_cols = [c for c in columns(rows) if any(_numeric(r.get(c)) is not None for r in rows)]
        value = nums_cols[-1] if nums_cols else columns(rows)[-1]
    vals = [_numeric(r.get(value)) or 0.0 for r in rows]
    if not vals:
        return ""
    lo, hi = min(vals), max(vals)
    span = hi - lo if hi != lo else 1.0
    lines = []
    for v in vals:
        pos = int(((v - lo) / span) * (width - 1))
        lines.append(" " * pos + "*")
    return "\n".join(lines)


def rename(data: Any, mapping: dict[str, str]) -> list[dict[str, Any]]:
    rows = _rows(data)
    return [{mapping.get(k, k): v for k, v in r.items()} for r in rows]


def drop_duplicates(data: Any, subset: list[str] | None = None) -> list[dict[str, Any]]:
    rows = _rows(data)
    seen = set()
    out = []
    for r in rows:
        key = tuple(r.get(c) for c in subset) if subset else tuple(sorted((str(k), str(v)) for k, v in r.items()))
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(r))
    return out


def concat(*datasets: Any) -> list[dict[str, Any]]:
    out = []
    for d in datasets:
        out.extend(_rows(d))
    return out


def sample(data: Any, n: int = 5, seed: int | None = None) -> list[dict[str, Any]]:
    import random
    rows = _rows(data)
    rng = random.Random(seed)
    n = min(int(n), len(rows))
    return [dict(x) for x in rng.sample(rows, n)] if n else []


def unique(data: Any, column: str) -> list[Any]:
    rows = _rows(data)
    seen = []
    for r in rows:
        v = r.get(column)
        if v not in seen:
            seen.append(v)
    return seen


def fillna(data: Any, value: Any = None, column: str | None = None) -> list[dict[str, Any]]:
    rows = _rows(data)
    out = []
    for r in rows:
        nr = dict(r)
        for k, v in list(nr.items()):
            if column is not None and k != column:
                continue
            if v is None or v == "":
                nr[k] = value
        out.append(nr)
    return out


def cumsum(data: Any, column: str) -> list[dict[str, Any]]:
    rows = _rows(data)
    total = 0.0
    out = []
    for r in rows:
        nr = dict(r)
        v = _numeric(nr.get(column))
        if v is not None:
            total += v
            nr[column + "_cumsum"] = total
        out.append(nr)
    return out


def quantile(data: Any, column: str, q: float = 0.5) -> float | None:
    rows = _rows(data)
    vals = sorted([v for v in (_numeric(r.get(column)) for r in rows) if v is not None])
    if not vals:
        return None
    if q <= 0:
        return vals[0]
    if q >= 1:
        return vals[-1]
    idx = (len(vals) - 1) * float(q)
    lo = int(idx)
    hi = min(lo + 1, len(vals) - 1)
    frac = idx - lo
    return vals[lo] * (1 - frac) + vals[hi] * frac


def corr_matrix(data: Any, columns: list[str] | None = None) -> dict[str, dict[str, float | None]]:
    rows = _rows(data)
    cols = columns or [c for c in columns(rows) if any(_numeric(r.get(c)) is not None for r in rows)]
    result = {}
    for a in cols:
        result[a] = {}
        for b in cols:
            result[a][b] = correlation(rows, a, b)
    return result


def add_column(data: Any, name: str, fn) -> list[dict[str, Any]]:
    CURRENT_INTERPRETER = None
    UserFunction = None
    try:
        from .interpreter import CURRENT_INTERPRETER as _CI, UserFunction as _UF
        CURRENT_INTERPRETER = _CI
        UserFunction = _UF
    except Exception:
        pass
    interp = CURRENT_INTERPRETER
    original = fn
    if UserFunction is not None and isinstance(fn, UserFunction):
        def fn(row):
            return interp.invoke_user_function(original, [row]) if interp is not None else None
    rows = _rows(data)
    out = []
    for r in rows:
        nr = dict(r)
        try:
            nr[name] = fn(r)
        except Exception:
            nr[name] = None
        out.append(nr)
    return out


def query(data: Any, column: str, op: str, value: Any) -> list[dict[str, Any]]:
    rows = _rows(data)
    ops = {
        "==": lambda a,b: a==b, "!=": lambda a,b: a!=b,
        ">": lambda a,b: (a or 0)>b, ">=": lambda a,b: (a or 0)>=b,
        "<": lambda a,b: (a or 0)<b, "<=": lambda a,b: (a or 0)<=b,
        "in": lambda a,b: a in b, "contains": lambda a,b: b in str(a),
    }
    fn = ops.get(op, ops["=="])
    return [dict(r) for r in rows if fn(r.get(column), value)]


def summary(data: Any) -> str:
    p = profile(data)
    lines = [f"Rows: {p['rows']}, Columns: {p['columns']}"]
    for name, info in p["fields"].items():
        if info.get("type") == "number":
            lines.append(f"- {name}: number, mean={info.get('mean')}, missing={info.get('missing')}")
        else:
            lines.append(f"- {name}: {info.get('type')}, distinct={info.get('distinct')}, missing={info.get('missing')}")
    return "\n".join(lines)


def from_csv_text(text: str, delimiter: str = ",") -> list[dict[str, Any]]:
    import csv, io
    reader = csv.DictReader(io.StringIO(str(text)), delimiter=delimiter)
    return [dict(r) for r in reader]


def from_json_text(text: str) -> Any:
    import json
    data = json.loads(str(text))
    return _rows(data) if isinstance(data, (list, dict)) else data


def to_json_text(data: Any, indent: int | None = None) -> str:
    import json
    return json.dumps(_rows(data), ensure_ascii=False, indent=indent, default=str)


def between(data: Any, column: str, low: Any = None, high: Any = None) -> list[dict[str, Any]]:
    rows = _rows(data)
    lo = _numeric(low) if low is not None else None
    hi = _numeric(high) if high is not None else None
    out = []
    for r in rows:
        v = _numeric(r.get(column))
        if v is None:
            continue
        if lo is not None and v < lo:
            continue
        if hi is not None and v > hi:
            continue
        out.append(dict(r))
    return out


def clip(data: Any, column: str, low: Any = None, high: Any = None) -> list[dict[str, Any]]:
    rows = _rows(data)
    lo = _numeric(low) if low is not None else None
    hi = _numeric(high) if high is not None else None
    out = []
    for r in rows:
        nr = dict(r)
        v = _numeric(nr.get(column))
        if v is not None:
            if lo is not None and v < lo: v = lo
            if hi is not None and v > hi: v = hi
            nr[column] = v
        out.append(nr)
    return out


def mode_col(data: Any, column: str) -> Any:
    rows = _rows(data)
    vals = [r.get(column) for r in rows]
    return Counter(vals).most_common(1)[0][0] if vals else None


def nunique(data: Any, column: str) -> int:
    return len(set(r.get(column) for r in _rows(data)))


def count(data: Any, column: str | None = None) -> int:
    rows = _rows(data)
    if column is None:
        return len(rows)
    return sum(1 for r in rows if r.get(column) is not None and r.get(column) != "")


def melt(data: Any, id_vars: list[str], value_vars: list[str] | None = None, var_name: str = "variable", value_name: str = "value") -> list[dict[str, Any]]:
    rows = _rows(data)
    if value_vars is None:
        all_cols = columns(rows)
        value_vars = [c for c in all_cols if c not in (id_vars or [])]
    out = []
    for r in rows:
        for v in value_vars:
            nr = {k: r.get(k) for k in (id_vars or [])}
            nr[var_name] = v
            nr[value_name] = r.get(v)
            out.append(nr)
    return out


def transpose(data: Any) -> list[dict[str, Any]]:
    rows = _rows(data)
    if not rows:
        return []
    cols = columns(rows)
    out = []
    for c in cols:
        row = {"field": c}
        for i, r in enumerate(rows):
            row[f"row_{i}"] = r.get(c)
        out.append(row)
    return out



def rank(data: Any, column: str, ascending: bool = True) -> list[dict[str, Any]]:
    rows = _rows(data)
    vals = [(i, _numeric(r.get(column))) for i, r in enumerate(rows)]
    valid = [(i, v) for i, v in vals if v is not None]
    valid.sort(key=lambda x: x[1], reverse=not ascending)
    ranks = {i: r+1 for r, (i, _) in enumerate(valid)}
    out = []
    for i, r in enumerate(rows):
        nr = dict(r); nr[column + "_rank"] = ranks.get(i); out.append(nr)
    return out


def pct_change(data: Any, column: str) -> list[dict[str, Any]]:
    rows = _rows(data)
    prev = None
    out = []
    for r in rows:
        nr = dict(r); v = _numeric(r.get(column))
        if v is not None and prev not in (None, 0):
            nr[column + "_pct"] = (v - prev) / prev
        else:
            nr[column + "_pct"] = None
        if v is not None: prev = v
        out.append(nr)
    return out


def diff(data: Any, column: str) -> list[dict[str, Any]]:
    rows = _rows(data)
    prev = None
    out = []
    for r in rows:
        nr = dict(r); v = _numeric(r.get(column))
        nr[column + "_diff"] = (v - prev) if (v is not None and prev is not None) else None
        if v is not None: prev = v
        out.append(nr)
    return out


def rolling_mean(data: Any, column: str, window: int = 3) -> list[dict[str, Any]]:
    rows = _rows(data)
    vals = []
    out = []
    for r in rows:
        nr = dict(r); v = _numeric(r.get(column))
        if v is not None: vals.append(v)
        w = vals[-int(window):]
        nr[column + "_rolling_mean"] = mean(w) if w else None
        out.append(nr)
    return out


def schema(data: Any) -> dict[str, str]:
    rows = _rows(data)
    cols = columns(rows)
    out = {}
    for c in cols:
        types = set()
        for r in rows:
            v = r.get(c)
            if v is None: types.add('null')
            elif isinstance(v, bool): types.add('bool')
            elif isinstance(v, int): types.add('int')
            elif isinstance(v, float): types.add('number')
            elif isinstance(v, str): types.add('string')
            elif isinstance(v, list): types.add('list')
            elif isinstance(v, dict): types.add('object')
            else: types.add(type(v).__name__)
        types.discard('null')
        out[c] = '|'.join(sorted(types)) if types else 'null'
    return out


def zscore_col(data: Any, column: str) -> list[dict[str, Any]]:
    rows = _rows(data)
    vals = [v for v in (_numeric(r.get(column)) for r in rows) if v is not None]
    if not vals: return [dict(r) for r in rows]
    m = mean(vals); sd = (sum((x-m)**2 for x in vals)/len(vals))**0.5 or 1.0
    out = []
    for r in rows:
        nr = dict(r); v = _numeric(r.get(column))
        nr[column+"_z"] = (v-m)/sd if v is not None else None
        out.append(nr)
    return out


def histogram(data: Any, column: str, bins: int = 10) -> list[dict[str, Any]]:
    rows = _rows(data)
    vals = [v for v in (_numeric(r.get(column)) for r in rows) if v is not None]
    if not vals: return []
    lo, hi = min(vals), max(vals)
    if hi == lo: return [{"bin_start": lo, "bin_end": hi, "count": len(vals)}]
    width = (hi-lo)/int(bins)
    buckets = [{"bin_start": lo+i*width, "bin_end": lo+(i+1)*width, "count": 0} for i in range(int(bins))]
    for v in vals:
        i = min(int((v-lo)/width), int(bins)-1)
        buckets[i]["count"] += 1
    return buckets


def cut(data: Any, column: str, bins: int = 4, labels: list[str] | None = None) -> list[dict[str, Any]]:
    rows = _rows(data)
    vals = [v for v in (_numeric(r.get(column)) for r in rows) if v is not None]
    if not vals: return [dict(r) for r in rows]
    lo, hi = min(vals), max(vals); width = (hi-lo)/int(bins) if hi!=lo else 1
    out = []
    for r in rows:
        nr = dict(r); v = _numeric(r.get(column))
        if v is None: nr[column+"_bin"] = None
        else:
            i = min(int((v-lo)/width), int(bins)-1) if hi!=lo else 0
            nr[column+"_bin"] = labels[i] if labels and i < len(labels) else f"bin_{i}"
        out.append(nr)
    return out


def ffill(data: Any, column: str | None = None) -> list[dict[str, Any]]:
    rows = _rows(data); last = {}; out = []
    for r in rows:
        nr = dict(r)
        for k, v in nr.items():
            if column and k != column: continue
            if v is None or v == "": nr[k] = last.get(k)
            else: last[k] = v
        out.append(nr)
    return out


def bfill(data: Any, column: str | None = None) -> list[dict[str, Any]]:
    rows = _rows(data)
    # simple reverse pass
    cols = [column] if column else columns(rows)
    nextv = {c: None for c in cols}
    out = [dict(r) for r in rows]
    for i in range(len(out)-1, -1, -1):
        for c in cols:
            v = out[i].get(c)
            if v is None or v == "": out[i][c] = nextv[c]
            else: nextv[c] = v
    return out


def dropna(data: Any, column: str | None = None) -> list[dict[str, Any]]:
    rows = _rows(data)
    if column: return [dict(r) for r in rows if r.get(column) is not None and r.get(column) != ""]
    return clean_missing(rows, "drop")


def cast(data: Any, column: str, dtype: str = "number") -> list[dict[str, Any]]:
    rows = _rows(data); out = []
    for r in rows:
        nr = dict(r); v = nr.get(column)
        try:
            if dtype in ("int","integer"): nr[column] = int(float(v)) if v not in (None,"") else None
            elif dtype in ("number","float"): nr[column] = float(v) if v not in (None,"") else None
            elif dtype in ("str","string"): nr[column] = str(v) if v is not None else None
            elif dtype in ("bool","boolean"): nr[column] = bool(v) if v not in (None,"") else None
        except Exception: nr[column] = None
        out.append(nr)
    return out


def crosstab(data: Any, row: str, col: str, value: str | None = None, agg: str = "count") -> dict[str, dict[str, Any]]:
    rows = _rows(data)
    table = {}
    for r in rows:
        rk = str(r.get(row)); ck = str(r.get(col))
        table.setdefault(rk, {}).setdefault(ck, [])
        table[rk][ck].append(r.get(value) if value else 1)
    for rk in table:
        for ck in table[rk]:
            vals = table[rk][ck]
            if agg == "count": table[rk][ck] = len(vals)
            elif agg == "sum": table[rk][ck] = sum(_numeric(v) or 0 for v in vals)
            elif agg == "mean":
                nums=[_numeric(v) for v in vals]; nums=[n for n in nums if n is not None]
                table[rk][ck] = mean(nums) if nums else None
            else: table[rk][ck] = vals
    return table


def duplicated(data: Any, subset: list[str] | None = None, keep: str = "first") -> list[dict[str, Any]]:
    rows = _rows(data); seen = set(); out = []
    for r in rows:
        key = tuple(r.get(c) for c in subset) if subset else tuple(sorted((str(k),str(v)) for k,v in r.items()))
        nr = dict(r); nr["_duplicated"] = key in seen
        if key not in seen: seen.add(key)
        out.append(nr)
    return out


def nlargest(data: Any, n: int, column: str) -> list[dict[str, Any]]:
    rows = _rows(data)
    return sorted(rows, key=lambda r: _numeric(r.get(column)) if _numeric(r.get(column)) is not None else float('-inf'), reverse=True)[:int(n)]


def nsmallest(data: Any, n: int, column: str) -> list[dict[str, Any]]:
    rows = _rows(data)
    return sorted(rows, key=lambda r: _numeric(r.get(column)) if _numeric(r.get(column)) is not None else float('inf'))[:int(n)]


def pivot_wider(data: Any, names_from: str, values_from: str, id_cols: list[str] | None = None) -> list[dict[str, Any]]:
    rows = _rows(data); ids = id_cols or [c for c in columns(rows) if c not in (names_from, values_from)]
    groups = {}
    for r in rows:
        key = tuple(r.get(c) for c in ids)
        groups.setdefault(key, {c: r.get(c) for c in ids})
        groups[key][str(r.get(names_from))] = r.get(values_from)
    return list(groups.values())


def explode(data: Any, column: str) -> list[dict[str, Any]]:
    rows = _rows(data); out = []
    for r in rows:
        vals = r.get(column)
        if isinstance(vals, list):
            for v in vals:
                nr = dict(r); nr[column] = v; out.append(nr)
        else:
            out.append(dict(r))
    return out


def where(data: Any, column: str, fn_or_value, other: Any = None) -> list[dict[str, Any]]:
    rows = _rows(data); out = []
    for r in rows:
        nr = dict(r); v = nr.get(column)
        try:
            keep = fn_or_value(v) if callable(fn_or_value) else (v == fn_or_value)
        except Exception:
            keep = False
        if not keep: nr[column] = other
        out.append(nr)
    return out


def shape(data: Any) -> dict[str, int]:
    rows = _rows(data)
    return {"rows": len(rows), "columns": len(columns(rows))}


def isna(data: Any, column: str | None = None) -> int | dict[str, int]:
    rows = _rows(data)
    if column:
        return sum(1 for r in rows if r.get(column) is None or r.get(column) == "")
    return {c: sum(1 for r in rows if r.get(c) is None or r.get(c) == "") for c in columns(rows)}


def notna(data: Any, column: str | None = None) -> int | dict[str, int]:
    rows = _rows(data)
    if column:
        return sum(1 for r in rows if r.get(column) is not None and r.get(column) != "")
    na = isna(rows)
    if isinstance(na, dict):
        return {c: len(rows)-n for c,n in na.items()}
    return len(rows)-na


def to_records(data: Any) -> list[dict[str, Any]]:
    return _rows(data)


def to_dict_orient(data: Any, orient: str = "records") -> Any:
    rows = _rows(data)
    if orient == "records": return rows
    if orient == "columns":
        out = {c: [] for c in columns(rows)}
        for r in rows:
            for c in out: out[c].append(r.get(c))
        return out
    if orient == "list":
        return [list(r.values()) for r in rows]
    return rows


def str_transform(data: Any, column: str, op: str = "lower") -> list[dict[str, Any]]:
    rows = _rows(data); out = []
    for r in rows:
        nr = dict(r); v = nr.get(column)
        if v is not None:
            sv = str(v)
            if op == "lower": nr[column] = sv.lower()
            elif op == "upper": nr[column] = sv.upper()
            elif op == "strip": nr[column] = sv.strip()
            elif op == "title": nr[column] = sv.title()
            elif op == "len": nr[column] = len(sv)
        out.append(nr)
    return out


def str_contains(data: Any, column: str, pattern: str, case: bool = True) -> list[dict[str, Any]]:
    rows = _rows(data); pat = str(pattern)
    if not case: pat = pat.lower()
    out = []
    for r in rows:
        v = r.get(column)
        sv = str(v) if v is not None else ""
        if not case: sv = sv.lower()
        if pat in sv: out.append(dict(r))
    return out


def str_replace(data: Any, column: str, old: str, new: str) -> list[dict[str, Any]]:
    rows = _rows(data); out = []
    for r in rows:
        nr = dict(r); v = nr.get(column)
        if v is not None: nr[column] = str(v).replace(str(old), str(new))
        out.append(nr)
    return out


def shift(data: Any, column: str, periods: int = 1, fill: Any = None) -> list[dict[str, Any]]:
    rows = _rows(data); out = []; n = len(rows); p = int(periods)
    for i, r in enumerate(rows):
        nr = dict(r)
        src = i - p
        nr[column] = rows[src].get(column) if 0 <= src < n else fill
        out.append(nr)
    return out


def lag(data: Any, column: str, periods: int = 1, fill: Any = None) -> list[dict[str, Any]]:
    return shift(data, column, periods, fill)


def lead(data: Any, column: str, periods: int = 1, fill: Any = None) -> list[dict[str, Any]]:
    return shift(data, column, -int(periods), fill)


def cummax(data: Any, column: str) -> list[dict[str, Any]]:
    rows = _rows(data); m = None; out = []
    for r in rows:
        nr = dict(r); v = _numeric(r.get(column))
        if v is not None: m = v if m is None else max(m, v)
        nr[column + "_cummax"] = m
        out.append(nr)
    return out


def cummin(data: Any, column: str) -> list[dict[str, Any]]:
    rows = _rows(data); m = None; out = []
    for r in rows:
        nr = dict(r); v = _numeric(r.get(column))
        if v is not None: m = v if m is None else min(m, v)
        nr[column + "_cummin"] = m
        out.append(nr)
    return out


def cumprod(data: Any, column: str) -> list[dict[str, Any]]:
    rows = _rows(data); p = 1.0; started = False; out = []
    for r in rows:
        nr = dict(r); v = _numeric(r.get(column))
        if v is not None:
            if not started: p = v; started = True
            else: p *= v
            nr[column + "_cumprod"] = p
        else:
            nr[column + "_cumprod"] = p if started else None
        out.append(nr)
    return out


def replace_values(data: Any, column: str, mapping: dict | None = None, old: Any = None, new: Any = None) -> list[dict[str, Any]]:
    rows = _rows(data); mp = dict(mapping or {})
    if old is not None or mapping is None and old is None and new is not None:
        mp[old] = new
    out = []
    for r in rows:
        nr = dict(r); v = nr.get(column)
        if v in mp: nr[column] = mp[v]
        out.append(nr)
    return out


def one_hot(data: Any, column: str, prefix: str | None = None, drop_original: bool = False) -> list[dict[str, Any]]:
    rows = _rows(data); vals = unique(rows, column); pre = (prefix or column) + "_"
    out = []
    for r in rows:
        nr = dict(r); v = r.get(column)
        for val in vals:
            nr[pre + str(val)] = 1 if v == val else 0
        if drop_original: nr.pop(column, None)
        out.append(nr)
    return out


def split_column(data: Any, column: str, sep: str = ",", names: list[str] | None = None, drop_original: bool = False) -> list[dict[str, Any]]:
    rows = _rows(data); out = []
    for r in rows:
        nr = dict(r); v = nr.get(column)
        parts = str(v).split(sep) if v is not None else []
        if names:
            for i, name in enumerate(names):
                nr[name] = parts[i] if i < len(parts) else None
        else:
            for i, part in enumerate(parts):
                nr[f"{column}_{i}"] = part
        if drop_original: nr.pop(column, None)
        out.append(nr)
    return out


def drop_columns(data: Any, *cols) -> list[dict[str, Any]]:
    if len(cols)==1 and isinstance(cols[0], list): cols=tuple(cols[0])
    drop=set(cols)
    return [{k:v for k,v in r.items() if k not in drop} for r in _rows(data)]


def keep_columns(data: Any, *cols) -> list[dict[str, Any]]:
    if len(cols)==1 and isinstance(cols[0], list): cols=list(cols[0])
    else: cols=list(cols)
    return [{c:r.get(c) for c in cols} for r in _rows(data)]


def assign(data: Any, mapping: dict[str, Any]) -> list[dict[str, Any]]:
    rows=_rows(data); out=[]
    for r in rows:
        nr=dict(r)
        for k,v in (mapping or {}).items(): nr[k]=v
        out.append(nr)
    return out


def round_col(data: Any, column: str, ndigits: int = 0) -> list[dict[str, Any]]:
    rows=_rows(data); out=[]
    for r in rows:
        nr=dict(r); v=_numeric(nr.get(column))
        nr[column]=round(v, int(ndigits)) if v is not None else nr.get(column)
        out.append(nr)
    return out


def abs_col(data: Any, column: str) -> list[dict[str, Any]]:
    rows=_rows(data); out=[]
    for r in rows:
        nr=dict(r); v=_numeric(nr.get(column))
        nr[column]=abs(v) if v is not None else nr.get(column)
        out.append(nr)
    return out


def variance(data: Any, column: str) -> float | None:
    vals=[v for v in (_numeric(r.get(column)) for r in _rows(data)) if v is not None]
    if len(vals)<2: return 0.0 if len(vals)==1 else None
    m=mean(vals); return sum((x-m)**2 for x in vals)/(len(vals)-1)


def std_col(data: Any, column: str) -> float | None:
    v=variance(data,column)
    return (v**0.5) if v is not None else None


def covariance(data: Any, x: str, y: str) -> float | None:
    rows=_rows(data)
    xs=[(_numeric(r.get(x)), _numeric(r.get(y))) for r in rows]
    xs=[(a,b) for a,b in xs if a is not None and b is not None]
    if len(xs)<2: return None
    mx=mean([a for a,_ in xs]); my=mean([b for _,b in xs])
    return sum((a-mx)*(b-my) for a,b in xs)/(len(xs)-1)


def idxmax(data: Any, column: str) -> int | None:
    rows=_rows(data); best=None; bi=None
    for i,r in enumerate(rows):
        v=_numeric(r.get(column))
        if v is None: continue
        if best is None or v>best: best=v; bi=i
    return bi


def idxmin(data: Any, column: str) -> int | None:
    rows=_rows(data); best=None; bi=None
    for i,r in enumerate(rows):
        v=_numeric(r.get(column))
        if v is None: continue
        if best is None or v<best: best=v; bi=i
    return bi


def mean_col(data: Any, column: str) -> float | None:
    vals=[v for v in (_numeric(r.get(column)) for r in _rows(data)) if v is not None]
    return mean(vals) if vals else None

def sum_col(data: Any, column: str) -> float:
    return sum(v for v in (_numeric(r.get(column)) for r in _rows(data)) if v is not None)

def min_col(data: Any, column: str) -> float | None:
    vals=[v for v in (_numeric(r.get(column)) for r in _rows(data)) if v is not None]
    return min(vals) if vals else None

def max_col(data: Any, column: str) -> float | None:
    vals=[v for v in (_numeric(r.get(column)) for r in _rows(data)) if v is not None]
    return max(vals) if vals else None

def median_col(data: Any, column: str) -> float | None:
    vals=[v for v in (_numeric(r.get(column)) for r in _rows(data)) if v is not None]
    return median(vals) if vals else None

def skew(data: Any, column: str) -> float | None:
    vals=[v for v in (_numeric(r.get(column)) for r in _rows(data)) if v is not None]
    n=len(vals)
    if n<3: return None
    m=mean(vals); s2=sum((x-m)**2 for x in vals)/(n-1); sd=s2**0.5
    if sd==0: return 0.0
    m3=sum((x-m)**3 for x in vals)/n
    return (n**2/((n-1)*(n-2))) * (m3/(sd**3))

def kurtosis(data: Any, column: str) -> float | None:
    vals=[v for v in (_numeric(r.get(column)) for r in _rows(data)) if v is not None]
    n=len(vals)
    if n<4: return None
    m=mean(vals); s2=sum((x-m)**2 for x in vals)/n
    if s2==0: return 0.0
    m4=sum((x-m)**4 for x in vals)/n
    return m4/(s2**2) - 3.0

def expanding_mean(data: Any, column: str) -> list[dict[str, Any]]:
    rows=_rows(data); vals=[]; out=[]
    for r in rows:
        nr=dict(r); v=_numeric(r.get(column))
        if v is not None: vals.append(v)
        nr[column+"_expanding_mean"]=mean(vals) if vals else None
        out.append(nr)
    return out

def to_jsonl(data: Any) -> str:
    import json
    return "\n".join(json.dumps(r, ensure_ascii=False, default=str) for r in _rows(data))

def from_jsonl(text: str) -> list[dict[str, Any]]:
    import json
    out=[]
    for line in str(text).splitlines():
        line=line.strip()
        if not line: continue
        try: v=json.loads(line); out.append(v if isinstance(v,dict) else {"value":v})
        except Exception: pass
    return out


def rolling_std(data: Any, column: str, window: int = 3) -> list[dict[str, Any]]:
    rows=_rows(data); vals=[]; out=[]
    for r in rows:
        nr=dict(r); v=_numeric(r.get(column))
        if v is not None: vals.append(v)
        w=vals[-int(window):]
        if len(w)>=2:
            m=mean(w); nr[column+"_rolling_std"]=(sum((x-m)**2 for x in w)/(len(w)-1))**0.5
        else:
            nr[column+"_rolling_std"]=0.0 if len(w)==1 else None
        out.append(nr)
    return out


def expanding_sum(data: Any, column: str) -> list[dict[str, Any]]:
    rows=_rows(data); total=0.0; out=[]
    for r in rows:
        nr=dict(r); v=_numeric(r.get(column))
        if v is not None: total+=v
        nr[column+"_expanding_sum"]=total
        out.append(nr)
    return out


def expanding_max(data: Any, column: str) -> list[dict[str, Any]]:
    rows=_rows(data); m=None; out=[]
    for r in rows:
        nr=dict(r); v=_numeric(r.get(column))
        if v is not None: m=v if m is None else max(m,v)
        nr[column+"_expanding_max"]=m
        out.append(nr)
    return out


def expanding_min(data: Any, column: str) -> list[dict[str, Any]]:
    rows=_rows(data); m=None; out=[]
    for r in rows:
        nr=dict(r); v=_numeric(r.get(column))
        if v is not None: m=v if m is None else min(m,v)
        nr[column+"_expanding_min"]=m
        out.append(nr)
    return out


def sample_frac(data: Any, frac: float = 0.5, seed: int | None = None) -> list[dict[str, Any]]:
    import random
    rows=_rows(data); n=max(0,min(len(rows), int(round(len(rows)*float(frac)))))
    rng=random.Random(seed)
    return [dict(x) for x in rng.sample(rows, n)] if n else []


def ewm_mean(data: Any, column: str, alpha: float = 0.3) -> list[dict[str, Any]]:
    rows=_rows(data); a=float(alpha); prev=None; out=[]
    for r in rows:
        nr=dict(r); v=_numeric(r.get(column))
        if v is not None:
            prev = v if prev is None else a*v + (1-a)*prev
        nr[column+"_ewm"]=prev
        out.append(nr)
    return out

def _quote_ident(name: Any) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def _sqlite_type(values: Iterable[Any]) -> str:
    for value in values:
        if value is None or value == "":
            continue
        if isinstance(value, bool):
            return "INTEGER"
        if isinstance(value, int):
            return "INTEGER"
        if isinstance(value, float):
            return "REAL"
        return "TEXT"
    return "TEXT"


def sql(data: Any, query: str, table: str = "data") -> list[dict[str, Any]]:
    """Run a SQL query over records using an in-memory SQLite database.

    Nested values (dicts/lists) are stored as JSON text, which makes joins,
    grouping, window functions and CTEs available without external services.
    """
    import json as _json
    import sqlite3
    rows = _rows(data)
    cols = columns(rows)
    if not cols:
        return []
    name = str(table or "data")
    connection = sqlite3.connect(":memory:")
    try:
        connection.row_factory = sqlite3.Row
        definitions = ", ".join(
            f"{_quote_ident(col)} {_sqlite_type([row.get(col) for row in rows])}" for col in cols
        )
        connection.execute(f"CREATE TABLE {_quote_ident(name)} ({definitions})")
        column_sql = ", ".join(_quote_ident(col) for col in cols)
        placeholders = ", ".join("?" for _ in cols)

        def encode(value: Any) -> Any:
            if isinstance(value, bool):
                return int(value)
            if isinstance(value, (dict, list, tuple)):
                return _json.dumps(value, ensure_ascii=False, default=str)
            return value

        connection.executemany(
            f"INSERT INTO {_quote_ident(name)} ({column_sql}) VALUES ({placeholders})",
            [tuple(encode(row.get(col)) for col in cols) for row in rows],
        )
        cursor = connection.execute(str(query))
        return [dict(record) for record in cursor.fetchall()]
    finally:
        connection.close()


def sql_value(data: Any, query: str, table: str = "data", default: Any = None) -> Any:
    """Return the first column of the first row produced by a SQL query."""
    rows = sql(data, query, table)
    if not rows:
        return default
    return next(iter(rows[0].values()), default)


def read_csv_file(path: str, delimiter: str = ",") -> list[dict[str, Any]]:
    """Read a CSV file into records (BOM-aware UTF-8)."""
    import csv
    with open(Path(path).expanduser(), newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter=str(delimiter))]


def write_csv_file(path: str, data: Any, delimiter: str = ",") -> str:
    """Write records to a CSV file, creating parent directories as needed."""
    import csv
    rows = _rows(data)
    cols = columns(rows)
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=cols, delimiter=str(delimiter))
        writer.writeheader()
        writer.writerows(rows)
    return str(target)


def read_json_file(path: str) -> list[dict[str, Any]]:
    """Read a JSON file (array of objects or column-oriented object) into records."""
    import json
    return _rows(json.loads(Path(path).expanduser().read_text(encoding="utf-8")))


def write_json_file(path: str, data: Any, indent: int = 2) -> str:
    """Write records to a JSON file, creating parent directories as needed."""
    import json
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    pretty = None if int(indent) == 0 else int(indent)
    target.write_text(
        json.dumps(_rows(data), ensure_ascii=False, indent=pretty, default=str),
        encoding="utf-8",
    )
    return str(target)


def read_jsonl_file(path: str) -> list[dict[str, Any]]:
    """Read a newline-delimited JSON file into records."""
    return from_jsonl(Path(path).expanduser().read_text(encoding="utf-8"))


def write_jsonl_file(path: str, data: Any) -> str:
    """Write records to a newline-delimited JSON file."""
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(to_jsonl(data), encoding="utf-8")
    return str(target)


def _apply_fn(fn, *args):
    try:
        from .interpreter import CURRENT_INTERPRETER as _CI, UserFunction as _UF
    except Exception:
        _CI = None
        _UF = None
    if _UF is not None and isinstance(fn, _UF) and _CI is not None:
        return _CI.invoke_user_function(fn, list(args))
    return fn(*args)


def _rolling_apply(data: Any, column: str, window: int, suffix: str, fn) -> list[dict[str, Any]]:
    rows = _rows(data)
    vals: list[float] = []
    out = []
    width = max(1, int(window))
    for r in rows:
        nr = dict(r)
        v = _numeric(r.get(column))
        if v is not None:
            vals.append(v)
        w = vals[-width:]
        nr[column + "_" + suffix] = fn(w) if w else None
        out.append(nr)
    return out


def rolling_sum(data: Any, column: str, window: int = 3) -> list[dict[str, Any]]:
    return _rolling_apply(data, column, window, "rolling_sum", sum)


def rolling_min(data: Any, column: str, window: int = 3) -> list[dict[str, Any]]:
    return _rolling_apply(data, column, window, "rolling_min", min)


def rolling_max(data: Any, column: str, window: int = 3) -> list[dict[str, Any]]:
    return _rolling_apply(data, column, window, "rolling_max", max)


def rolling_median(data: Any, column: str, window: int = 3) -> list[dict[str, Any]]:
    return _rolling_apply(data, column, window, "rolling_median", median)


def rolling_var(data: Any, column: str, window: int = 3) -> list[dict[str, Any]]:
    def _var(w):
        if len(w) < 2:
            return None
        m = mean(w)
        return sum((x - m) ** 2 for x in w) / (len(w) - 1)

    return _rolling_apply(data, column, window, "rolling_var", _var)


def _expanding_apply(data: Any, column: str, suffix: str, fn) -> list[dict[str, Any]]:
    rows = _rows(data)
    vals: list[float] = []
    out = []
    for r in rows:
        nr = dict(r)
        v = _numeric(r.get(column))
        if v is not None:
            vals.append(v)
        nr[column + "_" + suffix] = fn(vals) if vals else None
        out.append(nr)
    return out


def expanding_std(data: Any, column: str) -> list[dict[str, Any]]:
    def _std(w):
        if len(w) < 2:
            return None
        m = mean(w)
        return (sum((x - m) ** 2 for x in w) / (len(w) - 1)) ** 0.5

    return _expanding_apply(data, column, "expanding_std", _std)


def expanding_var(data: Any, column: str) -> list[dict[str, Any]]:
    def _var(w):
        if len(w) < 2:
            return None
        m = mean(w)
        return sum((x - m) ** 2 for x in w) / (len(w) - 1)

    return _expanding_apply(data, column, "expanding_var", _var)


def expanding_median(data: Any, column: str) -> list[dict[str, Any]]:
    return _expanding_apply(data, column, "expanding_median", median)


def qcut(data: Any, column: str, q: int = 4, labels: list[Any] | None = None) -> list[dict[str, Any]]:
    """Discretize a numeric column into equal-frequency buckets."""
    from .numerics import quantile as _quantile

    rows = _rows(data)
    vals = [v for v in (_numeric(r.get(column)) for r in rows) if v is not None]
    if not vals:
        return [dict(r) for r in rows]
    bins = max(1, int(q))
    edges = [_quantile(vals, i / bins) for i in range(bins + 1)]
    out = []
    for r in rows:
        nr = dict(r)
        v = _numeric(r.get(column))
        code = None
        if v is not None:
            code = bins - 1
            for i in range(bins):
                if v <= edges[i + 1]:
                    code = i
                    break
        if labels is not None and code is not None and code < len(labels):
            nr[column + "_qcut"] = labels[code]
        else:
            nr[column + "_qcut"] = code
        out.append(nr)
    return out


def interpolate(data: Any, column: str, method: str = "linear") -> list[dict[str, Any]]:
    from .numerics import interpolate as _interpolate

    rows = _rows(data)
    filled = _interpolate([r.get(column) for r in rows], method)
    return [{**dict(r), column: filled[i]} for i, r in enumerate(rows)]


def factorize(data: Any, column: str) -> dict[str, Any]:
    """Encode a column as integer codes plus the distinct values seen."""
    rows = _rows(data)
    uniques: list[Any] = []
    index: dict[Any, int] = {}
    codes = []
    for r in rows:
        value = r.get(column)
        if value not in index:
            index[value] = len(uniques)
            uniques.append(value)
        codes.append(index[value])
    return {"codes": codes, "uniques": uniques}


def mask(data: Any, column: str, predicate, other: Any = None) -> list[dict[str, Any]]:
    """Replace values where ``predicate`` is true with ``other``."""
    rows = _rows(data)
    out = []
    for r in rows:
        nr = dict(r)
        try:
            if _apply_fn(predicate, nr.get(column)):
                nr[column] = other
        except Exception:
            pass
        out.append(nr)
    return out


def _dtype_kinds(values: Iterable[Any]) -> set[str]:
    kinds: set[str] = set()
    for v in values:
        if v is None:
            continue
        if isinstance(v, bool):
            kinds.add("bool")
        elif isinstance(v, (int, float)):
            kinds.add("number")
        elif isinstance(v, str):
            kinds.add("string")
        elif isinstance(v, (list, tuple)):
            kinds.add("list")
        elif isinstance(v, dict):
            kinds.add("object")
        else:
            kinds.add(type(v).__name__)
    return kinds


def select_dtypes(data: Any, include: Any = "number", exclude: Any = None) -> list[dict[str, Any]]:
    rows = _rows(data)
    cols = columns(rows)
    wanted = {include} if isinstance(include, str) else set(include or [])
    dropped = {exclude} if isinstance(exclude, str) else set(exclude or [])
    keep = [c for c in cols if (_dtype_kinds([r.get(c) for r in rows]) & wanted) and not (_dtype_kinds([r.get(c) for r in rows]) & dropped)]
    return [{c: r.get(c) for c in keep} for r in rows]


def info(data: Any) -> dict[str, Any]:
    rows = _rows(data)
    cols = columns(rows)
    fields = []
    for c in cols:
        values = [r.get(c) for r in rows]
        present = [v for v in values if v is not None]
        kinds = _dtype_kinds(present)
        fields.append({
            "column": c,
            "dtype": "|".join(sorted(kinds)) if kinds else "null",
            "non_null": len(present),
            "missing": len(values) - len(present),
            "distinct": len({str(v) for v in present}),
        })
    return {"rows": len(rows), "columns": len(cols), "fields": fields}


def memory_usage(data: Any) -> dict[str, Any]:
    import sys

    rows = _rows(data)
    per: dict[str, int] = {}
    for c in columns(rows):
        per[c] = sum(sys.getsizeof(r.get(c)) for r in rows)
    return {"bytes": sum(per.values()), "columns": per}


def pivot_table(data: Any, index: Any, columns: str, values: str, agg: str = "mean") -> list[dict[str, Any]]:
    """Pivot records into one row per index group, one column per pivot value."""
    rows = _rows(data)
    index_cols = [index] if isinstance(index, str) else list(index or [])
    pivot_values: list[Any] = []
    for r in rows:
        pv = r.get(columns)
        if pv not in pivot_values:
            pivot_values.append(pv)

    def reduce(items):
        if agg == "count":
            return len(items)
        nums = [v for v in (_numeric(r.get(values)) for r in items) if v is not None]
        if not nums:
            return None
        if agg == "sum":
            return sum(nums)
        if agg == "min":
            return min(nums)
        if agg == "max":
            return max(nums)
        if agg == "median":
            return median(nums)
        if agg == "std":
            if len(nums) < 2:
                return None
            m = mean(nums)
            return (sum((x - m) ** 2 for x in nums) / (len(nums) - 1)) ** 0.5
        return mean(nums)

    groups: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[tuple(r.get(c) for c in index_cols)].append(r)
    out = []
    for key, items in groups.items():
        record = {c: key[i] for i, c in enumerate(index_cols)}
        for pv in pivot_values:
            record[str(pv)] = reduce([r for r in items if r.get(columns) == pv])
        out.append(record)
    return out


def reset_index(data: Any, name: str = "index") -> list[dict[str, Any]]:
    return [{name: i, **dict(r)} for i, r in enumerate(_rows(data))]


def set_index(data: Any, column: str, descending: bool = False) -> list[dict[str, Any]]:
    rows = _rows(data)

    def key(r):
        v = r.get(column)
        if v is None:
            return (2, 0.0, "")
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return (0, float(v), "")
        return (1, 0.0, str(v))

    return [dict(r) for r in sorted(rows, key=key, reverse=bool(descending))]


def agg(data: Any, column: str, funcs: list[str] | None = None) -> dict[str, Any]:
    rows = _rows(data)
    nums = [v for v in (_numeric(r.get(column)) for r in rows) if v is not None]
    names = list(funcs or ["count", "mean", "min", "max"])
    out: dict[str, Any] = {"column": column}
    for name in names:
        if name == "count":
            out["count"] = len(nums)
        elif name == "sum":
            out["sum"] = sum(nums) if nums else None
        elif name == "mean":
            out["mean"] = mean(nums) if nums else None
        elif name == "min":
            out["min"] = min(nums) if nums else None
        elif name == "max":
            out["max"] = max(nums) if nums else None
        elif name == "median":
            out["median"] = median(nums) if nums else None
        elif name in ("std", "var"):
            if len(nums) < 2:
                out[name] = None
            else:
                m = mean(nums)
                var = sum((x - m) ** 2 for x in nums) / (len(nums) - 1)
                out[name] = var ** 0.5 if name == "std" else var
        elif name == "nunique":
            out["nunique"] = len({str(r.get(column)) for r in rows})
        else:
            out[name] = None
    return out


def transform(data: Any, column: str, fn) -> list[dict[str, Any]]:
    rows = _rows(data)
    out = []
    for r in rows:
        nr = dict(r)
        try:
            nr[column] = _apply_fn(fn, r.get(column))
        except Exception:
            nr[column] = None
        out.append(nr)
    return out


def group_by_multi(data: Any, group_columns: Any, value_column: str | None = None, agg: str = "count") -> list[dict[str, Any]]:
    rows = _rows(data)
    cols = [group_columns] if isinstance(group_columns, str) else list(group_columns or [])
    groups: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[tuple(r.get(c) for c in cols)].append(r)
    out = []
    for key, items in groups.items():
        record = {c: key[i] for i, c in enumerate(cols)}
        if value_column is None or agg == "count":
            record["count"] = len(items)
        else:
            nums = [v for v in (_numeric(r.get(value_column)) for r in items) if v is not None]
            if agg == "sum":
                value = sum(nums) if nums else None
            elif agg == "mean":
                value = mean(nums) if nums else None
            elif agg == "min":
                value = min(nums) if nums else None
            elif agg == "max":
                value = max(nums) if nums else None
            elif agg == "median":
                value = median(nums) if nums else None
            else:
                value = len(items)
            record[agg + "_" + value_column] = value
        out.append(record)
    return out


def merge_multi(left: Any, right: Any, on: Any, how: str = "inner") -> list[dict[str, Any]]:
    left_rows = _rows(left)
    right_rows = _rows(right)
    keys = [on] if isinstance(on, str) else list(on or [])

    def key_of(row):
        return tuple(row.get(k) for k in keys)

    index: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for r in right_rows:
        index[key_of(r)].append(r)
    out = []
    for l in left_rows:
        matches = index.get(key_of(l), [])
        if matches:
            for r in matches:
                merged = dict(l)
                for k, v in r.items():
                    if k in merged and k not in keys:
                        merged["right_" + k] = v
                    else:
                        merged[k] = v
                out.append(merged)
        elif how in ("left", "outer"):
            out.append(dict(l))
    if how in ("right", "outer"):
        matched = {key_of(r) for r in left_rows}
        for r in right_rows:
            if key_of(r) not in matched:
                out.append(dict(r))
    return out


def describe_all(data: Any) -> dict[str, Any]:
    return describe(_rows(data))


def missing_summary(data: Any) -> list[dict[str, Any]]:
    rows = _rows(data)
    total = len(rows)
    out = []
    for c in columns(rows):
        missing = sum(1 for r in rows if r.get(c) is None)
        out.append({
            "column": c,
            "missing": missing,
            "present": total - missing,
            "missing_pct": (missing / total * 100.0) if total else 0.0,
        })
    return out


def winsorize(data: Any, column: str, lower: float = 0.05, upper: float = 0.95) -> list[dict[str, Any]]:
    from .numerics import winsorize as _winsorize

    rows = _rows(data)
    positions = [i for i, r in enumerate(rows) if _numeric(r.get(column)) is not None]
    clipped = _winsorize([_numeric(rows[i].get(column)) for i in positions], lower, upper)
    out = [dict(r) for r in rows]
    for pos, value in zip(positions, clipped):
        out[pos][column] = value
    return out


def corr_spearman(data: Any, x: str, y: str) -> float | None:
    from .numerics import spearman

    rows = _rows(data)
    xs = [_numeric(r.get(x)) for r in rows]
    ys = [_numeric(r.get(y)) for r in rows]
    return spearman(xs, ys)


def date_range(start: Any, end: Any, freq: str = "D", step: int = 1) -> list[str]:
    from datetime import date, datetime, timedelta

    def parse(value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    begin, finish = parse(start), parse(end)
    n = max(1, int(step))
    delta = {
        "D": timedelta(days=n),
        "H": timedelta(hours=n),
        "W": timedelta(weeks=n),
        "M": timedelta(days=30 * n),
        "Y": timedelta(days=365 * n),
    }.get(str(freq).upper(), timedelta(days=n))
    out = []
    current = begin
    while current <= finish:
        out.append(current.isoformat())
        current += delta
    return out


def regression_report(data: Any, target: str, features: Any = None,
                      confidence: float = 0.95) -> dict[str, Any]:
    """Fit OLS on records, auto-selecting numeric predictors when omitted."""
    from .inference import ols

    rows = _rows(data)
    if features is None:
        feature_names = [
            c for c in columns(rows)
            if c != target and any(_numeric(r.get(c)) is not None for r in rows)
        ]
    elif isinstance(features, str):
        feature_names = [features]
    else:
        feature_names = list(features)
    if not feature_names:
        raise ValueError("no numeric feature columns were found")
    usable = []
    for r in rows:
        values = [_numeric(r.get(c)) for c in feature_names]
        response = _numeric(r.get(target))
        if response is not None and all(value is not None for value in values):
            usable.append((values, response))
    if not usable:
        raise ValueError("no complete rows are available for regression")
    design = [pair[0] for pair in usable]
    response = [pair[1] for pair in usable]
    return ols(design, response, names=feature_names, confidence=confidence)


def time_series_report(data: Any, column: str, lags: int = 10,
                       period: int | None = None) -> dict[str, Any]:
    """ACF/PACF, Ljung-Box and optional seasonal decomposition for a column."""
    from .inference import acf, pacf, ljung_box, seasonal_decompose

    values = [v for v in (_numeric(r.get(column)) for r in _rows(data)) if v is not None]
    if len(values) < 2:
        raise ValueError("at least two numeric values are required")
    result: dict[str, Any] = {
        "n": len(values),
        "acf": acf(values, lags),
        "pacf": pacf(values, lags),
    }
    if len(values) > int(lags):
        result["ljung_box"] = ljung_box(values, lags)
    if period and len(values) >= 2 * int(period):
        result["decomposition"] = seasonal_decompose(values, period)
    return result


def _feature_columns(rows: list[dict[str, Any]], target: str,
                     features: Any) -> list[str]:
    if features is None:
        names = [
            c for c in columns(rows)
            if c != target and any(_numeric(r.get(c)) is not None for r in rows)
        ]
    elif isinstance(features, str):
        names = [features]
    else:
        names = list(features)
    if not names:
        raise ValueError("no numeric feature columns were found")
    return names


def glm_report(data: Any, target: str, features: Any = None,
               family: str = "binomial", confidence: float = 0.95) -> dict[str, Any]:
    """Fit a GLM on records, auto-selecting numeric predictors when omitted."""
    from .modeling import glm

    rows = _rows(data)
    feature_names = _feature_columns(rows, target, features)
    usable = []
    for r in rows:
        values = [_numeric(r.get(c)) for c in feature_names]
        raw = r.get(target)
        if isinstance(raw, bool):
            response = 1.0 if raw else 0.0
        else:
            response = _numeric(raw)
        if response is not None and all(value is not None for value in values):
            usable.append((values, response))
    if not usable:
        raise ValueError("no complete rows are available for the model")
    return glm(
        [pair[0] for pair in usable],
        [pair[1] for pair in usable],
        family,
        names=feature_names,
        confidence=confidence,
    )


def survival_report(data: Any, time: str, event: str | None = None,
                    features: Any = None, confidence: float = 0.95) -> dict[str, Any]:
    """Kaplan-Meier survival curve and an optional Cox proportional-hazards fit."""
    from .modeling import kaplan_meier, cox_proportional_hazards

    rows = _rows(data)
    usable = []
    for r in rows:
        moment = _numeric(r.get(time))
        if moment is None:
            continue
        if event is None:
            flag = 1
        else:
            raw = r.get(event)
            if isinstance(raw, bool):
                flag = 1 if raw else 0
            else:
                value = _numeric(raw)
                flag = 0 if value is None else int(value != 0)
        usable.append((r, moment, flag))
    if not usable:
        raise ValueError("no rows with a numeric time column were found")
    km = kaplan_meier([item[1] for item in usable], [item[2] for item in usable],
                      confidence)
    result: dict[str, Any] = {"kaplan_meier": km, "n": len(usable)}
    if features is not None:
        feature_names = _feature_columns(rows, time, features)
        design = []
        times = []
        events = []
        for r, moment, flag in usable:
            values = [_numeric(r.get(c)) for c in feature_names]
            if all(value is not None for value in values):
                design.append(values)
                times.append(moment)
                events.append(flag)
        if design:
            result["cox"] = cox_proportional_hazards(
                design, times, events, names=feature_names, confidence=confidence
            )
    return result


def arima_report(data: Any, column: str, order: Any = None,
                 max_p: int = 3, max_q: int = 3, d: int | None = None,
                 periods: int = 1) -> dict[str, Any]:
    """Fit an ARIMA model to a column, selecting the order by AIC when omitted."""
    from .modeling import arima, auto_arima

    values = [v for v in (_numeric(r.get(column)) for r in _rows(data)) if v is not None]
    if len(values) < 8:
        raise ValueError("at least eight numeric values are required")
    if order is not None:
        parts = list(order)
        if len(parts) > 3:
            raise ValueError("ARIMA order must have at most three components")
        parts += [0] * (3 - len(parts))
        return arima(values, int(parts[0]), int(parts[1]), int(parts[2]), periods)
    return auto_arima(values, max_p, max_q, d, periods)


def _causal_columns(rows: list[dict[str, Any]], exclude: list[str],
                    features: Any) -> list[str]:
    if features is None:
        names = [
            c for c in columns(rows)
            if c not in exclude and any(_numeric(r.get(c)) is not None for r in rows)
        ]
    elif isinstance(features, str):
        names = [features]
    else:
        names = list(features)
    if not names:
        raise ValueError("no numeric covariate columns were found")
    return names


def _binary(value: Any) -> int | None:
    if isinstance(value, bool):
        return 1 if value else 0
    number = _numeric(value)
    if number is None or number not in (0.0, 1.0):
        return None
    return int(number)


def causal_report(data: Any, treatment: str, outcome: str,
                  covariates: Any = None, method: str = "ipw",
                  trim: float = 0.0, confidence: float = 0.95,
                  caliper: float = 0.2, ratio: int = 1) -> dict[str, Any]:
    """Estimate a treatment effect from records.

    ``method`` is ``"ipw"`` (default), ``"aipw"`` (doubly robust), or
    ``"matching"``. The result includes the effect estimate, interval, and
    covariate-balance diagnostics.
    """
    from .causal import (ipw_ate, aipw_ate, propensity_match,
                         covariate_balance)

    rows = _rows(data)
    feature_names = _causal_columns(rows, [treatment, outcome], covariates)
    usable = []
    for r in rows:
        flag = _binary(r.get(treatment))
        response = _numeric(r.get(outcome))
        values = [_numeric(r.get(c)) for c in feature_names]
        if flag is not None and response is not None and all(v is not None for v in values):
            usable.append((values, flag, response))
    if not usable:
        raise ValueError("no complete rows are available for the causal model")
    features = [item[0] for item in usable]
    treated = [item[1] for item in usable]
    response = [item[2] for item in usable]
    key = str(method).lower()
    if key in ("ipw", "ate", "weighting"):
        result = ipw_ate(features, treated, response, trim, confidence)
    elif key in ("aipw", "doubly_robust", "dr"):
        result = aipw_ate(features, treated, response, trim, confidence)
    elif key in ("matching", "match", "psm"):
        result = propensity_match(features, treated, response, caliper, ratio)
    else:
        raise ValueError("unknown causal method: " + str(method))
    result["method"] = key
    result["features"] = feature_names
    result["balance"] = covariate_balance(features, treated, feature_names)
    weights = result.get("weights")
    if weights is not None:
        result["weighted_balance"] = covariate_balance(
            features, treated, feature_names, weights
        )
    return result


def did_report(data: Any, outcome: str, treated: str, post: str,
               covariates: Any = None, cluster: Any = None,
               confidence: float = 0.95) -> dict[str, Any]:
    """Difference-in-differences from records with optional clustered errors."""
    from .causal import difference_in_differences

    rows = _rows(data)
    if covariates is None:
        feature_names: list[str] = []
    else:
        feature_names = _causal_columns(rows, [outcome, treated, post], covariates)
    usable = []
    indices = []
    for index, r in enumerate(rows):
        flag = _binary(r.get(treated))
        period = _binary(r.get(post))
        response = _numeric(r.get(outcome))
        values = [_numeric(r.get(c)) for c in feature_names]
        if (flag is not None and period is not None and response is not None
                and all(v is not None for v in values)):
            usable.append((values, flag, period, response))
            indices.append(index)
    if not usable:
        raise ValueError("no complete rows are available for the DiD model")
    cluster_values = None
    if cluster is not None:
        if isinstance(cluster, str):
            cluster_values = [rows[i].get(cluster) for i in indices]
        else:
            cluster_values = [list(cluster)[i] for i in indices]
    return difference_in_differences(
        [item[3] for item in usable],
        [item[1] for item in usable],
        [item[2] for item in usable],
        [item[0] for item in usable] if feature_names else None,
        feature_names or None,
        cluster_values,
        confidence,
    )


def iv_report(data: Any, outcome: str, endogenous: str, instruments: Any,
              controls: Any = None, confidence: float = 0.95) -> dict[str, Any]:
    """Two-stage least squares from records."""
    from .causal import instrumental_variables

    rows = _rows(data)
    if isinstance(instruments, str):
        instrument_names = [instruments]
    else:
        instrument_names = list(instruments)
    control_names = [] if controls is None else (
        [controls] if isinstance(controls, str) else list(controls)
    )
    usable = []
    for r in rows:
        response = _numeric(r.get(outcome))
        endo = _numeric(r.get(endogenous))
        z_values = [_numeric(r.get(c)) for c in instrument_names]
        c_values = [_numeric(r.get(c)) for c in control_names]
        if (response is not None and endo is not None
                and all(v is not None for v in z_values)
                and all(v is not None for v in c_values)):
            usable.append((z_values, endo, response, c_values))
    if not usable:
        raise ValueError("no complete rows are available for the IV model")
    return instrumental_variables(
        [item[0] for item in usable],
        [item[1] for item in usable],
        [item[2] for item in usable],
        [item[3] for item in usable] if control_names else None,
        control_names or None,
        instrument_names,
        confidence,
    )


def rdd_report(data: Any, outcome: str, running: str, cutoff: float = 0.0,
               bandwidth: float | None = None, degree: int = 1,
               confidence: float = 0.95) -> dict[str, Any]:
    """Sharp regression-discontinuity estimate from records."""
    from .causal import regression_discontinuity

    rows = _rows(data)
    running_values = []
    outcome_values = []
    for r in rows:
        x = _numeric(r.get(running))
        y = _numeric(r.get(outcome))
        if x is not None and y is not None:
            running_values.append(x)
            outcome_values.append(y)
    if not running_values:
        raise ValueError("no complete rows are available for the RDD model")
    return regression_discontinuity(
        running_values, outcome_values, cutoff, bandwidth, degree, confidence
    )


def train_test_split(data: Any, test_size: float = 0.25, seed: Any = 0,
                     stratify: str | None = None,
                     shuffle: bool = True) -> dict[str, Any]:
    """Split records into train and test sets, optionally stratified by column."""
    from .evaluation import train_test_split as _split

    rows = _rows(data)
    labels = [r.get(stratify) for r in rows] if stratify is not None else None
    result = _split(rows, [0] * len(rows), test_size, shuffle, seed, labels)
    return {
        "train": [rows[i] for i in result["train_index"]],
        "test": [rows[i] for i in result["test_index"]],
        "train_index": result["train_index"],
        "test_index": result["test_index"],
        "n_train": result["n_train"],
        "n_test": result["n_test"],
        "stratified": result["stratified"],
    }


def evaluate_classification(data: Any, actual: str, predicted: str,
                            scores: str | None = None,
                            positive: Any = None) -> dict[str, Any]:
    """Classification metrics from two label columns, with optional scores."""
    from .evaluation import (accuracy_score, precision_recall_fscore,
                             roc_auc, log_loss, brier_score)

    rows = _rows(data)
    labels = []
    guesses = []
    probabilities = []
    for r in rows:
        truth = r.get(actual)
        guess = r.get(predicted)
        if truth is None or guess is None:
            continue
        if scores is not None:
            probability = _numeric(r.get(scores))
            if probability is None:
                continue
            probabilities.append(probability)
        labels.append(truth)
        guesses.append(guess)
    if not labels:
        raise ValueError("no complete rows are available for evaluation")
    result: dict[str, Any] = {"n": len(labels), "accuracy": accuracy_score(labels, guesses)}
    result.update(precision_recall_fscore(labels, guesses, positive))
    if scores is not None:
        result["roc_auc"] = roc_auc(labels, probabilities, positive)
        result["log_loss"] = log_loss(labels, probabilities, positive)
        result["brier_score"] = brier_score(labels, probabilities, positive)
    return result


def evaluate_regression(data: Any, actual: str, predicted: str) -> dict[str, Any]:
    """Regression metrics from two numeric columns."""
    from .evaluation import (mean_squared_error, root_mean_squared_error,
                             mean_absolute_error, median_absolute_error,
                             r2_score, explained_variance_score)

    rows = _rows(data)
    truths = []
    guesses = []
    for r in rows:
        truth = _numeric(r.get(actual))
        guess = _numeric(r.get(predicted))
        if truth is None or guess is None:
            continue
        truths.append(truth)
        guesses.append(guess)
    if not truths:
        raise ValueError("no complete rows are available for evaluation")
    return {
        "n": len(truths),
        "mse": mean_squared_error(truths, guesses),
        "rmse": root_mean_squared_error(truths, guesses),
        "mae": mean_absolute_error(truths, guesses),
        "median_ae": median_absolute_error(truths, guesses),
        "r2": r2_score(truths, guesses),
        "explained_variance": explained_variance_score(truths, guesses),
    }


def add_polynomial_features(data: Any, columns: Any, degree: int = 2,
                            interaction_only: bool = False,
                            prefix: str = "") -> list[dict[str, Any]]:
    """Add polynomial and interaction columns derived from numeric columns."""
    from .evaluation import polynomial_features

    rows = _rows(data)
    names = [columns] if isinstance(columns, str) else list(columns)
    usable = [
        r for r in rows
        if all(_numeric(r.get(name)) is not None for name in names)
    ]
    if not usable:
        raise ValueError("no complete rows are available for polynomial features")
    matrix = [[_numeric(r.get(name)) for name in names] for r in usable]
    expanded = polynomial_features(matrix, degree, False, interaction_only, names)
    out = []
    position = 0
    for r in rows:
        if all(_numeric(r.get(name)) is not None for name in names):
            record = dict(r)
            for name, value in zip(expanded["names"], expanded["features"][position]):
                if name in names:
                    continue
                record[prefix + name] = value
            out.append(record)
            position += 1
        else:
            out.append(dict(r))
    return out


def build_analysis_namespace() -> dict[str, Any]:
    return {
        "profile": profile,
        "describe": describe,
        "columns": columns,
        "correlation": correlation,
        "corr_matrix": corr_matrix,
        "outliers": outliers,
        "clean_missing": clean_missing,
        "normalize": normalize,
        "pivot": pivot,
        "top_values": top_values,
        "to_markdown": to_markdown,
        "to_html": to_html,
        "to_csv": to_csv,
        "sort_by": sort_by,
        "select": select,
        "filter_rows": filter_rows,
        "group_by": group_by,
        "value_counts": value_counts,
        "impute": impute,
        "fillna": fillna,
        "join": join,
        "merge": join,
        "rename": rename,
        "drop_duplicates": drop_duplicates,
        "concat": concat,
        "sample": sample,
        "unique": unique,
        "cumsum": cumsum,
        "quantile": quantile,
        "add_column": add_column,
        "query": query,
        "summary": summary,
        "head": head,
        "tail": tail,
        "bar_chart": bar_chart,
        "line_chart": line_chart,
        "from_csv": from_csv_text,
        "from_json": from_json_text,
        "to_json": to_json_text,
        "between": between,
        "clip": clip,
        "mode": mode_col,
        "nunique": nunique,
        "count": count,
        "melt": melt,
        "transpose": transpose,
        "rank": rank,
        "pct_change": pct_change,
        "diff": diff,
        "rolling_mean": rolling_mean,
        "schema": schema,
        "zscore": zscore_col,
        "histogram": histogram,
        "cut": cut,
        "ffill": ffill,
        "bfill": bfill,
        "dropna": dropna,
        "cast": cast,
        "crosstab": crosstab,
        "duplicated": duplicated,
        "nlargest": nlargest,
        "nsmallest": nsmallest,
        "pivot_wider": pivot_wider,
        "explode": explode,
        "where": where,
        "shape": shape,
        "isna": isna,
        "notna": notna,
        "astype": cast,
        "to_records": to_records,
        "to_dict": to_dict_orient,
        "str_transform": str_transform,
        "str_lower": lambda d,c: str_transform(d,c,"lower"),
        "str_upper": lambda d,c: str_transform(d,c,"upper"),
        "str_strip": lambda d,c: str_transform(d,c,"strip"),
        "str_contains": str_contains,
        "str_replace": str_replace,
        "shift": shift,
        "lag": lag,
        "lead": lead,
        "cummax": cummax,
        "cummin": cummin,
        "cumprod": cumprod,
        "replace_values": replace_values,
        "one_hot": one_hot,
        "split_column": split_column,
        "percentile": quantile,
        "drop_columns": drop_columns,
        "keep_columns": keep_columns,
        "assign": assign,
        "round_col": round_col,
        "abs_col": abs_col,
        "variance": variance,
        "std": std_col,
        "covariance": covariance,
        "idxmax": idxmax,
        "idxmin": idxmin,
        "mean_col": mean_col,
        "sum_col": sum_col,
        "min_col": min_col,
        "max_col": max_col,
        "median_col": median_col,
        "skew": skew,
        "kurtosis": kurtosis,
        "expanding_mean": expanding_mean,
        "to_jsonl": to_jsonl,
        "from_jsonl": from_jsonl,
        "corr": correlation,
        "rolling_std": rolling_std,
        "expanding_sum": expanding_sum,
        "expanding_max": expanding_max,
        "expanding_min": expanding_min,
        "expanding_count": lambda d,c=None: [{"_expanding_count": i+1, **dict(r)} for i,r in enumerate(_rows(d))],
        "sample_frac": sample_frac,
        "ewm_mean": ewm_mean,
        "standardize": zscore_col,
        "sql": sql,
        "sql_value": sql_value,
        "read_csv_file": read_csv_file,
        "write_csv_file": write_csv_file,
        "read_json_file": read_json_file,
        "write_json_file": write_json_file,
        "read_jsonl_file": read_jsonl_file,
        "write_jsonl_file": write_jsonl_file,
        "qcut": qcut,
        "rolling_sum": rolling_sum,
        "rolling_min": rolling_min,
        "rolling_max": rolling_max,
        "rolling_median": rolling_median,
        "rolling_var": rolling_var,
        "expanding_std": expanding_std,
        "expanding_var": expanding_var,
        "expanding_median": expanding_median,
        "interpolate": interpolate,
        "factorize": factorize,
        "mask": mask,
        "select_dtypes": select_dtypes,
        "info": info,
        "memory_usage": memory_usage,
        "pivot_table": pivot_table,
        "reset_index": reset_index,
        "set_index": set_index,
        "agg": agg,
        "transform": transform,
        "group_by_multi": group_by_multi,
        "merge_multi": merge_multi,
        "describe_all": describe_all,
        "missing_summary": missing_summary,
        "winsorize": winsorize,
        "corr_spearman": corr_spearman,
        "date_range": date_range,
        "regression_report": regression_report,
        "time_series_report": time_series_report,
        "glm_report": glm_report,
        "survival_report": survival_report,
        "arima_report": arima_report,
        "causal_report": causal_report,
        "did_report": did_report,
        "iv_report": iv_report,
        "rdd_report": rdd_report,
        "train_test_split": train_test_split,
        "evaluate_classification": evaluate_classification,
        "evaluate_regression": evaluate_regression,
        "add_polynomial_features": add_polynomial_features,
    }

