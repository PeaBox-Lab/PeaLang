"""Phase 34: std.config module tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pealang.stdlib import build_standard_library


def test_config_parse_ini(tmp_path):
    std = build_standard_library()['std']
    import tempfile
    import os
    ini_content = """
[database]
host = localhost
port = 5432
"""
    ini_file = tmp_path / "test.ini"
    ini_file.write_text(ini_content)
    config = std['config'].parse_ini(str(ini_file))
    assert config['database']['host'] == 'localhost'
    assert config['database']['port'] == '5432'


def test_config_parse_json(tmp_path):
    std = build_standard_library()['std']
    import json
    data = {"name": "test", "version": "1.0"}
    json_file = tmp_path / "config.json"
    json_file.write_text(_json := __import__('json').dumps(data))
    config = std['config'].parse_json(str(json_file))
    assert config['name'] == 'test'
    assert config['version'] == '1.0'


def test_config_get():
    std = build_standard_library()['std']
    config = {'database': {'host': 'localhost', 'port': 5432}}
    assert std['config'].get(config, 'database.host') == 'localhost'
    assert std['config'].get(config, 'database.port') == 5432
    assert std['config'].get(config, 'database.missing', 'default') == 'default'
