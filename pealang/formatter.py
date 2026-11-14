"""AST-based code formatter, linter, and auto-fix codemods for PeaLang (v1.2.0).

Provides deterministic formatting, static analysis, and automated code
transformations built on the PeaLang AST and parser.
"""

from __future__ import annotations

import re
from typing import Any

from .lexer import Lexer
from .parser import Parser, parse_source
from .ast_nodes import *


# ---------------------------------------------------------------------------
# AST-based formatter
# ---------------------------------------------------------------------------

class PeaFormatter:
    """Deterministic AST-based code formatter."""

    def __init__(self, indent_size: int = 4):
        self.indent_size = indent_size
        self._indent = 0

    def _ind(self) -> str:
        return " " * (self._indent * self.indent_size)

    def format(self, source: str) -> str:
        try:
            program = parse_source(source)
        except Exception:
            # Fall back to token-based formatting
            from .tooling import format_source as tok_fmt
            return tok_fmt(source)
        lines = self._format_program(program)
        return "\n".join(lines) + "\n"

    def _format_program(self, program) -> list[str]:
        out = []
        for stmt in getattr(program, "statements", []) or getattr(program, "body", []) or []:
            out.extend(self._format_stmt(stmt))
        return out

    def _format_stmt(self, stmt) -> list[str]:
        t = type(stmt).__name__
        if "Let" in t or "Const" in t:
            name = getattr(stmt, "name", "")
            value = self._format_expr(getattr(stmt, "value", None)) if getattr(stmt, "value", None) is not None else ""
            if value:
                return [f"{self._ind()}let {name} = {value}"]
            return [f"{self._ind()}let {name}"]
        if "Print" in t:
            args = [self._format_expr(a) for a in getattr(stmt, "args", []) or [getattr(stmt, "value", None)]]
            args = [a for a in args if a]
            return [f"{self._ind()}print " + ", ".join(args)]
        if "If" in t:
            cond = self._format_expr(getattr(stmt, "condition", None))
            out = [f"{self._ind()}if {cond} {{"]
            self._indent += 1
            for s in getattr(stmt, "then_body", []) or getattr(stmt, "body", []) or []:
                out.extend(self._format_stmt(s))
            self._indent -= 1
            out.append(f"{self._ind()}" + "}")
            else_body = getattr(stmt, "else_body", None)
            if else_body:
                out[-1] = out[-1] + " else {"
                self._indent += 1
                for s in else_body:
                    out.extend(self._format_stmt(s))
                self._indent -= 1
                out.append(f"{self._ind()}" + "}")
            return out
        if "For" in t:
            var = getattr(stmt, "variable", getattr(stmt, "var", ""))
            iterable = self._format_expr(getattr(stmt, "iterable", None))
            out = [f"{self._ind()}for {var} in {iterable} {{"]
            self._indent += 1
            for s in getattr(stmt, "body", []) or []:
                out.extend(self._format_stmt(s))
            self._indent -= 1
            out.append(f"{self._ind()}" + "}")
            return out
        if "While" in t:
            cond = self._format_expr(getattr(stmt, "condition", None))
            out = [f"{self._ind()}while {cond} {{"]
            self._indent += 1
            for s in getattr(stmt, "body", []) or []:
                out.extend(self._format_stmt(s))
            self._indent -= 1
            out.append(f"{self._ind()}" + "}")
            return out
        if "Return" in t:
            val = self._format_expr(getattr(stmt, "value", None))
            if val:
                return [f"{self._ind()}return {val}"]
            return [f"{self._ind()}return"]
        if "Function" in t or "FuncDef" in t:
            name = getattr(stmt, "name", "")
            params = getattr(stmt, "params", [])
            param_str = ", ".join(str(p) for p in params)
            out = [f"{self._ind()}function {name}({param_str}) {{"]
            self._indent += 1
            for s in getattr(stmt, "body", []) or []:
                out.extend(self._format_stmt(s))
            self._indent -= 1
            out.append(f"{self._ind()}" + "}")
            return out
        if "Expr" in t or "Expression" in t:
            expr = self._format_expr(getattr(stmt, "expr", getattr(stmt, "value", None)))
            if expr:
                return [f"{self._ind()}{expr}"]
            return []
        # Fallback: stringify
        return [f"{self._ind()}{str(stmt)}"]

    def _format_expr(self, expr) -> str:
        if expr is None:
            return ""
        t = type(expr).__name__
        if "Literal" in t or "Number" in t:
            return str(getattr(expr, "value", ""))
        if "String" in t:
            return repr(getattr(expr, "value", ""))
        if "Variable" in t or "Identifier" in t:
            return str(getattr(expr, "name", getattr(expr, "value", "")))
        if "Binary" in t:
            left = self._format_expr(getattr(expr, "left", None))
            op = getattr(expr, "op", "+")
            right = self._format_expr(getattr(expr, "right", None))
            return f"{left} {op} {right}"
        if "Call" in t:
            func = self._format_expr(getattr(expr, "func", None))
            args = [self._format_expr(a) for a in getattr(expr, "args", []) or []]
            return f"{func}(" + ", ".join(args) + ")"
        if "Index" in t:
            target = self._format_expr(getattr(expr, "target", None))
            idx = self._format_expr(getattr(expr, "index", None))
            return f"{target}[{idx}]"
        if "List" in t:
            items = [self._format_expr(i) for i in getattr(expr, "items", []) or []]
            return "[" + ", ".join(items) + "]"
        if "Dict" in t:
            pairs = getattr(expr, "pairs", []) or []
            items = [f"{self._format_expr(k)}: {self._format_expr(v)}" for k, v in pairs]
            return "{" + ", ".join(items) + "}"
        return str(expr)


