"""Phase 34: std.graph module tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pealang.stdlib import build_standard_library


def test_graph_create():
    std = build_standard_library()['std']
    g = std['graph'].create(directed=False)
    assert g is not None


def test_graph_add_node_and_edge():
    std = build_standard_library()['std']
    g = std.graph.create(directed=False)
    g.add_node("A")
    g.add_node("B")
    g.add_edge("A", "B")
    assert g.has_node("A") is True
    assert g.has_edge("A", "B") is True


def test_graph_bfs():
    std = build_standard_library()['std']
    g = std.graph.create(directed=False)
    g.add_edge("A", "B")
    g.add_edge("B", "C")
    g.add_edge("A", "C")
    order = g.bfs("A")
    assert order[0] == "A"
    assert "B" in order
    assert "C" in order


def test_graph_dfs():
    std = build_standard_library()['std']
    g = std.graph.create(directed=False)
    g.add_edge("A", "B")
    g.add_edge("B", "C")
    g.add_edge("A", "C")
    order = g.dfs("A")
    assert order[0] == "A"
    assert "B" in order
    assert "C" in order


def test_graph_shortest_path():
    std = build_standard_library()['std']
    g = std.graph.create(directed=False)
    g.add_edge("A", "B")
    g.add_edge("B", "C")
    g.add_edge("A", "C")
    path = g.shortest_path("A", "C")
    assert path == ["A", "C"]
