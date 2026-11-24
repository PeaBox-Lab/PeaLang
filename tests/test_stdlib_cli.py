"""Phase 34: std.cli module tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pealang.stdlib import build_standard_library


def test_cli_parse_with_flags():
    std = build_standard_library()['std']
    import sys as _sys
    _sys.argv = ['pea', '--verbose', '--output', 'result.txt']
    result = std['cli'].parse()
    assert result['verbose'] is True
    assert result['output'] == 'result.txt'
    assert result['_positional'] == []


def test_cli_parse_positional_only():
    std = build_standard_library()['std']
    import sys as _sys
    _sys.argv = ['pea', 'file1.pea', 'file2.pea']
    result = std['cli'].parse()
    assert result['_positional'] == ['file1.pea', 'file2.pea']


def test_cli_has():
    std = build_standard_library()['std']
    import sys as _sys
    _sys.argv = ['pea', '--verbose']
    assert std['cli'].has('verbose') is True
    assert std['cli'].has('missing') is False


def test_cli_get():
    std = build_standard_library()['std']
    import sys as _sys
    _sys.argv = ['pea', '--output', 'result.txt']
    assert std['cli'].get('output') == 'result.txt'
    assert std['cli'].get('missing', 'default') == 'default'
