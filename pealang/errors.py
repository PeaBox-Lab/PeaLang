from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SourceSpan:
    line: int
    col: int
    end_line: Optional[int] = None
    end_col: Optional[int] = None

@dataclass(frozen=True)
class TraceFrame:
    source_name: str
    line: Optional[int] = None
    col: Optional[int] = None
    operation: str = "execute"

class PeaError(Exception):
    """Base PeaLang error with source location, category, and Pea stack frames."""
    category = "runtime"
    def __init__(self, message: str, span: Optional[SourceSpan] = None,
                 source_name: str = "<input>", *, category: Optional[str] = None,
                 frames=None):
        self.message, self.span, self.source_name = str(message), span, source_name
        self.category = category or self.category
        self.frames = list(frames or [])
        super().__init__(self.message)
    def add_frame(self, source_name, span=None, operation="execute"):
        line = span.line if span else None; col = span.col if span else None
        frame = TraceFrame(str(source_name), line, col, str(operation))
        if not self.frames or self.frames[-1] != frame: self.frames.append(frame)
        return self
    def render(self, source_text=None):
        location = f"{self.source_name}:{self.span.line}:{self.span.col}: " if self.span else ""
        lines = [f"{location}{self.category} error: {self.message}"]
        if source_text and self.span:
            src = source_text.splitlines()
            if 1 <= self.span.line <= len(src):
                text = src[self.span.line-1]; lines += [f"  {text}", "  " + " "*max(0,self.span.col-1) + "^"]
        for frame in reversed(self.frames):
            pos = f":{frame.line}:{frame.col}" if frame.line is not None else ""
            lines.append(f"  at {frame.operation} ({frame.source_name}{pos})")
        return "\n".join(lines)
    def __str__(self):
        if self.span: return f"{self.source_name}:{self.span.line}:{self.span.col}: {self.message}"
        return self.message

class PeaSyntaxError(PeaError): category = "syntax"
class PeaRuntimeError(PeaError): category = "runtime"
class PeaImportError(PeaError): category = "import"
class PeaProjectError(PeaError): category = "project"
class PeaPermissionError(PeaError): category = "permission"
