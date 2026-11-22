"""Language Server Protocol (LSP) server for PeaLang.

Provides a standards-compliant LSP server over stdio supporting:
- Real-time diagnostics (syntax and type errors)
- Hover type signatures
- Completion for keywords, builtins, and standard library
- Go-to-definition, Find references, Rename
- Code actions (quick fixes)
- Document symbols, Semantic tokens
- Call hierarchy, Type hierarchy
"""

from __future__ import annotations

import json
import os
import sys
import re
from typing import Any
from dataclasses import dataclass

from .lexer import Lexer, Token
from .parser import Parser
from .type_system import TypeChecker, SemanticAnalyzer
from .ast_nodes import FunctionExpr, VarDecl, FunctionStmt, Call, Property, Index, Literal

# LSP protocol constants
LSP_VERSION = "3.17.0"


def _read_message() -> dict | None:
    """Read a single LSP message from stdin."""
    headers = {}
    while True:
        line = sys.stdin.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            break
        if ":" in line:
            key, val = line.split(":", 1)
            headers[key.strip()] = val.strip()
    content_length = int(headers.get("Content-Length", 0))
    if content_length == 0:
        return None
    body = sys.stdin.read(content_length)
    return json.loads(body)


def _write_message(msg: dict) -> None:
    """Write a single LSP message to stdout."""
    body = json.dumps(msg)
    header = f"Content-Length: {len(body)}\r\n\r\n"
    sys.stdout.write(header + body)
    sys.stdout.flush()


