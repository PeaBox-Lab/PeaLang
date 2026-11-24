import re
from pathlib import Path

import pytest

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def assert_output_approx(actual, expected, tolerance=0.02):
    """Compare example output, allowing small cross-version float drift."""
    assert len(actual) == len(expected)
    number_at_end = re.compile(r"^(.*?)(-?\d+(?:\.\d+)?)$")
    for got, want in zip(actual, expected):
        match = number_at_end.match(want)
        if not match:
            assert got == want
            continue
        prefix, expected_number = match.groups()
        assert got.startswith(prefix)
        got_number = got[len(prefix):]
        try:
            value = float(got_number)
        except ValueError:
            assert got == want
        else:
            assert value == pytest.approx(float(expected_number), abs=tolerance)


def test_trees_forests_example(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    name = "15_trees_forests.pea"
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    assert_output_approx(out, [
        "tree r2: 0.968",
        "tree rmse: 0.221",
        "forest r2: 0.986",
        "forest rmse: 0.148",
        "forest oob r2: 0.962",
        "class accuracy: 0.967",
        "class oob: 0.933",
        "top feature: b",
        "tree accuracy: 0.917",
        "tree top: b",
        "tree guess: [0, 1]",
    ])
