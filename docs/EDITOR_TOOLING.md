# Editor Tooling

PeaLang 0.13 introduces `pealang.editor` and `pea lsp`. The editor API exposes `diagnostics`, `symbols`, `definition`, `hover`, and `completions`. The LSP transport uses Content-Length framed JSON-RPC over stdin/stdout and supports initialize, shutdown, text synchronization, completion, hover, and same-document definitions.
