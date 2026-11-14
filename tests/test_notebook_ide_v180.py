"""Regression coverage for v1.8.0 notebook IDE."""

from pealang.notebook_ide import (
    build_notebook_ide_namespace,
    ReactiveCell,
    ReactiveNotebook,
    inspect_dataframe,
    inspect_sql_result,
    publish_as_webapp,
    generate_notebook_html,
)


def test_reactive_cell():
    cell = ReactiveCell("c1", "let x = 1")
    assert cell.cell_id == "c1"
    assert cell.dirty is True
    d = cell.to_dict()
    assert d["cell_id"] == "c1"


def test_reactive_notebook():
    nb = ReactiveNotebook()
    nb.add_cell("c1", "let x = 1")
    nb.add_cell("c2", "print x", ["c1"])
    assert len(nb.cells) == 2
    assert nb.get_dependents("c1") == ["c2"]
    order = nb.execution_order()
    assert order.index("c1") < order.index("c2")


def test_reactive_notebook_remove():
    nb = ReactiveNotebook()
    nb.add_cell("c1", "let x = 1")
    nb.add_cell("c2", "print x", ["c1"])
    assert nb.remove_cell("c1") is True
    assert "c1" not in nb.cells
    assert "c1" not in nb.cells["c2"].dependencies


def test_reactive_notebook_mark_dirty():
    nb = ReactiveNotebook()
    nb.add_cell("c1", "let x = 1")
    nb.add_cell("c2", "print x", ["c1"])
    nb.cells["c1"].dirty = False
    nb.cells["c2"].dirty = False
    affected = nb.mark_dirty("c1")
    assert "c1" in affected
    assert "c2" in affected
    assert nb.cells["c1"].dirty is True
    assert nb.cells["c2"].dirty is True


def test_inspect_dataframe():
    data = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}, {"a": None, "b": "x"}]
    result = inspect_dataframe(data)
    assert result["row_count"] == 3
    assert result["column_count"] == 2
    assert result["columns"][0]["name"] == "a"
    assert result["columns"][0]["null_count"] == 1


def test_inspect_sql_result():
    result = inspect_sql_result("SELECT * FROM data", [{"a": 1}, {"a": 2}])
    assert result["row_count"] == 2
    assert result["column_count"] == 1
    assert result["columns"] == ["a"]


def test_publish_as_webapp():
    result = publish_as_webapp("print 42", title="My App")
    assert result["title"] == "My App"
    assert "index.html" in result["files"]
    assert "<html" in result["html"]


def test_generate_notebook_html():
    cells = [{"source": "let x = 1", "output": "1"}]
    html = generate_notebook_html(cells)
    assert "PeaLang Notebook" in html
    assert "let x = 1" in html
    assert "1" in html


def test_build_notebook_ide_namespace():
    ns = build_notebook_ide_namespace()
    assert "ReactiveCell" in ns
    assert "ReactiveNotebook" in ns
    assert "inspect_dataframe" in ns
    assert "publish_as_webapp" in ns
    assert len(ns) == 6
