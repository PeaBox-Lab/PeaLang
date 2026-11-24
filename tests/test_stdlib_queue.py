"""Phase 34: std.queue module tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pealang.stdlib import build_standard_library


def test_queue_create():
    std = build_standard_library()['std']
    q = std['queue'].create()
    assert q is not None


def test_queue_enqueue_dequeue():
    std = build_standard_library()['std']
    q = std['queue'].create()
    q.enqueue("first")
    q.enqueue("second")
    assert q.dequeue() == "first"
    assert q.dequeue() == "second"


def test_queue_is_empty():
    std = build_standard_library()['std']
    q = std['queue'].create()
    assert q.is_empty() is True
    q.enqueue("first")
    assert q.is_empty() is False


def test_queue_size():
    std = build_standard_library()['std']
    q = std['queue'].create()
    assert q.size() == 0
    q.enqueue("first")
    assert q.size() == 1


def test_queue_peek():
    std = build_standard_library()['std']
    q = std['queue'].create()
    q.enqueue("first")
    assert q.peek() == "first"
    q.dequeue()
    assert q.is_empty() is True


def test_priority_queue():
    std = build_standard_library()['std']
    pq = std['queue'].priority_create()
    pq.push("low", 1)
    pq.push("high", 10)
    pq.push("mid", 5)
    assert pq.pop() == "high"
    assert pq.pop() == "mid"
    assert pq.pop() == "low"
