"""Data validation and schema enforcement for PeaLang.

Provides dependency-free tools for defining schemas, validating records,
and generating data-quality reports.  Mirrors pandas' dtype validation and
Great Expectations-style checks.
"""

from __future__ import annotations

import json

import re
from typing import Any, Iterable


# ---------------------------------------------------------------------------
# Schema definition
# ---------------------------------------------------------------------------

class FieldSpec:
    def __init__(self, name: str, dtype: str = "any", *,
                 required: bool = True, nullable: bool = True,
                 min_value: Any = None, max_value: Any = None,
                 pattern: str | None = None, allowed: list[Any] | None = None,
                 unique: bool = False):
        self.name = str(name)
        self.dtype = str(dtype).lower()
        self.required = bool(required)
        self.nullable = bool(nullable)
        self.min_value = min_value
        self.max_value = max_value
        self.pattern = pattern
        self.allowed = allowed
        self.unique = bool(unique)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name, "dtype": self.dtype, "required": self.required,
            "nullable": self.nullable, "min_value": self.min_value,
            "max_value": self.max_value, "pattern": self.pattern,
            "allowed": self.allowed, "unique": self.unique,
        }


class Schema:
    def __init__(self, fields: list[FieldSpec] | None = None):
        self.fields = list(fields or [])
        self._by_name = {f.name: f for f in self.fields}

    def add_field(self, field: FieldSpec) -> "Schema":
        self.fields.append(field)
        self._by_name[field.name] = field
        return self

    def field(self, name: str) -> FieldSpec | None:
        return self._by_name.get(name)

    def to_dict(self) -> dict[str, Any]:
        return {"fields": [f.to_dict() for f in self.fields]}


def build_schema(fields: list[dict[str, Any]] | None = None) -> Schema:
    """Build a Schema from a list of field dicts."""
    schema = Schema()
    for f in (fields or []):
        schema.add_field(FieldSpec(
            name=f.get("name", f.get("field", "")),
            dtype=f.get("dtype", f.get("type", "any")),
            required=f.get("required", True),
            nullable=f.get("nullable", True),
            min_value=f.get("min_value", f.get("min")),
            max_value=f.get("max_value", f.get("max")),
            pattern=f.get("pattern"),
            allowed=f.get("allowed", f.get("enum")),
            unique=f.get("unique", False),
        ))
    return schema


# ---------------------------------------------------------------------------
# Type checking helpers
# ---------------------------------------------------------------------------

_TYPE_CHECKERS = {
    "any": lambda v: True,
    "string": lambda v: isinstance(v, str),
    "str": lambda v: isinstance(v, str),
    "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "float": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "bool": lambda v: isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "list": lambda v: isinstance(v, list),
    "dict": lambda v: isinstance(v, dict),
    "null": lambda v: v is None,
}


def check_type(value: Any, dtype: str) -> bool:
    checker = _TYPE_CHECKERS.get(str(dtype).lower())
    if checker is None:
        return True
    return checker(value)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_record(record: dict[str, Any], schema: Schema) -> dict[str, Any]:
    """Validate a single record against a schema. Returns error list."""
    errors = []
    for field in schema.fields:
        value = record.get(field.name)
        present = field.name in record
        if not present:
            if field.required:
                errors.append({"field": field.name, "error": "missing required field"})
            continue
        if value is None:
            if not field.nullable:
                errors.append({"field": field.name, "error": "null not allowed"})
            continue
        if not check_type(value, field.dtype):
            errors.append({"field": field.name, "error": f"type mismatch: expected {field.dtype}, got {type(value).__name__}"})
            continue
        if field.min_value is not None:
            try:
                if value < field.min_value:
                    errors.append({"field": field.name, "error": f"below min {field.min_value}"})
            except TypeError:
                pass
        if field.max_value is not None:
            try:
                if value > field.max_value:
                    errors.append({"field": field.name, "error": f"above max {field.max_value}"})
            except TypeError:
                pass
        if field.pattern is not None and isinstance(value, str):
            if not re.search(field.pattern, value):
                errors.append({"field": field.name, "error": f"pattern mismatch: {field.pattern}"})
        if field.allowed is not None and value not in field.allowed:
            errors.append({"field": field.name, "error": f"value not in allowed set"})
    # unknown fields
    for key in record:
        if key not in schema._by_name:
            errors.append({"field": key, "error": "unknown field"})
    return {"valid": len(errors) == 0, "errors": errors}


