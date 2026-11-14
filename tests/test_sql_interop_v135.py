"""Regression coverage for v135 SQL/dataframe interop."""

from pealang.sql_interop import (
    build_sql_interop_namespace,
    sql_query,
    sql_value,
    dataframe_from_records,
    dataframe_select,
    dataframe_filter,
    dataframe_sort,
    dataframe_groupby,
    dataframe_to_records,
    dataframe_head,
    dataframe_tail,
    dataframe_describe,
    window_function,
)


def test_sql_query():
    data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    result = sql_query(data, "SELECT * FROM data WHERE age > 26")
    assert len(result) == 1
    assert result[0]["name"] == "Alice"


def test_sql_value():
    data = [{"x": 10}, {"x": 20}]
    result = sql_value(data, "SELECT SUM(x) FROM data")
    assert result == 30


def test_dataframe_from_records():
    data = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    df = dataframe_from_records(data)
    assert df["shape"] == (2, 2)
    assert df["columns"] == ["a", "b"]


def test_dataframe_select():
    data = [{"a": 1, "b": "x", "c": 3}]
    df = dataframe_from_records(data)
    sel = dataframe_select(df, ["a", "c"])
    assert sel["columns"] == ["a", "c"]
    assert sel["rows"][0] == {"a": 1, "c": 3}


def test_dataframe_filter():
    data = [{"a": 1}, {"a": 5}, {"a": 3}]
    df = dataframe_from_records(data)
    filt = dataframe_filter(df, "a > 2")
    assert len(filt["rows"]) == 2


def test_dataframe_sort():
    data = [{"a": 3}, {"a": 1}, {"a": 2}]
    df = dataframe_from_records(data)
    sorted_df = dataframe_sort(df, "a")
    assert sorted_df["rows"][0]["a"] == 1


def test_dataframe_groupby():
    data = [{"g": "a", "v": 1}, {"g": "a", "v": 2}, {"g": "b", "v": 3}]
    df = dataframe_from_records(data)
    result = dataframe_groupby(df, "g", "v", "sum")
    assert len(result) == 2


def test_dataframe_head_tail():
    data = [{"a": i} for i in range(10)]
    df = dataframe_from_records(data)
    assert len(dataframe_head(df, 3)["rows"]) == 3
    assert len(dataframe_tail(df, 3)["rows"]) == 3


def test_dataframe_describe():
    data = [{"x": 1}, {"x": 2}, {"x": 3}]
    df = dataframe_from_records(data)
    desc = dataframe_describe(df)
    assert "x" in desc
    assert desc["x"]["mean"] == 2.0


def test_window_function():
    data = [{"g": "a", "v": 10}, {"g": "a", "v": 20}]
    result = window_function(data, "v", "row_number", partition_by="g", order_by="v")
    assert len(result) == 2
    assert result[0]["v_row_number"] == 1


def test_build_sql_interop_namespace():
    ns = build_sql_interop_namespace()
    assert "sql_query" in ns
    assert "dataframe_from_records" in ns
    assert "window_function" in ns
    assert len(ns) == 12
