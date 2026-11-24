"""Phase 34: std.uuid module tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pealang.stdlib import build_standard_library


def test_uuid_v4():
    std = build_standard_library()['std']
    uuid = std['uuid'].v4()
    assert isinstance(uuid, str)
    assert len(uuid) == 32


def test_uuid_v4_full():
    std = build_standard_library()['std']
    uuid = std['uuid'].v4_full()
    assert isinstance(uuid, str)
    assert len(uuid) == 36


def test_uuid_v1():
    std = build_standard_library()['std']
    uuid = std['uuid'].v1()
    assert isinstance(uuid, str)
    assert len(uuid) == 36


def test_uuid_v3():
    std = build_standard_library()['std']
    uuid = std['uuid'].v3('6ba7b810-9dad-11d1-80b4-00c04fd430c8', 'example.com')
    assert isinstance(uuid, str)
    assert len(uuid) == 36


def test_uuid_v5():
    std = build_standard_library()['std']
    uuid = std['uuid'].v5('6ba7b810-9dad-11d1-80b4-00c04fd430c8', 'example.com')
    assert isinstance(uuid, str)
    assert len(uuid) == 36


def test_uuid_random():
    std = build_standard_library()['std']
    uuid = std['uuid'].random()
    assert isinstance(uuid, str)
    assert len(uuid) == 32
