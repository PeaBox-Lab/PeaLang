"""Typed runtime exceptions for PeaLang.

Every exception the language raises derives from `PeaException`, which in turn
derives from `PeaError` (existing API, error formatting preserved). This gives
programs real exception classes to catch, match on, and route with — instead of
one flat PeaError for everything.
"""

from __future__ import annotations

from .errors import PeaError


class PeaException(PeaError):
    """Base class for all PeaLang runtime exceptions."""
    kind = "Exception"


class NameError(PeaException):
    kind = "NameError"


class ValueError(PeaException):
    kind = "ValueError"


class TypeError(PeaException):
    kind = "TypeError"


class IndexError(PeaException):
    kind = "IndexError"


class ZeroDivisionError(PeaException):
    kind = "ZeroDivisionError"


class ScopeError(PeaException):
    kind = "ScopeError"


class AssertionError(PeaException):
    kind = "AssertionError"


class AttributeError(PeaException):
    kind = "AttributeError"


class ImportError(PeaException):
    kind = "ImportError"


class UserError(PeaException):
    """Raised by the `throw` statement."""
    kind = "UserError"


# name -> class mapping for catch-type matching, e.g. `catch ValueError e {}`
EXCEPTION_TYPES = {
    cls.kind: cls
    for cls in (
        PeaException,
        NameError,
        ValueError,
        TypeError,
        IndexError,
        ZeroDivisionError,
        ScopeError,
        AssertionError,
        AttributeError,
        ImportError,
        UserError,
    )
}
