"""Data analysis toolkit for PeaLang."""

from __future__ import annotations

from collections import Counter, defaultdict
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
    }