def validate_records(records: Iterable[dict[str, Any]], schema: Schema) -> dict[str, Any]:
    """Validate a list of records. Returns summary + per-row errors."""
    results = []
    error_count = 0
    for i, rec in enumerate(records or []):
        r = validate_record(rec, schema)
        if not r["valid"]:
            error_count += 1
        results.append({"index": i, "valid": r["valid"], "errors": r["errors"]})
    # unique check
    for field in schema.fields:
        if field.unique:
            seen = set()
            for i, rec in enumerate(records or []):
                v = rec.get(field.name)
                if v is None:
                    continue
                key = (v if not isinstance(v, (list, dict)) else json.dumps(v, sort_keys=True, default=str))
                if key in seen:
                    results[i]["valid"] = False
                    results[i]["errors"].append({"field": field.name, "error": "duplicate value"})
                    error_count += 1
                seen.add(key)
    return {
        "total": len(results),
        "valid": len(results) - error_count,
        "invalid": error_count,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Data quality report
# ---------------------------------------------------------------------------

def data_quality_report(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Generate a data-quality summary for a list of records."""
    rows = list(records or [])
    if not rows:
        return {"row_count": 0, "column_count": 0, "columns": {}}
    columns = []
    for r in rows:
        for k in r:
            if k not in columns:
                columns.append(k)
    col_info = {}
    for col in columns:
        vals = [r.get(col) for r in rows]
        null_count = sum(1 for v in vals if v is None)
        non_null = [v for v in vals if v is not None]
        distinct = len(set(str(v) for v in non_null))
        col_info[col] = {
            "count": len(vals),
            "null_count": null_count,
            "null_pct": round(null_count / len(vals) * 100, 2) if vals else 0.0,
            "distinct_count": distinct,
            "distinct_pct": round(distinct / len(non_null) * 100, 2) if non_null else 0.0,
            "sample_values": non_null[:5],
        }
    return {"row_count": len(rows), "column_count": len(columns), "columns": col_info}


def missing_value_summary(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Summarize missing values per column."""
    rows = list(records or [])
    if not rows:
        return {}
    columns = []
    for r in rows:
        for k in r:
            if k not in columns:
                columns.append(k)
    out = {}
    for col in columns:
        nulls = sum(1 for r in rows if r.get(col) is None)
        out[col] = {"null_count": nulls, "null_pct": round(nulls / len(rows) * 100, 2) if rows else 0.0}
    return out


def duplicate_rows(records: Iterable[dict[str, Any]]) -> list[int]:
    """Return indices of duplicate rows (by full record equality)."""
    seen = set()
    dupes = []
    for i, r in enumerate(records or []):
        key = json.dumps(r, sort_keys=True, default=str)
        if key in seen:
            dupes.append(i)
        seen.add(key)
    return dupes


def infer_schema(records: Iterable[dict[str, Any]]) -> Schema:
    """Infer a Schema from a list of records."""
    rows = list(records or [])
    if not rows:
        return Schema()
    columns = []
    for r in rows:
        for k in r:
            if k not in columns:
                columns.append(k)
    fields = []
    for col in columns:
        vals = [r.get(col) for r in rows if r.get(col) is not None]
        if not vals:
            dtype = "any"
        elif all(isinstance(v, bool) for v in vals):
            dtype = "bool"
        elif all(isinstance(v, int) and not isinstance(v, bool) for v in vals):
            dtype = "int"
        elif all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
            dtype = "float"
        else:
            dtype = "string"
        nulls = sum(1 for r in rows if r.get(col) is None)
        nullable = nulls > 0
        fields.append(FieldSpec(name=col, dtype=dtype, required=True, nullable=nullable))
    return Schema(fields)



def build_validation_namespace() -> dict[str, Any]:
    return {
        "FieldSpec": FieldSpec,
        "Schema": Schema,
        "build_schema": build_schema,
        "check_type": check_type,
        "validate_record": validate_record,
        "validate_records": validate_records,
        "data_quality_report": data_quality_report,
        "missing_summary": missing_value_summary,
        "duplicate_rows": duplicate_rows,
        "infer_schema": infer_schema,
    }
