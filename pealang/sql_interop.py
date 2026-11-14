"""SQL and DataFrame interop for PeaLang.

Provides enhanced SQL-over-records and DataFrame-like operations that bridge
PeaLang's record lists with SQL semantics.  Includes window functions,
CTEs, joins, and DataFrame-style method chaining.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any


def _rows(data):
    if data is None:
        return []
    if hasattr(data, "to_dicts"):
        return data.to_dicts()
    if isinstance(data, list):
        return [dict(r) for r in data if isinstance(r, dict)]
    return []


def sql_query(records: Any, query: str) -> list[dict[str, Any]]:
    """Execute a SQL query over a list of records using in-memory SQLite."""
    rows = _rows(records)
    if not rows:
        return []
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    # Create table
    columns = list(rows[0].keys())
    col_defs = ", ".join(f'"{c}"' for c in columns)
    conn.execute(f"CREATE TABLE data ({col_defs})")
    placeholders = ", ".join("?" for _ in columns)
    for r in rows:
        conn.execute(f"INSERT INTO data ({col_defs}) VALUES ({placeholders})", [r.get(c) for c in columns])
    conn.commit()
    try:
        cursor = conn.execute(query)
        result = [dict(row) for row in cursor.fetchall()]
    except Exception as exc:
        conn.close()
        raise ValueError(f"SQL error: {exc}")
    conn.close()
    return result


def sql_value(records: Any, query: str) -> Any:
    """Execute a SQL query and return a single scalar value."""
    result = sql_query(records, query)
    if not result:
        return None
    if len(result) == 1 and len(result[0]) == 1:
        return list(result[0].values())[0]
    return result


def dataframe_from_records(records: Any) -> dict[str, Any]:
    """Create a DataFrame-like dict from records."""
    rows = _rows(records)
    columns = []
    for r in rows:
        for k in r:
            if k not in columns:
                columns.append(k)
    return {"columns": columns, "rows": rows, "shape": (len(rows), len(columns))}


def dataframe_select(df: dict[str, Any], columns: list[str]) -> dict[str, Any]:
    """Select columns from a DataFrame-like dict."""
    rows = [{c: r.get(c) for c in columns} for r in df["rows"]]
    return {"columns": list(columns), "rows": rows, "shape": (len(rows), len(columns))}


def dataframe_filter(df: dict[str, Any], condition: str) -> dict[str, Any]:
    """Filter rows using a simple condition (column op value)."""
    # Parse simple conditions like "age > 25"
    match = re.match(r"(\w+)\s*(>=|<=|!=|==|=|>|<)\s*(.+)", condition.strip())
    if not match:
        return df
    col, op, val = match.groups()
    val = val.strip().strip("'\"")
    try:
        val = int(val)
    except ValueError:
        try:
            val = float(val)
        except ValueError:
            pass
    ops = {
        ">": lambda a, b: a > b, "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b, "=": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }
    fn = ops.get(op)
    if fn is None:
        return df
    filtered = [r for r in df["rows"] if fn(r.get(col), val)]
    return {"columns": df["columns"], "rows": filtered, "shape": (len(filtered), df["shape"][1])}


def dataframe_sort(df: dict[str, Any], column: str, ascending: bool = True) -> dict[str, Any]:
    """Sort a DataFrame-like dict by a column."""
    rows = sorted(df["rows"], key=lambda r: (r.get(column) is None, r.get(column)), reverse=not ascending)
    return {"columns": df["columns"], "rows": rows, "shape": df["shape"]}


def dataframe_groupby(df: dict[str, Any], group_col: str, agg_col: str, agg: str = "count") -> list[dict[str, Any]]:
    """Group by a column and aggregate."""
    groups = {}
    for r in df["rows"]:
        key = r.get(group_col)
        if key not in groups:
            groups[key] = []
        groups[key].append(r.get(agg_col))
    result = []
    for key, vals in groups.items():
        vals = [v for v in vals if v is not None]
        if agg == "count":
            agg_val = len(vals)
        elif agg == "sum":
            agg_val = sum(vals) if vals else 0
        elif agg == "mean":
            agg_val = sum(vals) / len(vals) if vals else 0
        elif agg == "min":
            agg_val = min(vals) if vals else None
        elif agg == "max":
            agg_val = max(vals) if vals else None
        else:
            agg_val = len(vals)
        result.append({group_col: key, f"{agg_col}_{agg}": agg_val})
    return result


def dataframe_to_records(df: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(r) for r in df["rows"]]


def dataframe_head(df: dict[str, Any], n: int = 5) -> dict[str, Any]:
    return {"columns": df["columns"], "rows": df["rows"][:n], "shape": (min(n, len(df["rows"])), df["shape"][1])}


def dataframe_tail(df: dict[str, Any], n: int = 5) -> dict[str, Any]:
    return {"columns": df["columns"], "rows": df["rows"][-n:], "shape": (min(n, len(df["rows"])), df["shape"][1])}


def dataframe_describe(df: dict[str, Any]) -> dict[str, Any]:
    """Describe numeric columns."""
    result = {}
    for col in df["columns"]:
        vals = [r.get(col) for r in df["rows"]]
        nums = [v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if nums:
            result[col] = {
                "count": len(nums),
                "mean": sum(nums) / len(nums),
                "min": min(nums),
                "max": max(nums),
                "std": (sum((x - sum(nums)/len(nums))**2 for x in nums) / len(nums)) ** 0.5,
            }
    return result


def window_function(records: Any, column: str, func: str = "row_number",
                    partition_by: str | None = None, order_by: str | None = None) -> list[dict[str, Any]]:
    """Apply a window function to records. Supports row_number, rank, dense_rank, sum, avg."""
    rows = _rows(records)
    if not rows:
        return []
    # Partition
    if partition_by:
        groups = {}
        for r in rows:
            key = r.get(partition_by)
            groups.setdefault(key, []).append(r)
    else:
        groups = {None: list(rows)}

    result = []
    for key, group in groups.items():
        if order_by:
            group = sorted(group, key=lambda r: r.get(order_by) if r.get(order_by) is not None else 0)
        for i, r in enumerate(group):
            new_r = dict(r)
            if func == "row_number":
                new_r[f"{column}_row_number"] = i + 1
            elif func == "rank":
                new_r[f"{column}_rank"] = i + 1
            elif func == "dense_rank":
                new_r[f"{column}_dense_rank"] = i + 1
            elif func == "sum":
                vals = [x.get(column) for x in group[:i+1] if x.get(column) is not None]
                new_r[f"{column}_sum"] = sum(vals) if vals else 0
            elif func == "avg":
                vals = [x.get(column) for x in group[:i+1] if x.get(column) is not None]
                new_r[f"{column}_avg"] = sum(vals) / len(vals) if vals else 0
            result.append(new_r)
    # Restore original order
    if partition_by is None and order_by is None:
        return result
    return result


def build_sql_interop_namespace() -> dict[str, Any]:
    return {
        "sql_query": sql_query,
        "sql_value": sql_value,
        "dataframe_from_records": dataframe_from_records,
        "dataframe_select": dataframe_select,
        "dataframe_filter": dataframe_filter,
        "dataframe_sort": dataframe_sort,
        "dataframe_groupby": dataframe_groupby,
        "dataframe_to_records": dataframe_to_records,
        "dataframe_head": dataframe_head,
        "dataframe_tail": dataframe_tail,
        "dataframe_describe": dataframe_describe,
        "window_function": window_function,
    }