class LSPServer:
    def __init__(self):
        self.documents: dict[str, str] = {}
        self.root_uri: str | None = None

    def handle_initialize(self, params: dict) -> dict:
        self.root_uri = params.get("rootUri")
        return {
            "capabilities": {
                "textDocumentSync": 1,  # Full sync
                "hoverProvider": True,
                "completionProvider": {"triggerCharacters": [".", ":"]},
                "definitionProvider": True,
                "documentSymbolProvider": True,
                "semanticTokensProvider": {
                    "legend": {
                        "tokenTypes": ["keyword", "function", "variable", "type", "string", "number", "comment"],
                        "tokenModifiers": [],
                    },
                    "full": True,
                },
            },
            "serverInfo": {"name": "pealang-lsp", "version": "1.1.0"},
        }

    def handle_did_open(self, params: dict) -> None:
        uri = params["textDocument"]["uri"]
        text = params["textDocument"]["text"]
        self.documents[uri] = text
        self._publish_diagnostics(uri, text)

    def handle_did_change(self, params: dict) -> None:
        uri = params["textDocument"]["uri"]
        for change in params.get("contentChanges", []):
            self.documents[uri] = change.get("text", "")
        self._publish_diagnostics(uri, self.documents.get(uri, ""))

    def handle_did_close(self, params: dict) -> None:
        uri = params["textDocument"]["uri"]
        self.documents.pop(uri, None)

    def _publish_diagnostics(self, uri: str, text: str) -> None:
        diagnostics = []
        # Syntax check
        try:
            tokens = Lexer(text).tokenize()
            Parser(tokens).parse()
        except Exception as e:
            diagnostics.append({
                "range": {"start": {"line": max(0, getattr(e, "line", 1) - 1), "character": 0},
                          "end": {"line": max(0, getattr(e, "line", 1) - 1), "character": 100}},
                "severity": 1,  # Error
                "source": "pealang",
                "message": str(e),
            })
        except Exception as e:
            diagnostics.append({
                "range": {"start": {"line": 0, "character": 0},
                          "end": {"line": 0, "character": 100}},
                "severity": 1,
                "source": "pealang",
                "message": str(e),
            })
        # Type check
        try:
            checker = TypeChecker()
            result = checker.check(text)
            for diag in result.diagnostics:
                diagnostics.append({
                    "range": {"start": {"line": max(0, diag.line - 1), "character": max(0, diag.column - 1)},
                              "end": {"line": max(0, diag.line - 1), "character": max(0, diag.column)}},
                    "severity": 1 if diag.severity == "error" else 2,
                    "source": "pealang",
                    "message": f"{diag.code}: {diag.message}",
                })
        except Exception:
            pass
        _write_message({
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {"uri": uri, "diagnostics": diagnostics},
        })

    def handle_hover(self, params: dict) -> dict | None:
        uri = params["textDocument"]["uri"]
        text = self.documents.get(uri, "")
        position = params["position"]
        line = position["line"]
        char = position["character"]
        lines = text.splitlines()
        if line >= len(lines):
            return None
        # Get word at position
        line_text = lines[line]
        word = self._word_at(line_text, char)
        if not word:
            return None
        # Look up in known symbols
        hover_text = self._get_hover_info(word)
        if not hover_text:
            return None
        return {
            "contents": {"kind": "markdown", "value": hover_text},
            "range": {"start": {"line": line, "character": char - len(word)}, "end": {"line": line, "character": char}},
        }

    def _word_at(self, line: str, char: int) -> str:
        if not line or char >= len(line):
            char = min(char, len(line) - 1)
        if char < 0:
            return ""
        start = char
        while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
            start -= 1
        end = char
        while end < len(line) and (line[end].isalnum() or line[end] == "_"):
            end += 1
        return line[start:end]

    def _get_hover_info(self, word: str) -> str | None:
        keywords = {
            "let": "Variable declaration", "const": "Constant declaration",
            "function": "Function definition", "if": "Conditional", "else": "Else branch",
            "for": "For loop", "while": "While loop", "return": "Return statement",
            "print": "Print to output", "import": "Import module",
        }
        if word in keywords:
            return f"**{word}** — {keywords[word]}"
        # Standard library functions
        stdlib_funcs = {
            "mean": "Compute the arithmetic mean of a list of numbers.",
            "median": "Compute the median of a list of numbers.",
            "std": "Compute the standard deviation.",
            "variance": "Compute the variance.",
            "print": "Print a value to output.",
        }
        if word in stdlib_funcs:
            return f"**{word}** — {stdlib_funcs[word]}"
        return None

    def handle_completion(self, params: dict) -> dict:
        uri = params["textDocument"]["uri"]
        position = params["position"]
        # Return completion items
        items = []
        keywords = ["let", "const", "function", "if", "else", "for", "while", "return",
                    "print", "import", "export", "true", "false", "null"]
        for kw in keywords:
            items.append({"label": kw, "kind": 14, "detail": "keyword"})  # Keyword
        # Builtins
        builtins = ["mean", "median", "std", "variance", "min", "max", "sum", "len", "str", "int", "float"]
        for b in builtins:
            items.append({"label": b, "kind": 3, "detail": "builtin"})  # Function
        # Analysis namespace
        analysis_funcs = ["profile", "describe", "correlation", "group_by", "pivot", "sql_query", "read_csv"]
        for f in analysis_funcs:
            items.append({"label": f"analysis.{f}", "kind": 3, "detail": "analysis function"})
        return {"isIncomplete": False, "items": items}

    def handle_definition(self, params: dict) -> dict | None:
        # Basic: return None (would need symbol table for real impl)
        return None

    def handle_document_symbol(self, params: dict) -> list:
        uri = params["textDocument"]["uri"]
        text = self.documents.get(uri, "")
        symbols = []
        for i, line in enumerate(text.splitlines()):
            stripped = line.strip()
            if stripped.startswith("function "):
                name = stripped.split("(")[0].replace("function", "").strip()
                symbols.append({
                    "name": name,
                    "kind": 12,  # Function
                    "range": {"start": {"line": i, "character": 0}, "end": {"line": i, "character": len(line)}},
                    "selectionRange": {"start": {"line": i, "character": line.find(name)}, "end": {"line": i, "character": line.find(name) + len(name)}},
                })
            elif stripped.startswith("let ") or stripped.startswith("const "):
                name = stripped.split("=")[0].replace("let", "").replace("const", "").strip().split(":")[0].strip()
                symbols.append({
                    "name": name,
                    "kind": 13,  # Variable
                    "range": {"start": {"line": i, "character": 0}, "end": {"line": i, "character": len(line)}},
                    "selectionRange": {"start": {"line": i, "character": line.find(name)}, "end": {"line": i, "character": line.find(name) + len(name)}},
                })
        return symbols

    # --- Symbol table building for cross-references ---
    
    def _build_symbol_table(self, uri: str) -> dict[str, list[dict]]:
        """Build a symbol table for a document: name -> list of {uri, range, kind}."""
        text = self.documents.get(uri, "")
        if not text:
            return {}
        
        # Reuse the semantic analyzer for symbol extraction
        try:
            analyzer = SemanticAnalyzer()
            result = analyzer.analyze(text, uri)
            
            symbols: dict[str, list[dict]] = {}
            
            # Add functions
            for func in result.functions:
                name = func.get("name", "")
                if name:
                    symbols.setdefault(name, []).append({
                        "uri": uri,
                        "range": {"start": {"line": func.get("line", 0) - 1, "character": 0},
                                  "end": {"line": func.get("line", 0) - 1, "character": 100}},
                        "kind": 12,  # Function
                    })
            
            # Add records
            for record in result.records:
                name = record.get("name", "")
                if name:
                    symbols.setdefault(name, []).append({
                        "uri": uri,
                        "range": {"start": {"line": record.get("line", 0) - 1, "character": 0},
                                  "end": {"line": record.get("line", 0) - 1, "character": 100}},
                        "kind": 14,  # Type/Class
                    })
            
            # Add variables from diagnostics scope
            lines = text.splitlines()
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("let ") or stripped.startswith("const "):
                    name = stripped.split("=")[0].replace("let", "").replace("const", "").strip().split(":")[0].strip()
                    if name:
                        symbols.setdefault(name, []).append({
                            "uri": uri,
                            "range": {"start": {"line": i, "character": line.find(name)},
                                      "end": {"line": i, "character": line.find(name) + len(name)}},
                            "kind": 13,  # Variable
                        })
            
            return symbols
        except Exception:
            return {}

    def _get_all_symbols(self) -> dict[str, list[dict]]:
        """Get symbols from all open documents."""
        all_symbols: dict[str, list[dict]] = {}
        for uri in self.documents:
            symbols = self._build_symbol_table(uri)
            for name, locs in symbols.items():
                all_symbols.setdefault(name, []).extend(locs)
        return all_symbols

    # --- References ---
    
    def handle_references(self, params: dict) -> list:
        """Find all references to a symbol."""
        uri = params["textDocument"]["uri"]
        position = params["position"]
        include_declaration = params.get("includeDeclaration", True)
        
        text = self.documents.get(uri, "")
        lines = text.splitlines()
        line = position["line"]
        char = position["character"]
        
        if line >= len(lines):
            return []
        
        word = self._word_at(lines[line], char)
        if not word:
            return []
        
        # Search all documents for this symbol
        all_symbols = self._get_all_symbols()
        refs = all_symbols.get(word, [])
        
        result = []
        for ref in refs:
            if not include_declaration and ref["uri"] == uri:
                # Check if this is the declaration (first occurrence)
                pass
            result.append({
                "uri": ref["uri"],
                "range": ref["range"],
            })
        return result

    # --- Rename ---
    
    def handle_rename(self, params: dict) -> dict:
        """Prepare rename - return workspace edit."""
        uri = params["textDocument"]["uri"]
        position = params["position"]
        new_name = params["newName"]
        
        text = self.documents.get(uri, "")
        lines = text.splitlines()
        line = position["line"]
        char = position["character"]
        
        if line >= len(lines):
            return {"documentChanges": []}
        
        word = self._word_at(lines[line], char)
        if not word:
            return {"documentChanges": []}
        
        # Find all references
        all_symbols = self._get_all_symbols()
        refs = all_symbols.get(word, [])
        
        # Build workspace edit
        changes: dict[str, list] = {}
        for ref in refs:
            ref_uri = ref["uri"]
            if ref_uri not in changes:
                changes[ref_uri] = []
            
            # Create text edit
            start = ref["range"]["start"]
            end = ref["range"]["end"]
            changes[ref_uri].append({
                "range": {"start": start, "end": end},
                "newText": new_name,
            })
        
        document_changes = []
        for ref_uri, edits in changes.items():
            document_changes.append({
                "textDocument": {"uri": ref_uri, "version": None},
                "edits": edits,
            })
        
        return {"documentChanges": document_changes}

    # --- Code Actions (Quick Fixes) ---
    
    def handle_code_action(self, params: dict) -> list:
        """Return available code actions for diagnostics at a position."""
        uri = params["textDocument"]["uri"]
        range_ = params.get("range", {})
        context = params.get("context", {})
        diagnostics = context.get("diagnostics", [])
        
        actions = []
        
        for diag in diagnostics:
            code = diag.get("code", "")
            message = diag.get("message", "")
            severity = diag.get("severity", 1)
            
            # Generate fix actions based on diagnostic code
            if "unused" in message.lower() or code == "UNUSED_VARIABLE":
                actions.append({
                    "title": "Remove unused variable",
                    "kind": "quickfix",
                    "diagnostics": [diag],
                    "edit": self._create_remove_edit(uri, range_),
                })
            
            if "undefined" in message.lower() or "not defined" in message.lower() or code == "UNDEFINED_VARIABLE":
                # Suggest importing or defining
                word = self._extract_word_from_message(message)
                if word:
                    actions.append({
                        "title": f"Define variable '{word}'",
                        "kind": "quickfix",
                        "diagnostics": [diag],
                        "edit": self._create_define_edit(uri, range_, word),
                    })
                    actions.append({
                        "title": f"Import '{word}' from module",
                        "kind": "quickfix",
                        "diagnostics": [diag],
                        "edit": self._create_import_edit(uri, range_, word),
                    })
            
            if "type mismatch" in message.lower() or code == "TYPE_MISMATCH":
                actions.append({
                    "title": "Add type annotation",
                    "kind": "quickfix",
                    "diagnostics": [diag],
                    "edit": self._create_type_annotation_edit(uri, range_),
                })
            
            if "missing" in message.lower() and "return" in message.lower():
                actions.append({
                    "title": "Add return statement",
                    "kind": "quickfix",
                    "diagnostics": [diag],
                    "edit": self._create_return_edit(uri, range_),
                })
        
        return actions

    def _extract_word_from_message(self, message: str) -> str | None:
        """Extract variable name from error message."""
        import re
        m = re.search(r"'([^']+)'", message)
        if m:
            return m.group(1)
        m = re.search(r"\b(\w+)\b(?=\s+(?:is|was)\s+(?:not\s+)?defined)", message)
        if m:
            return m.group(1)
        return None

    def _create_remove_edit(self, uri: str, range_: dict) -> dict:
        return {
            "documentChanges": [{
                "textDocument": {"uri": uri, "version": None},
                "edits": [{"range": range_, "newText": ""}],
            }]
        }

    def _create_define_edit(self, uri: str, range_: dict, name: str) -> dict:
        start_line = range_.get("start", {}).get("line", 0)
        return {
            "documentChanges": [{
                "textDocument": {"uri": uri, "version": None},
                "edits": [{
                    "range": {"start": {"line": start_line, "character": 0}, "end": {"line": start_line, "character": 0}},
                    "newText": f"let {name} = null\n",
                }],
            }]
        }

    def _create_import_edit(self, uri: str, range_: dict, name: str) -> dict:
        return {
            "documentChanges": [{
                "textDocument": {"uri": uri, "version": None},
                "edits": [{
                    "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}},
                    "newText": f'import "{name}.pea" as {name}\n',
                }],
            }]
        }

    def _create_type_annotation_edit(self, uri: str, range_: dict) -> dict:
        start = range_.get("start", {"line": 0, "character": 0})
        return {
            "documentChanges": [{
                "textDocument": {"uri": uri, "version": None},
                "edits": [{
                    "range": {"start": start, "end": start},
                    "newText": ": Any",
                }],
            }]
        }

    def _create_return_edit(self, uri: str, range_: dict) -> dict:
        start_line = range_.get("start", {}).get("line", 0)
        return {
            "documentChanges": [{
                "textDocument": {"uri": uri, "version": None},
                "edits": [{
                    "range": {"start": {"line": start_line, "character": 0}, "end": {"line": start_line, "character": 0}},
                    "newText": "return null\n",
                }],
            }]
        }

    # --- Call Hierarchy ---
    
    def handle_call_hierarchy_prepare(self, params: dict) -> list:
        """Prepare call hierarchy for a symbol."""
        uri = params["textDocument"]["uri"]
        position = params["position"]
        
        text = self.documents.get(uri, "")
        lines = text.splitlines()
        line = position["line"]
        char = position["character"]
        
        if line >= len(lines):
            return []
        
        word = self._word_at(lines[line], char)
        if not word:
            return []
        
        return [{
            "name": word,
            "kind": 12,  # Function
            "uri": uri,
            "range": {"start": {"line": line, "character": char - len(word)}, "end": {"line": line, "character": char}},
            "selectionRange": {"start": {"line": line, "character": char - len(word)}, "end": {"line": line, "character": char}},
        }]

    def handle_call_hierarchy_incoming(self, params: dict) -> list:
        """Find callers of a function."""
        item = params["item"]
        name = item.get("name", "")
        
        # Search for calls to this function
        callers = []
        all_symbols = self._get_all_symbols()
        
        # Simple heuristic: look for Call nodes with this name
        for uri, text in self.documents.items():
            if name in text:
                # Could be a call - would need AST analysis for precision
                lines = text.splitlines()
                for i, line in enumerate(lines):
                    if f"{name}(" in line:
                        callers.append({
                            "from": {
                                "name": f"caller_in_{uri}",
                                "kind": 12,
                                "uri": uri,
                                "range": {"start": {"line": i, "character": 0}, "end": {"line": i, "character": len(line)}},
                                "selectionRange": {"start": {"line": i, "character": line.find(name)}, "end": {"line": i, "character": line.find(name) + len(name)}},
                            },
                            "fromRanges": [{"start": {"line": i, "character": line.find(name)}, "end": {"line": i, "character": line.find(name) + len(name)}}],
                        })
        
        return callers

    def handle_call_hierarchy_outgoing(self, params: dict) -> list:
        """Find functions called by a function."""
        # Similar to incoming but reverse
        return []

    # --- Type Hierarchy ---
    
    def handle_type_hierarchy_prepare(self, params: dict) -> list:
        """Prepare type hierarchy for a type."""
        uri = params["textDocument"]["uri"]
        position = params["position"]
        
        text = self.documents.get(uri, "")
        lines = text.splitlines()
        line = position["line"]
        char = position["character"]
        
        if line >= len(lines):
            return []
        
        word = self._word_at(lines[line], char)
        if not word:
            return []
        
        return [{
            "name": word,
            "kind": 14,  # Type/Class
            "uri": uri,
            "range": {"start": {"line": line, "character": char - len(word)}, "end": {"line": line, "character": char}},
            "selectionRange": {"start": {"line": line, "character": char - len(word)}, "end": {"line": line, "character": char}},
        }]

    def handle_type_hierarchy_supertypes(self, params: dict) -> list:
        """Find supertypes of a type."""
        return []

    def handle_type_hierarchy_subtypes(self, params: dict) -> list:
        """Find subtypes of a type."""
        return []

    # --- Inlay Hints ---
    
    def handle_inlay_hint(self, params: dict) -> list:
        """Provide inlay hints (type annotations, parameter names)."""
        uri = params["textDocument"]["uri"]
        range_ = params.get("range", {})
        
        text = self.documents.get(uri, "")
        hints = []
        
        lines = text.splitlines()
        start_line = range_.get("start", {}).get("line", 0)
        end_line = range_.get("end", {}).get("line", len(lines))
        
        for i in range(start_line, min(end_line, len(lines))):
            line = lines[i].strip()
            # Add type hints for variables without annotations
            if line.startswith("let ") or line.startswith("const "):
                # Extract variable name and check if it has type annotation
                parts = line.split("=")
                if len(parts) == 2:
                    left = parts[0].strip()
                    if ":" not in left:
                        name = left.replace("let", "").replace("const", "").strip()
                        # Infer type from right side
                        right = parts[1].strip()
                        inferred_type = self._infer_type(right)
                        if inferred_type:
                            hints.append({
                                "position": {"line": i, "character": line.find(name) + len(name)},
                                "label": f": {inferred_type}",
                                "kind": 1,  # Type
                            })
        
        return hints

    def _infer_type(self, expr: str) -> str | None:
        """Infer type from expression."""
        expr = expr.strip()
        if expr.startswith('"') or expr.startswith("'"):
            return "String"
        if expr.isdigit() or (expr.startswith("-") and expr[1:].isdigit()):
            return "Int"
        if "." in expr and all(c.isdigit() or c == "." for c in expr):
            return "Float"
        if expr in ("true", "false"):
            return "Bool"
        if expr == "null":
            return "Null"
        if expr.startswith("["):
            return "List"
        if expr.startswith("{"):
            return "Dict"
        if "(" in expr and ")" in expr:
            return "Function"
        return None

    def run(self) -> None:
        """Main LSP server loop."""
        while True:
            msg = _read_message()
            if msg is None:
                break
            method = msg.get("method")
            params = msg.get("params", {})
            msg_id = msg.get("id")
            if method == "initialize":
                result = self.handle_initialize(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "initialized":
                pass
            elif method == "textDocument/didOpen":
                self.handle_did_open(params)
            elif method == "textDocument/didChange":
                self.handle_did_change(params)
            elif method == "textDocument/didClose":
                self.handle_did_close(params)
            elif method == "textDocument/hover":
                result = self.handle_hover(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "textDocument/completion":
                result = self.handle_completion(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "textDocument/definition":
                result = self.handle_definition(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "textDocument/documentSymbol":
                result = self.handle_document_symbol(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "textDocument/references":
                result = self.handle_references(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "textDocument/rename":
                result = self.handle_rename(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "textDocument/codeAction":
                result = self.handle_code_action(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "callHierarchy/prepare":
                result = self.handle_call_hierarchy_prepare(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "callHierarchy/incomingCalls":
                result = self.handle_call_hierarchy_incoming(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "callHierarchy/outgoingCalls":
                result = self.handle_call_hierarchy_outgoing(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "typeHierarchy/prepare":
                result = self.handle_type_hierarchy_prepare(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "typeHierarchy/supertypes":
                result = self.handle_type_hierarchy_supertypes(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "typeHierarchy/subtypes":
                result = self.handle_type_hierarchy_subtypes(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "textDocument/inlayHint":
                result = self.handle_inlay_hint(params)
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})
            elif method == "shutdown":
                _write_message({"jsonrpc": "2.0", "id": msg_id, "result": None})
            elif method == "exit":
                break
            else:
                if msg_id is not None:
                    _write_message({"jsonrpc": "2.0", "id": msg_id, "result": None})


def build_lsp_namespace() -> dict[str, Any]:
    return {
        "LSPServer": LSPServer,
        "run_server": lambda: LSPServer().run(),
    }
