from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

ERROR_VALUE_SCHEMA = "pealang-error-v1"


@dataclass(frozen=True)
class SourceSpan:
    line: int
    col: int
    end_line: Optional[int] = None
    end_col: Optional[int] = None


class ErrorValue(dict):
    """Structured, script-visible error record that stringifies to its message."""

    def __str__(self):
        return str(self.get("message", ""))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, str):
            return self.get("message") == other
        return dict.__eq__(self, other)

    __hash__ = None


class PeaError(Exception):
    def __init__(self, message: str, span: Optional[SourceSpan] = None,
                 source_name: str = "<input>", frames: Optional[list] = None, *,
                 code: str = "", cause: Any = None, context: Optional[dict] = None):
        self.message, self.span, self.source_name = message, span, source_name
        self.frames = frames
        self.code = str(code) if code else str(getattr(self, "kind", ""))
        self.cause = cause
        self.context = dict(context or {})
        super().__init__(self.__str__())

    def __str__(self):
        if self.span:
            return f"{self.source_name}:{self.span.line}:{self.span.col}: {self.message}"
        return self.message

    def trace(self) -> str:
        """Return a human-readable stack trace including user-function frames."""
        if not self.frames:
            return str(self)
        lines = [str(self), "Traceback (most recent call last):"]
        for frame in self.frames:
            name = frame.get("name", "<anonymous>")
            src = frame.get("call_source") or frame.get("source", self.source_name)
            line = frame.get("call_line") if frame.get("call_line") is not None else frame.get("line", 0)
            def_line = frame.get("line", 0)
            if frame.get("call_line") is not None and frame.get("call_line") != def_line:
                lines.append(f'  File "{src}", line {line}, in {name} (defined at line {def_line})')
            else:
                lines.append(f'  File "{src}", line {line}, in {name}')
        return "\n".join(lines)

    def to_value(self) -> ErrorValue:
        """Return the structured record exposed to `catch` bindings and hosts."""
        cause = self.cause if self.cause is not None else self.__cause__
        cause_value = None
        if isinstance(cause, PeaError):
            cause_value = cause.to_value()
        elif cause is not None:
            cause_value = {"kind": type(cause).__name__, "message": str(cause), "code": ""}
        return ErrorValue({
            "schema": ERROR_VALUE_SCHEMA,
            "kind": getattr(self, "kind", type(self).__name__),
            "message": self.message,
            "code": self.code,
            "cause": cause_value,
            "context": dict(self.context),
            "source": self.source_name,
            "line": self.span.line if self.span else None,
            "column": self.span.col if self.span else None,
            "end_line": self.span.end_line if self.span else None,
            "end_col": self.span.end_col if self.span else None,
            "frames": self.frames,
            "trace": self.trace(),
        })
