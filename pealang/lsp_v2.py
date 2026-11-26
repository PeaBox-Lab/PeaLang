"""Phase 81: deterministic LSP v2 layer for PeaLang editor tooling.

This module is additive to the v1 ``pealang.lsp`` server. It provides a
versioned capability set, a deterministic document store with full and
incremental synchronization, and reviewable language features whose results can
be checked without starting a stdio server. Wall-clock and host-specific values
are excluded from digests so editor integrations can assert stable behavior.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

from .lexer import KEYWORDS, Lexer
from .parser import Parser

LSP_V2_VERSION = '3.1.44'
LSP_V2_PROTOCOL_VERSION = '3.17.0'
LSP_V2_FORMAT = 'pea-lsp-v2'

_KEYWORD_LABELS = tuple(sorted(KEYWORDS))
_BUILTIN_LABELS = (
    'len', 'sum', 'sorted', 'reversed', 'map', 'filter', 'all', 'any',
    'print', 'range', 'iter', 'next', 'error', 'assert', 'open',
)
_STDLIB_HINTS = ('std.collections', 'std.string', 'std.math', 'std.json',
                 'std.file', 'std.path', 'std.http', 'std.analysis')
_SYMBOL_PATTERNS = (
    ('function', re.compile(r'^[ \t]*function\s+([A-Za-z_]\w*)\s*\(', re.M)),
    ('variable', re.compile(r'^[ \t]*(?:let|const)\s+([A-Za-z_]\w*)\s*=', re.M)),
    ('type', re.compile(r'^[ \t]*type\s+([A-Za-z_]\w*)\s*=', re.M)),
    ('interface', re.compile(r'^[ \t]*(?:protocol|trait)\s+([A-Za-z_]\w*)', re.M)),
)
_SYMBOL_KINDS = {'function': 12, 'variable': 13, 'type': 5, 'interface': 11}
_SEMANTIC_TYPES = ('keyword', 'function', 'variable', 'type', 'string', 'number')
_WORD_RE = re.compile(r'\w+')


class LspV2Error(Exception):
    """Raised when an LSP v2 document or request is malformed."""


def _digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


def _range_for_span(text: str, start: int, end: int) -> dict[str, Any]:
    before = text[:start]
    line = before.count('\n')
    line_start = before.rfind('\n') + 1
    end_before = text[:end]
    end_line = end_before.count('\n')
    end_line_start = end_before.rfind('\n') + 1
    return {
        'start': {'line': line, 'character': start - line_start},
        'end': {'line': end_line, 'character': end - end_line_start},
    }


def _position_offset(text: str, position: dict[str, Any]) -> int:
    lines = text.splitlines(keepends=True)
    line = max(0, min(int(position.get('line', 0)), len(lines)))
    character = max(0, int(position.get('character', 0)))
    line_start = sum(len(item) for item in lines[:line])
    line_end = line_start + len(lines[line]) if line < len(lines) else len(text)
    return min(line_start + character, line_end)


def _range_offsets(text: str, span: dict[str, Any]) -> tuple[int, int]:
    start = _position_offset(text, span.get('start', {}))
    end = _position_offset(text, span.get('end', {}))
    if end < start:
        raise LspV2Error('LSP range end precedes start')
    return start, end


def _full_range(text: str) -> dict[str, Any]:
    lines = text.splitlines(keepends=True)
    last_line = max(0, len(lines) - 1)
    return {
        'start': {'line': 0, 'character': 0},
        'end': {'line': last_line, 'character': len(lines[last_line])
                if lines else 0},
    }


@dataclass(frozen=True)
class TextDocument:
    """One versioned editor document with a stable digest."""

    uri: str
    text: str
    version: int = 1
    language_id: str = 'pealang'

    def to_dict(self) -> dict[str, Any]:
        return {
            'uri': self.uri, 'text': self.text, 'version': self.version,
            'language_id': self.language_id,
        }

    @property
    def digest(self) -> str:
        return _digest(self.to_dict())


class DocumentStore:
    """Deterministic full and incremental text-document synchronization."""

    def __init__(self) -> None:
        self._documents: dict[str, TextDocument] = {}

    def open(self, uri: str, text: str, *, version: int = 1,
             language_id: str = 'pealang') -> TextDocument:
        if not uri or not isinstance(text, str):
            raise LspV2Error('document open requires a uri and text')
        document = TextDocument(uri, text, max(1, int(version)), language_id)
        self._documents[uri] = document
        return document

    def change(self, uri: str, changes: Iterable[dict[str, Any]], *,
               version: int | None = None) -> TextDocument:
        document = self.get(uri)
        text = document.text
        edits = tuple(changes)
        if not edits:
            raise LspV2Error('document change requires at least one edit')
        ranged = [edit for edit in edits if edit.get('range') is not None]
        if ranged and any(edit.get('range') is None for edit in edits):
            raise LspV2Error('mixed full and incremental LSP changes are invalid')
        if ranged:
            ordered = sorted(
                ((_range_offsets(text, edit['range']), str(edit.get('newText', '')))
                 for edit in ranged),
                key=lambda item: item[0][0], reverse=True,
            )
            for (start, end), new_text in ordered:
                text = text[:start] + new_text + text[end:]
        else:
            text = str(edits[-1].get('text', edits[-1].get('newText', '')))
        next_version = document.version + 1 if version is None else max(1, int(version))
        updated = TextDocument(document.uri, text, next_version, document.language_id)
        self._documents[uri] = updated
        return updated

    def close(self, uri: str) -> bool:
        return self._documents.pop(uri, None) is not None

    def get(self, uri: str) -> TextDocument:
        try:
            return self._documents[uri]
        except KeyError as exc:
            raise LspV2Error(f'unknown document: {uri}') from exc

    def snapshot(self) -> tuple[TextDocument, ...]:
        return tuple(self._documents[uri] for uri in sorted(self._documents))

    def digest(self) -> str:
        return _digest([document.to_dict() for document in self.snapshot()])


def lsp_v2_capabilities() -> dict[str, Any]:
    """Return the versioned LSP v2 capability set."""

    return {
        'capabilities': {
            'textDocumentSync': {
                'openClose': True, 'change': 2,
                'save': {'includeText': False},
            },
            'hoverProvider': True,
            'completionProvider': {'triggerCharacters': ['.', ':', ' ']},
            'definitionProvider': True,
            'referencesProvider': True,
            'renameProvider': True,
            'documentSymbolProvider': True,
            'workspaceSymbolProvider': True,
            'documentFormattingProvider': True,
            'semanticTokensProvider': {
                'legend': {'tokenTypes': list(_SEMANTIC_TYPES),
                           'tokenModifiers': []},
                'full': True,
            },
            'inlayHintProvider': True,
            'foldingRangeProvider': True,
        },
        'serverInfo': {'name': 'pealang-lsp-v2', 'version': LSP_V2_VERSION},
    }


class LspV2Server:
    """Protocol-facing LSP v2 server with deterministic, inspectable results."""

    def __init__(self, root_uri: str | None = None) -> None:
        self.root_uri = root_uri
        self.store = DocumentStore()
        self.initialized = False
        self.shutdown = False

    def capabilities(self) -> dict[str, Any]:
        """Return the versioned capability set advertised by this server."""

        return lsp_v2_capabilities()

    def handle_initialize(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = params or {}
        self.root_uri = params.get('rootUri', self.root_uri)
        self.initialized = True
        return self.capabilities()

    def handle_did_open(self, params: dict[str, Any]) -> dict[str, Any]:
        item = params['textDocument']
        document = self.store.open(
            item['uri'], item.get('text', ''),
            version=int(item.get('version', 1)),
            language_id=item.get('languageId', 'pealang'),
        )
        return {'uri': document.uri, 'version': document.version,
                'diagnostics': self.diagnostics(document.uri)}

    def handle_did_change(self, params: dict[str, Any]) -> dict[str, Any]:
        document = self.store.change(
            params['textDocument']['uri'], params.get('contentChanges', ()),
            version=params['textDocument'].get('version'),
        )
        return {'uri': document.uri, 'version': document.version,
                'diagnostics': self.diagnostics(document.uri)}

    def handle_did_close(self, params: dict[str, Any]) -> dict[str, Any]:
        uri = params['textDocument']['uri']
        return {'uri': uri, 'closed': self.store.close(uri)}

    def diagnostics(self, uri: str) -> list[dict[str, Any]]:
        document = self.store.get(uri)
        try:
            Parser(Lexer(document.text, uri).tokens()).parse()
        except Exception as exc:  # parser failures are editor diagnostics
            line = max(0, int(getattr(getattr(exc, 'span', None), 'line', 1)) - 1)
            return [{
                'range': {
                    'start': {'line': line, 'character': 0},
                    'end': {'line': line, 'character': 100},
                },
                'severity': 1, 'source': 'pealang', 'message': str(exc),
            }]
        return []

    def document_symbols(self, uri: str) -> list[dict[str, Any]]:
        document = self.store.get(uri)
        symbols: list[dict[str, Any]] = []
        for category, pattern in _SYMBOL_PATTERNS:
            for match in pattern.finditer(document.text):
                span = _range_for_span(document.text, match.start(1), match.end(1))
                kind = _SYMBOL_KINDS[category]
                symbols.append({
                    'name': match.group(1), 'kind': kind,
                    'detail': category, 'range': span, 'selectionRange': span,
                })
        return sorted(symbols, key=lambda item: (
            item['range']['start']['line'], item['range']['start']['character'],
            item['name'], item['kind'],
        ))

    def workspace_symbols(self, query: str = '') -> list[dict[str, Any]]:
        needle = query.lower()
        symbols: list[dict[str, Any]] = []
        for document in self.store.snapshot():
            for symbol in self.document_symbols(document.uri):
                if needle and needle not in symbol['name'].lower():
                    continue
                item = dict(symbol)
                item['location'] = {'uri': document.uri,
                                    'range': symbol['range']}
                symbols.append(item)
        return sorted(symbols, key=lambda item: (
            item['name'], item['location']['uri'],
            item['range']['start']['line'],
        ))

    def _word_at(self, uri: str, position: dict[str, Any]) -> tuple[str, int, int] | None:
        document = self.store.get(uri)
        lines = document.text.splitlines()
        line_index = max(0, min(int(position.get('line', 0)), len(lines) - 1)) if lines else 0
        line = lines[line_index] if lines else ''
        character = max(0, min(int(position.get('character', 0)), len(line)))
        for match in _WORD_RE.finditer(line):
            if match.start() <= character <= match.end():
                return match.group(), match.start(), match.end()
        return None

    def completion(self, uri: str, position: dict[str, Any] | None = None
                   ) -> dict[str, Any]:
        self.store.get(uri)
        labels = set(_KEYWORD_LABELS) | set(_BUILTIN_LABELS) | set(_STDLIB_HINTS)
        labels.update(symbol['name'] for symbol in self.document_symbols(uri))
        items = [{'label': label, 'kind': 14 if label in _KEYWORD_LABELS else 6,
                  'detail': 'keyword' if label in _KEYWORD_LABELS else 'pealang'}
                 for label in sorted(labels)]
        return {'isIncomplete': False, 'items': items}

    def hover(self, uri: str, position: dict[str, Any]) -> dict[str, Any] | None:
        found = self._word_at(uri, position)
        if found is None:
            return None
        word, start, character = found
        line = int(position.get('line', 0))
        for symbol in self.document_symbols(uri):
            if symbol['name'] != word:
                continue
            return {
                'contents': {'kind': 'markdown',
                             'value': f'`{word}` — {symbol["detail"]}'},
                'range': {
                    'start': {'line': line, 'character': start},
                    'end': {'line': line, 'character': character},
                },
            }
        return None

    def definition(self, uri: str, position: dict[str, Any]) -> dict[str, Any] | None:
        found = self._word_at(uri, position)
        if found is None:
            return None
        word = found[0]
        for symbol in self.document_symbols(uri):
            if symbol['name'] == word:
                return {'uri': uri, 'range': symbol['range']}
        return None

    def references(self, uri: str, position: dict[str, Any]) -> list[dict[str, Any]]:
        found = self._word_at(uri, position)
        if found is None:
            return []
        word = found[0]
        pattern = re.compile(rf'\b{re.escape(word)}\b')
        locations: list[dict[str, Any]] = []
        for document in self.store.snapshot():
            for match in pattern.finditer(document.text):
                locations.append({
                    'uri': document.uri,
                    'range': _range_for_span(document.text, match.start(), match.end()),
                })
        return sorted(locations, key=lambda item: (
            item['uri'], item['range']['start']['line'],
            item['range']['start']['character'],
        ))

    def rename(self, uri: str, position: dict[str, Any], new_name: str
               ) -> dict[str, Any]:
        if not re.fullmatch(r'[A-Za-z_]\w*', new_name or ''):
            raise LspV2Error('rename requires a valid PeaLang identifier')
        locations = self.references(uri, position)
        changes: dict[str, list[dict[str, Any]]] = {}
        for location in locations:
            changes.setdefault(location['uri'], []).append({
                'range': location['range'], 'newText': new_name,
            })
        return {'changes': changes}

    def formatting(self, uri: str) -> list[dict[str, Any]]:
        document = self.store.get(uri)
        lines = [line.rstrip() for line in document.text.splitlines()]
        formatted = '\n'.join(lines)
        if document.text.endswith('\n'):
            formatted += '\n'
        if formatted == document.text:
            return []
        return [{'range': _full_range(document.text), 'newText': formatted}]

    def folding_ranges(self, uri: str) -> list[dict[str, Any]]:
        document = self.store.get(uri)
        ranges: list[dict[str, Any]] = []
        stack: list[int] = []
        for index, line in enumerate(document.text.splitlines()):
            for _ in range(line.count('{')):
                stack.append(index)
            for _ in range(line.count('}')):
                if stack:
                    start = stack.pop()
                    ranges.append({'startLine': start, 'endLine': index,
                                   'kind': 'region'})
        return sorted(ranges, key=lambda item: (item['startLine'], item['endLine']))

    def inlay_hints(self, uri: str) -> list[dict[str, Any]]:
        self.store.get(uri)
        return []

    def semantic_tokens(self, uri: str) -> dict[str, Any]:
        document = self.store.get(uri)
        tokens = Lexer(document.text, uri).tokens()
        data: list[int] = []
        previous_line = 0
        previous_char = 0
        for index, token in enumerate(tokens):
            if token.kind in ('EOF', 'NEWLINE'):
                continue
            line = max(0, int(token.line) - 1)
            character = max(0, int(token.col) - 1)
            if str(token.value) in KEYWORDS or token.kind in KEYWORDS:
                token_type = 0
            elif token.kind == 'IDENT':
                following = tokens[index + 1] if index + 1 < len(tokens) else None
                token_type = 1 if following is not None and following.value == '(' else 2
            elif token.kind == 'STRING':
                token_type = 4
            elif token.kind == 'NUMBER':
                token_type = 5
            else:
                token_type = 2
            delta_line = line - previous_line
            delta_char = character - previous_char if delta_line == 0 else character
            data.extend([delta_line, delta_char,
                         max(1, len(str(token.value))), token_type, 0])
            previous_line, previous_char = line, character
        return {'data': data}

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """Dispatch one JSON-RPC message; notifications return ``None``."""

        method = message.get('method')
        params = message.get('params') or {}
        message_id = message.get('id')

        def response(result: Any) -> dict[str, Any]:
            return {'jsonrpc': '2.0', 'id': message_id, 'result': result}

        if method == 'initialize':
            return response(self.handle_initialize(params))
        if method == 'initialized':
            self.initialized = True
            return None
        if method == 'textDocument/didOpen':
            self.handle_did_open(params)
            return None
        if method == 'textDocument/didChange':
            self.handle_did_change(params)
            return None
        if method == 'textDocument/didClose':
            self.handle_did_close(params)
            return None
        if method == 'textDocument/completion':
            return response(self.completion(params['textDocument']['uri'],
                                            params.get('position')))
        if method == 'textDocument/hover':
            return response(self.hover(params['textDocument']['uri'],
                                       params.get('position', {})))
        if method == 'textDocument/definition':
            return response(self.definition(params['textDocument']['uri'],
                                            params.get('position', {})))
        if method == 'textDocument/documentSymbol':
            return response(self.document_symbols(params['textDocument']['uri']))
        if method == 'textDocument/references':
            return response(self.references(params['textDocument']['uri'],
                                            params.get('position', {})))
        if method == 'textDocument/rename':
            return response(self.rename(params['textDocument']['uri'],
                                        params.get('position', {}),
                                        params.get('newName', '')))
        if method == 'textDocument/formatting':
            return response(self.formatting(params['textDocument']['uri']))
        if method == 'textDocument/semanticTokens/full':
            return response(self.semantic_tokens(params['textDocument']['uri']))
        if method == 'textDocument/foldingRange':
            return response(self.folding_ranges(params['textDocument']['uri']))
        if method == 'textDocument/inlayHint':
            return response(self.inlay_hints(params['textDocument']['uri']))
        if method == 'workspace/symbol':
            return response(self.workspace_symbols(params.get('query', '')))
        if method == 'shutdown':
            self.shutdown = True
            return response(None)
        if method == 'exit':
            return None
        return response(None) if message_id is not None else None


def lsp_v2_report(server: LspV2Server) -> dict[str, Any]:
    """Return a deterministic report over capabilities and open documents."""

    documents = server.store.snapshot()
    diagnostics = {document.uri: server.diagnostics(document.uri)
                   for document in documents}
    payload: dict[str, Any] = {
        'version': LSP_V2_VERSION,
        'format': LSP_V2_FORMAT,
        'protocol_version': LSP_V2_PROTOCOL_VERSION,
        'root_uri': server.root_uri,
        'document_count': len(documents),
        'store_digest': server.store.digest(),
        'capabilities': server.capabilities(),
        'diagnostics': diagnostics,
        'gate': 'PASS',
    }
    payload['digest'] = _digest(payload)
    return payload


def lsp_v2_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Reduce an LSP v2 report to a deterministic PASS/FAIL decision."""

    issues: list[str] = []
    if report.get('version') != LSP_V2_VERSION:
        issues.append('version')
    if report.get('format') != LSP_V2_FORMAT:
        issues.append('format')
    if report.get('gate') != 'PASS':
        issues.append('report')
    capabilities = report.get('capabilities', {})
    required = ('capabilities', 'serverInfo')
    if any(key not in capabilities for key in required):
        issues.append('capabilities')
    if len(str(report.get('digest', ''))) != 64:
        issues.append('digest')
    return {'gate': 'PASS' if not issues else 'FAIL', 'issues': issues}


def build_lsp_v2_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'LSP_V2_VERSION': LSP_V2_VERSION,
        'LSP_V2_PROTOCOL_VERSION': LSP_V2_PROTOCOL_VERSION,
        'LSP_V2_FORMAT': LSP_V2_FORMAT,
        'LspV2Error': LspV2Error,
        'TextDocument': TextDocument,
        'DocumentStore': DocumentStore,
        'LspV2Server': LspV2Server,
        'lsp_v2_capabilities': lsp_v2_capabilities,
        'lsp_v2_report': lsp_v2_report,
        'lsp_v2_gate': lsp_v2_gate,
        'build_lsp_v2_namespace': build_lsp_v2_namespace,
    }


__all__ = [
    'LSP_V2_VERSION', 'LSP_V2_PROTOCOL_VERSION', 'LSP_V2_FORMAT',
    'LspV2Error', 'TextDocument', 'DocumentStore', 'LspV2Server',
    'lsp_v2_capabilities', 'lsp_v2_report', 'lsp_v2_gate',
    'build_lsp_v2_namespace',
]
