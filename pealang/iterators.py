"""Explicit iterator protocol shared by the interpreter and bytecode VM."""
from __future__ import annotations

from typing import Any

ITER_EXHAUSTED = object()
_MISSING = object()


class PeaIterator:
    """A lazy iterator with non-consuming lookahead and explicit cleanup."""

    def __init__(self, source: Any) -> None:
        self._source = iter(source)
        self._buffer: list[Any] = []
        self._closed = False

    def __iter__(self) -> 'PeaIterator':
        return self

    def __next__(self) -> Any:
        if not self._fill():
            raise StopIteration
        return self._buffer.pop(0)

    def _fill(self) -> bool:
        if self._buffer:
            return True
        if self._closed:
            return False
        try:
            self._buffer.append(next(self._source))
            return True
        except StopIteration:
            self._closed = True
            return False

    def has_next(self) -> bool:
        return self._fill()

    def peek(self) -> Any:
        if not self._fill():
            raise StopIteration
        return self._buffer[0]

    def close(self) -> None:
        self._closed = True
        self._buffer.clear()
        close = getattr(self._source, 'close', None)
        if callable(close):
            close()


def make_iterator(value: Any) -> PeaIterator:
    """Return *value* as a PeaIterator, reusing an existing one unchanged."""
    if isinstance(value, PeaIterator):
        return value
    return PeaIterator(value)


def iterator_next(iterator: Any, default: Any = _MISSING) -> Any:
    """Advance an iterator, returning *default* on exhaustion when supplied."""
    try:
        return next(iterator)
    except StopIteration:
        if default is not _MISSING:
            return default
        raise ValueError('Iterator exhausted') from None


def has_next(iterator: Any) -> bool:
    """Return True when the iterator has another value without consuming it."""
    return make_iterator(iterator).has_next()


def peek(iterator: Any) -> Any:
    """Return the next value without consuming it."""
    return make_iterator(iterator).peek()


def close_iterator(iterator: Any) -> None:
    """Close an iterator if it exposes cleanup."""
    if isinstance(iterator, PeaIterator):
        iterator.close()
        return
    close = getattr(iterator, 'close', None)
    if callable(close):
        close()
