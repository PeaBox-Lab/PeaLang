"""Regression coverage for v132 data validation and schema enforcement."""

from pealang.validation import (
    build_validation_namespace,
    FieldSpec,
    Schema,
    build_schema,
    check_type,
    validate_record,
    validate_records,
    data_quality_report,
    missing_value_summary as missing_summary,
    duplicate_rows,
    infer_schema,
)


def test_check_type():
    assert check_type(5, "int") is True
    assert check_type(5.0, "int") is False
    assert check_type("hello", "string") is True
    assert check_type(True, "bool") is True


def test_validate_record_valid():
    schema = build_schema([{"name": "age", "dtype": "int", "required": True, "nullable": False}])
    result = validate_record({"age": 30}, schema)
    assert result["valid"] is True
    assert result["errors"] == []


def test_validate_record_missing():
    schema = build_schema([{"name": "age", "dtype": "int", "required": True}])
    result = validate_record({}, schema)
    assert result["valid"] is False
    assert any(e["error"] == "missing required field" for e in result["errors"])


def test_validate_record_type_mismatch():
    schema = build_schema([{"name": "age", "dtype": "int", "required": True}])
    result = validate_record({"age": "thirty"}, schema)
    assert result["valid"] is False


def test_validate_record_min_max():
    schema = build_schema([{"name": "age", "dtype": "int", "min_value": 0, "max_value": 100}])
    assert validate_record({"age": 50}, schema)["valid"] is True
    assert validate_record({"age": 150}, schema)["valid"] is False
    assert validate_record({"age": -5}, schema)["valid"] is False


def test_validate_record_pattern():
    schema = build_schema([{"name": "email", "dtype": "string", "pattern": r"@.*\.com$"}])
    assert validate_record({"email": "a@b.com"}, schema)["valid"] is True
    assert validate_record({"email": "a@b.org"}, schema)["valid"] is False


def test_validate_record_allowed():
    schema = build_schema([{"name": "status", "dtype": "string", "allowed": ["active", "inactive"]}])
    assert validate_record({"status": "active"}, schema)["valid"] is True
    assert validate_record({"status": "pending"}, schema)["valid"] is False


def test_validate_records():
    schema = build_schema([{"name": "x", "dtype": "int"}])
    result = validate_records([{"x": 1}, {"x": 2}, {"x": "bad"}], schema)
    assert result["total"] == 3
    assert result["valid"] == 2
    assert result["invalid"] == 1


def test_unique_constraint():
    schema = build_schema([{"name": "id", "dtype": "int", "unique": True}])
    result = validate_records([{"id": 1}, {"id": 1}], schema)
    assert result["invalid"] >= 1


def test_data_quality_report():
    rows = [{"a": 1, "b": None}, {"a": 2, "b": "x"}, {"a": None, "b": "y"}]
    report = data_quality_report(rows)
    assert report["row_count"] == 3
    assert report["column_count"] == 2
    assert report["columns"]["a"]["null_count"] == 1
    assert report["columns"]["b"]["null_count"] == 1


def test_missing_summary():
    rows = [{"a": 1, "b": None}, {"a": None, "b": "x"}]
    ms = missing_summary(rows)
    assert ms["a"]["null_count"] == 1
    assert ms["b"]["null_count"] == 1


def test_duplicate_rows():
    rows = [{"a": 1}, {"a": 2}, {"a": 1}]
    dupes = duplicate_rows(rows)
    assert 2 in dupes


def test_infer_schema():
    rows = [{"name": "Alice", "age": 30, "active": True}, {"name": "Bob", "age": 25, "active": False}]
    schema = infer_schema(rows)
    assert schema.field("name").dtype == "string"
    assert schema.field("age").dtype == "int"
    assert schema.field("active").dtype == "bool"


def test_build_schema():
    schema = build_schema([{"name": "x", "dtype": "float"}])
    assert schema.field("x").dtype == "float"


def test_build_validation_namespace():
    ns = build_validation_namespace()
    assert "validate_record" in ns
    assert "infer_schema" in ns
    assert "data_quality_report" in ns
    assert len(ns) >= 8
