"""Phase 34: std.cache module tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pealang.stdlib import build_standard_library


def test_cache_set_get():
    std = build_standard_library()['std']
    cache = std['cache']
    cache.set('key1', 'value1', ttl=60)
    assert cache.get('key1') == 'value1'


def test_cache_get_default():
    std = build_standard_library()['std']
    cache = std['cache']
    assert cache.get('missing', 'default') == 'default'


def test_cache_has():
    std = build_standard_library()['std']
    cache = std['cache']
    cache.set('key1', 'value1')
    assert cache.has('key1') is True
    assert cache.has('missing') is False


def test_cache_delete():
    std = build_standard_library()['std']
    cache = std['cache']
    cache.set('key1', 'value1')
    assert cache.delete('key1') is True
    assert cache.has('key1') is False
    assert cache.delete('key1') is False


def test_cache_clear():
    std = build_standard_library()['std']
    cache = std['cache']
    cache.set('key1', 'value1')
    cache.set('key2', 'value2')
    cache.clear()
    assert cache.size() == 0


def test_cache_keys():
    std = build_standard_library()['std']
    cache = std['cache']
    cache.set('a', '1')
    cache.set('b', '2')
    assert set(cache.keys()) == {'a', 'b'}
