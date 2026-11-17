from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SourceSpan:
    line: int
    col: int
    end_line: Optional[int] = None
    end_col: Optional[int] = None

class PeaError(Exception):
    def __init__(self, message: str, span: Optional[SourceSpan] = None, source_name: str = "<input>", frames: Optional[list] = None):
        self.message, self.span, self.source_name = message, span, source_name
        self.frames = frames
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
