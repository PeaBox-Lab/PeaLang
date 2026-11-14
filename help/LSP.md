# Language Server Protocol (v1.1.0)

PeaLang provides a standards-compliant LSP server over stdio.

## Key capabilities

- Real-time diagnostics (syntax and type errors)
- Hover type signatures
- Completion for keywords, builtins, and standard library
- Go-to-definition
- Document symbols
- Semantic tokens

## Usage

Start the LSP server with `pea lsp` or use `analysis.LSPServer()`.