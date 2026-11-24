"""Phase 34: std.env module tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pealang.stdlib import build_standard_library


def test_env_get():
    std = build_standard_library()['std']
    std['env'].set("TEST_VAR", "hello")
    assert std['env'].get("TEST_VAR") == "hello"
    assert std['env'].get("MISSING", "default") == "default"


def test_env_set_get():
    std = build_standard_library()['std']
    std['env'].set("MY_VAR", "test_value")
    assert std['env'].get("MY_VAR") == "test_value"


def test_env_unset():
    std = build_standard_library()['std']
    std['env'].set("TEST_VAR", "hello")
    assert std['env'].has("TEST_VAR") is True
    std['env'].unset("TEST_VAR")
    assert std['env'].has("TEST_VAR") is False


def test_env_has():
    std = build_standard_library()['std']
    std['env'].set("TEST_VAR", "hello")
    assert std['env'].has("TEST_VAR") is True
    assert std['env'].has("MISSING") is False


def test_env_keys():
    std = build_standard_library()['std']
    std['env'].set("VAR1", "val1")
    std['env'].set("VAR2", "val2")
    keys = std['env'].keys()
    assert "VAR1" in keys
    assert "VAR2" in keys
