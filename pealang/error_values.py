"""Shared structured error values for the interpreter, VM, and host API."""
from __future__ import annotations

from typing import Any

from .errors import ERROR_VALUE_SCHEMA, ErrorValue, PeaError
from .exceptions import EXCEPTION_TYPES, PeaException, UserError


def _cause_value(cause: Any, depth: int = 0) -> Any:
    if cause is None or depth > 8:
        return None
    if isinstance(cause, PeaError):
        return cause.to_value()
    if isinstance(cause, ErrorValue):
        return ErrorValue(cause)
    if isinstance(cause, dict):
        return ErrorValue(cause)
    if isinstance(cause, BaseException):
        return {"kind": type(cause).__name__, "message": str(cause), "code": ""}
    return {"kind": "Value", "message": str(cause), "code": ""}


def build_error(kind: str, message: Any = "", code: Any = "", cause: Any = None,
                context: Any = None) -> ErrorValue:
    """Create a structured error value suitable for `throw` and host APIs."""
    kind = str(kind)
    if kind not in EXCEPTION_TYPES:
        raise PeaError(f"Unknown error kind: {kind}")
    code = str(code) or kind
    value = ErrorValue({
        "schema": ERROR_VALUE_SCHEMA,
        "kind": kind,
        "message": str(message),
        "code": code,
        "cause": _cause_value(cause),
        "context": dict(context) if isinstance(context, dict) else {},
        "source": "",
        "line": None,
        "column": None,
        "end_line": None,
        "end_col": None,
        "frames": None,
        "trace": str(message),
    })
    return value


def is_error_value(value: Any) -> bool:
    return isinstance(value, dict) and (
        value.get("schema") == ERROR_VALUE_SCHEMA or "kind" in value
    )


def error_value_from_exception(exc: BaseException) -> ErrorValue:
    """Normalize any exception into the structured catch/host record."""
    if isinstance(exc, PeaError):
        return exc.to_value()
    return ErrorValue({
        "schema": ERROR_VALUE_SCHEMA,
        "kind": type(exc).__name__,
        "message": str(exc),
        "code": "",
        "cause": _cause_value(exc.__cause__),
        "context": {},
        "source": "<input>",
        "line": None,
        "column": None,
        "end_line": None,
        "end_col": None,
        "frames": None,
        "trace": str(exc),
    })


def error_value_from_raw(value: Any) -> ErrorValue:
    """Normalize a thrown value into the structured catch record."""
    if isinstance(value, PeaError):
        return value.to_value()
    if isinstance(value, ErrorValue):
        return ErrorValue(value)
    if isinstance(value, dict) and is_error_value(value):
        kind = str(value.get("kind", "UserError"))
        message = str(value.get("message", ""))
        normalized = {
            "schema": ERROR_VALUE_SCHEMA,
            "kind": kind if kind in EXCEPTION_TYPES else "UserError",
            "message": message,
            "code": str(value.get("code", "")),
            "cause": _cause_value(value.get("cause")),
            "context": dict(value.get("context") or {}),
            "source": str(value.get("source", "")) if value.get("source") else "",
            "line": value.get("line"),
            "column": value.get("column"),
            "end_line": value.get("end_line"),
            "end_col": value.get("end_col"),
            "frames": value.get("frames"),
            "trace": str(value.get("trace") or message),
        }
        return ErrorValue(normalized)
    message = str(value)
    return ErrorValue({
        "schema": ERROR_VALUE_SCHEMA,
        "kind": "UserError",
        "message": message,
        "code": "",
        "cause": None,
        "context": {},
        "source": "",
        "line": None,
        "column": None,
        "end_line": None,
        "end_col": None,
        "frames": None,
        "trace": message,
    })


def exception_from_error_value(value: Any, span: Any = None,
                               source_name: str = "<input>",
                               frames: Any = None) -> PeaError:
    """Promote a structured error value into a typed PeaLang exception."""
    record = error_value_from_raw(value)
    kind = record.get("kind", "UserError")
    cls = EXCEPTION_TYPES.get(kind, UserError)
    cause = None
    if record.get("cause") is not None:
        cause = exception_from_error_value(record["cause"], span, source_name, frames)
    return cls(
        record.get("message", ""), span, source_name, frames,
        code=record.get("code", ""), cause=cause, context=record.get("context") or {},
    )


def matches_error(value: Any, catch_type: str | None) -> bool:
    """Return whether a thrown value matches an optional typed catch clause."""
    if not catch_type:
        return True
    expected = EXCEPTION_TYPES.get(catch_type)
    if expected is None:
        return True  # Preserve the historical permissive behavior for unknown names.
    if isinstance(value, PeaError):
        actual = EXCEPTION_TYPES.get(getattr(value, "kind", type(value).__name__))
    elif isinstance(value, dict):
        actual = EXCEPTION_TYPES.get(str(value.get("kind", "")))
    else:
        actual = None
    return actual is not None and issubclass(actual, expected)


__all__ = [
    "build_error", "is_error_value", "error_value_from_exception",
    "error_value_from_raw", "exception_from_error_value", "matches_error",
]
