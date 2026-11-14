# Language Server Protocol (v1.1.0)

PeaLang provides a standards-compliant LSP server over stdio.

## Features

- Real-time diagnostics (syntax and type errors)
- Hover type signatures
- Completion for keywords, builtins, and standard library
- Go-to-definition
- Document symbols
- Semantic tokens

## Usage

Start the LSP server:

```bash
pea lsp
```

Or use the Python API:

```python
from pealang.lsp import LSPServer
server = LSPServer()
server.run()
```

## VS Code Extension

A VS Code extension is available in `editors/vscode/` with:
- TextMate grammar for syntax highlighting
- DAP client wiring for debugging
- LSP client for IntelliSense