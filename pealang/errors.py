
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
    def __init__(self, message: str, span: Optional[SourceSpan] = None, source_name: str = "<input>"):
        self.message, self.span, self.source_name = message, span, source_name
        super().__init__(self.__str__())
    def __str__(self):
        if self.span:
            return f"{self.source_name}:{self.span.line}:{self.span.col}: {self.message}"
        return self.message

