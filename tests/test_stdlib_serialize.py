"""Phase 34: std.serialize module tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pealang.stdlib import build_standard_library


def test_json_dumps():
    std = build_standard_library()['std']
    result = std['serialize'].json_dumps({"a": 1, "b": 2})
    assert '"a"' in result
    assert '1' in result


def test_json_loads():
    std = build_standard_library()['std']
    result = std['serialize'].json_loads('{"a": 1, "b": 2}')
    assert result == {"a": 1, "b": 2}


def test_csv_dumps():
    std = build_standard_library()['std']
    rows = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    csv = std['serialize'].csv_dumps(rows)
    assert "name" in csv
    assert "Alice" in csv


def test_csv_loads():
    std = build_standard_library()['std']
    rows = std['serialize'].csv_loads("name,age\nAlice,30\nBob,25")
    assert len(rows) == 2
    assert rows[0]["name"] == "Alice"
