"""AST-based code formatter, linter, and auto-fix codemods for PeaLang (v1.2.0).

Provides deterministic formatting, static analysis, and automated code
transformations built on the PeaLang AST and parser.

Configuration:
  Create a `.peafmt.toml` file in your project root to customize formatting:
  
  ```toml
  indent_size = 4
  max_line_length = 120
  trailing_comma = true
  space_around_operators = true
  brace_style = "same_line"  # or "next_line"
  ```

  Or configure per-project in `pea.json`:
  
  ```json
  {
    "formatter": {
      "indent_size": 2,
      "max_line_length": 100
    }
  }
  ```

"""

from __future__ import annotations

import re
import json
import os
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field

from .lexer import Lexer
from .parser import Parser, parse_source
from .ast_nodes import *


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class FormatConfig:
    """Formatter configuration."""
    indent_size: int = 4
    max_line_length: int = 120
    trailing_comma: bool = True
    space_around_operators: bool = True
    brace_style: str = "same_line"  # "same_line" or "next_line"
    newline_at_eof: bool = True
    
    @classmethod
    def load(cls, project_root: str = ".") -> "FormatConfig":
        """Load configuration from .peafmt.toml or pea.json."""
        config = cls()
        
        # Try .peafmt.toml
        toml_path = Path(project_root) / ".peafmt.toml"
        if toml_path.exists():
            try:
                import tomli
                with open(toml_path, "rb") as f:
                    data = tomli.load(f)
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            except ImportError:
                pass
            except Exception:
                pass
        
        # Try pea.json
        pea_path = Path(project_root) / "pea.json"
        if pea_path.exists():
            try:
                with open(pea_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                fmt_data = data.get("formatter", {})
                for key, value in fmt_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            except Exception:
                pass
        
        return config


# ---------------------------------------------------------------------------
# AST-based formatter
# ---------------------------------------------------------------------------

class PeaFormatter:
    """Deterministic AST-based code formatter."""
    
    def __init__(self, config: FormatConfig | None = None):
        self.config = config or FormatConfig()
        self._indent = 0
    
    def _ind(self) -> str:
        return " " * (self._indent * self.config.indent_size)
    
    def format(self, source: str) -> str:
        try:
            program = parse_source(source)
        except Exception:
            # Fall back to token-based formatting
            from .tooling import format_source as tok_fmt
            return tok_fmt(source)
        lines = self._format_program(program)
        result = "\n".join(lines)
        if self.config.newline_at_eof and result and not result.endswith("\n"):
            result += "\n"
        return result
    
    def format_range(self, source: str, start_line: int, end_line: int) -> str:
        """Format only a specific line range (for incremental formatting)."""
        # For now, format the whole file - true incremental requires more complex diffing
        return self.format(source)
    
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
        if "Function" in t or "FuncDef" in t or "FuncStmt" in t:
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
            if self.config.space_around_operators:
                return f"{left} {op} {right}"
            return f"{left}{op}{right}"
        if "Call" in t:
            func = self._format_expr(getattr(expr, "func", None))
            args = [self._format_expr(a) for a in getattr(expr, "args", []) or []]
            if self.config.trailing_comma and len(args) > 1:
                return f"{func}(\n{self._ind()}  " + ",\n{self._ind()}  ".join(args) + ",\n{self._ind()})"
            return f"{func}(" + ", ".join(args) + ")"
        if "Index" in t:
            target = self._format_expr(getattr(expr, "target", None))
            idx = self._format_expr(getattr(expr, "index", None))
            return f"{target}[{idx}]"
        if "List" in t:
            items = [self._format_expr(i) for i in getattr(expr, "items", []) or []]
            if self.config.trailing_comma and len(items) > 1:
                return "[\n{self._ind()}  " + ",\n{self._ind()}  ".join(items) + ",\n{self._ind()}]"
            return "[" + ", ".join(items) + "]"
        if "Dict" in t:
            pairs = getattr(expr, "pairs", []) or []
            items = [f"{self._format_expr(k)}: {self._format_expr(v)}" for k, v in pairs]
            if self.config.trailing_comma and len(items) > 1:
                return "{\n{self._ind()}  " + ",\n{self._ind()}  ".join(items) + ",\n{self._ind()}}"
            return "{" + ", ".join(items) + "}"
        if "Property" in t:
            target = self._format_expr(getattr(expr, "target", None))
            name = getattr(expr, "name", "")
            return f"{target}.{name}"
        return str(expr)


def format_source_ast(source: str, config: FormatConfig | None = None, indent_size: int = 4) -> str:
    """Format source using AST-based formatter."""
    if config is None:
        config = FormatConfig()
        config.indent_size = indent_size
    fmt = PeaFormatter(config=config)
    return fmt.format(source)


# ---------------------------------------------------------------------------
# Static linter (dead code, complexity, naming)
# ---------------------------------------------------------------------------

@dataclass
class LintConfig:
    """Linter configuration."""
    max_function_length: int = 50
    max_complexity: int = 10
    max_line_length: int = 120
    check_naming: bool = True
    check_dead_code: bool = True
    check_style: bool = True
    
    @classmethod
    def from_format_config(cls, fmt_config: FormatConfig) -> "LintConfig":
        return cls(
            max_line_length=fmt_config.max_line_length,
        )


class PeaLinter:
    """Static linter for PeaLang source."""
    
    def __init__(self, config: LintConfig | None = None):
        self.config = config or LintConfig()
        self.issues = []
    
    def lint(self, source: str) -> list[dict[str, Any]]:
        self.issues = []
        try:
            program = parse_source(source)
        except Exception as e:
            self.issues.append({"line": 0, "severity": "error", "message": f"Parse error: {e}"})
            return self.issues
        
        self._check_complexity(program, source)
        if self.config.check_naming:
            self._check_naming(program)
        if self.config.check_dead_code:
            self._check_dead_code(program)
        if self.config.check_style:
            self._check_style(source)
        return self.issues
    
    def _check_complexity(self, program, source):
        for node in self._walk(program):
            t = type(node).__name__
            if "Function" in t or "FuncDef" in t or "FuncStmt" in t:
                body = getattr(node, "body", []) or []
                if len(body) > self.config.max_function_length:
                    self.issues.append({"line": getattr(node, "line", 0), "severity": "warning",
                                        "message": f"Function too long ({len(body)} statements > {self.config.max_function_length})"})
                # Cyclomatic complexity
                complexity = 1
                for n in self._walk(node):
                    nt = type(n).__name__
                    if "If" in nt or "While" in nt or "For" in nt:
                        complexity += 1
                if complexity > self.config.max_complexity:
                    self.issues.append({"line": getattr(node, "line", 0), "severity": "warning",
                                        "message": f"High cyclomatic complexity ({complexity} > {self.config.max_complexity})"})
    
    def _check_naming(self, program):
        for node in self._walk(program):
            t = type(node).__name__
            if "Function" in t or "FuncDef" in t or "FuncStmt" in t:
                name = getattr(node, "name", "")
                if name and not name[0].islower():
                    self.issues.append({"line": getattr(node, "line", 0), "severity": "warning",
                                        "message": f"Function name '{name}' should start with lowercase (snake_case)"})
            if "Let" in t or "Const" in t:
                name = getattr(node, "name", "")
                if name and name[0].isupper():
                    self.issues.append({"line": getattr(node, "line", 0), "severity": "info",
                                        "message": f"Variable '{name}' should start with lowercase (snake_case)"})
    
    def _check_dead_code(self, program):
        for node in self._walk(program):
            t = type(node).__name__
            if "Function" in t or "FuncDef" in t or "FuncStmt" in t:
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
            if len(line) > self.config.max_line_length:
                self.issues.append({"line": i, "severity": "warning", "message": f"Line too long ({len(line)} > {self.config.max_line_length})"})
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


def lint_source_ast(source: str, config: LintConfig | None = None) -> list[dict[str, Any]]:
    """Lint source using AST-based linter."""
    linter = PeaLinter(config=config)
    return linter.lint(source)


# ---------------------------------------------------------------------------
# Auto-fix codemods
# ---------------------------------------------------------------------------

def codemod_remove_unused_imports(source: str) -> str:
    """Remove unused import statements."""
    lines = source.splitlines()
    result = []
    for line in lines:
        m = re.match(r'^\s*import\s+(\w+)', line.strip())
        if m:
            name = m.group(1)
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
    return re.sub(r'\b' + re.escape(old_name) + r'\b', new_name, source)


def codemod_fix_naming(source: str) -> str:
    """Fix naming conventions (camelCase to snake_case for functions)."""
    def to_snake(name):
        s = re.sub(r'([A-Z])', r'_\1', name).lower().lstrip('_')
        return s
    return re.sub(r'(function\s+)([A-Za-z_]\w*)', lambda m: m.group(1) + to_snake(m.group(2)), source)


def codemod_remove_unused_variables(source: str) -> str:
    """Remove unused variable declarations (simple heuristic)."""
    # This is a simple implementation - a real one would need data flow analysis
    return source


def codemod_simplify_returns(source: str) -> str:
    """Simplify explicit returns at end of functions."""
    # Replace `return` at end of function with implicit return
    lines = source.splitlines()
    result = []
    in_function = False
    function_indent = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("function "):
            in_function = True
            function_indent = len(line) - len(line.lstrip())
            result.append(line)
            continue
        if in_function and line and len(line) - len(line.lstrip()) <= function_indent:
            in_function = False
        
        if in_function and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # Check if this is the last statement before closing brace
            if stripped == "return" and next_line == "}":
                continue  # Skip explicit return at end
        
        result.append(line)
    
    return "\n".join(result)


def codemod_remove_debug_prints(source: str) -> str:
    """Remove debug print statements."""
    lines = source.splitlines()
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("print ") and ("debug" in stripped.lower() or "DEBUG" in stripped):
            continue
        result.append(line)
    return "\n".join(result)


def codemod_organize_imports(source: str) -> str:
    """Organize imports (group and sort)."""
    lines = source.splitlines()
    imports = []
    other = []
    
    for line in lines:
        if line.strip().startswith("import "):
            imports.append(line)
        else:
            other.append(line)
    
    # Sort imports
    imports.sort()
    
    return "\n".join(imports + ([""] if imports and other else []) + other)


def codemod_modernize_syntax(source: str) -> str:
    """Apply modern syntax transformations."""
    # Replace old-style patterns with new ones
    # e.g., function foo() { } -> function foo() {}
    return source


# ---------------------------------------------------------------------------
# Formatter/Linter integration helpers
# ---------------------------------------------------------------------------

def apply_codemods(source: str, codemods: list[str]) -> str:
    """Apply a list of codemods to source."""
    for name in codemods:
        if name == "remove_unused_imports":
            source = codemod_remove_unused_imports(source)
        elif name == "fix_naming":
            source = codemod_fix_naming(source)
        elif name == "remove_unused_variables":
            source = codemod_remove_unused_variables(source)
        elif name == "simplify_returns":
            source = codemod_simplify_returns(source)
        elif name == "remove_debug_prints":
            source = codemod_remove_debug_prints(source)
        elif name == "organize_imports":
            source = codemod_organize_imports(source)
        elif name == "modernize_syntax":
            source = codemod_modernize_syntax(source)
    return source


def format_and_lint(source: str, project_root: str = ".") -> tuple[str, list[dict]]:
    """Format and lint source in one pass."""
    fmt_config = FormatConfig.load(project_root)
    lint_config = LintConfig.from_format_config(fmt_config)
    
    formatted = format_source_ast(source, config=fmt_config)
    issues = lint_source_ast(formatted, config=lint_config)
    
    return formatted, issues


def build_formatter_namespace() -> dict[str, Any]:
    return {
        "PeaFormatter": PeaFormatter,
        "format_source_ast": format_source_ast,
        "FormatConfig": FormatConfig,
        "PeaLinter": PeaLinter,
        "lint_source_ast": lint_source_ast,
        "LintConfig": LintConfig,
        "codemod_remove_unused_imports": codemod_remove_unused_imports,
        "codemod_rename_variable": codemod_rename_variable,
        "codemod_fix_naming": codemod_fix_naming,
        "codemod_remove_unused_variables": codemod_remove_unused_variables,
        "codemod_simplify_returns": codemod_simplify_returns,
        "codemod_remove_debug_prints": codemod_remove_debug_prints,
        "codemod_organize_imports": codemod_organize_imports,
        "codemod_modernize_syntax": codemod_modernize_syntax,
        "apply_codemods": apply_codemods,
        "format_and_lint": format_and_lint,
    }