def format_source_ast(source: str, indent_size: int = 4) -> str:
    """Format source using AST-based formatter."""
    fmt = PeaFormatter(indent_size=indent_size)
    return fmt.format(source)


# ---------------------------------------------------------------------------
# Static linter (dead code, complexity, naming)
# ---------------------------------------------------------------------------

class PeaLinter:
    """Static linter for PeaLang source."""

    def __init__(self):
        self.issues = []

    def lint(self, source: str) -> list[dict[str, Any]]:
        self.issues = []
        try:
            program = parse_source(source)
        except Exception as e:
            self.issues.append({"line": 0, "severity": "error", "message": f"Parse error: {e}"})
            return self.issues
        self._check_complexity(program, source)
        self._check_naming(program)
        self._check_dead_code(program)
        self._check_style(source)
        return self.issues

    def _check_complexity(self, program, source):
        for node in self._walk(program):
            t = type(node).__name__
            if "Function" in t or "FuncDef" in t:
                body = getattr(node, "body", []) or []
                if len(body) > 50:
                    self.issues.append({"line": getattr(node, "line", 0), "severity": "warning",
                                        "message": f"Function too long ({len(body)} statements)"})
                # Cyclomatic complexity
                complexity = 1
                for n in self._walk(node):
                    nt = type(n).__name__
                    if "If" in nt or "While" in nt or "For" in nt:
                        complexity += 1
                if complexity > 10:
                    self.issues.append({"line": getattr(node, "line", 0), "severity": "warning",
                                        "message": f"High cyclomatic complexity ({complexity})"})

    def _check_naming(self, program):
        for node in self._walk(program):
            t = type(node).__name__
            if "Function" in t or "FuncDef" in t:
                name = getattr(node, "name", "")
                if name and not name[0].islower():
                    self.issues.append({"line": getattr(node, "line", 0), "severity": "warning",
                                        "message": f"Function name '{name}' should start with lowercase"})
            if "Let" in t or "Const" in t:
                name = getattr(node, "name", "")
                if name and name[0].isupper():
                    self.issues.append({"line": getattr(node, "line", 0), "severity": "info",
                                        "message": f"Variable '{name}' should start with lowercase"})

    def _check_dead_code(self, program):
        # Check for unreachable code after return
        for node in self._walk(program):
            t = type(node).__name__
            if "Function" in t or "FuncDef" in t:
                body = getattr(node, "body", []) or []
                terminated = False
                for i, stmt in enumerate(body):
                    if terminated:
                        self.issues.append({"line": getattr(stmt, "line", 0), "severity": "warning",
                                            "message": "Unreachable code after return/throw"})
                        break
                    st = type(stmt).__name__
                    if "Return" in st or "Throw" in st:
                        terminated = True

    def _check_style(self, source):
        lines = source.splitlines()
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                self.issues.append({"line": i, "severity": "warning", "message": f"Line too long ({len(line)} > 120)"})
            if line != line.rstrip():
                self.issues.append({"line": i, "severity": "info", "message": "Trailing whitespace"})
            if "TODO" in line or "FIXME" in line:
                self.issues.append({"line": i, "severity": "info", "message": "TODO/FIXME found"})

    def _walk(self, node):
        result = [node]
        for attr in dir(node):
            if attr.startswith("_"):
                continue
            val = getattr(node, attr, None)
            if isinstance(val, list):
                for item in val:
                    if hasattr(item, "__dict__"):
                        result.extend(self._walk(item))
            elif hasattr(val, "__dict__") and not isinstance(val, (str, int, float, bool)):
                result.extend(self._walk(val))
        return result


def lint_source_ast(source: str) -> list[dict[str, Any]]:
    """Lint source using AST-based linter."""
    linter = PeaLinter()
    return linter.lint(source)


# ---------------------------------------------------------------------------
# Auto-fix codemods
# ---------------------------------------------------------------------------

def codemod_remove_unused_imports(source: str) -> str:
    """Remove unused import statements."""
    # Simple heuristic: find import lines and check if the imported name is used
    lines = source.splitlines()
    result = []
    for line in lines:
        m = re.match(r'^\s*import\s+(\w+)', line.strip())
        if m:
            name = m.group(1)
            # Check if name is used elsewhere
            rest = "\n".join(l for l in lines if l != line)
            if name not in rest.split():
                continue  # skip this import
        result.append(line)
    return "\n".join(result)


def codemod_add_missing_semicolons(source: str) -> str:
    """Add missing semicolons (no-op in PeaLang, which uses newlines)."""
    return source


def codemod_rename_variable(source: str, old_name: str, new_name: str) -> str:
    """Rename a variable throughout the source."""
    # Simple word-boundary replacement
    return re.sub(r'\b' + re.escape(old_name) + r'\b', new_name, source)


def codemod_fix_naming(source: str) -> str:
    """Fix naming conventions (camelCase to snake_case for functions)."""
    def to_snake(name):
        s = re.sub(r'([A-Z])', r'_\1', name).lower().lstrip('_')
        return s
    # Find function definitions and rename
    def replace_func(m):
        prefix = m.group(1)
        name = m.group(2)
        return prefix + to_snake(name)
    return re.sub(r'(function\s+)([A-Za-z_]\w*)', lambda m: m.group(1) + to_snake(m.group(2)), source)


def build_formatter_namespace() -> dict[str, Any]:
    return {
        "PeaFormatter": PeaFormatter,
        "format_source_ast": format_source_ast,
        "PeaLinter": PeaLinter,
        "lint_source_ast": lint_source_ast,
        "codemod_remove_unused_imports": codemod_remove_unused_imports,
        "codemod_rename_variable": codemod_rename_variable,
        "codemod_fix_naming": codemod_fix_naming,
    }
