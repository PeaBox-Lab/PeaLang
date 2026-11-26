# Language Server Protocol v2

Wave 3 opens with an additive LSP v2 layer. It does not change the frozen 3.0
language surface defined by `CORE_SURFACES`, and it does not replace the v1
`LSPServer`; both namespaces remain available.

`lsp_v2_capabilities()` returns the versioned capability set with full open/close
and incremental change synchronization, hover, completion, definition,
references, rename, document and workspace symbols, formatting, semantic tokens,
inlay hints, and folding ranges. `serverInfo` reports the implementation name
`pealang-lsp-v2` and version `3.1.44`, while `LSP_V2_PROTOCOL_VERSION` records the
negotiated LSP protocol version `3.17.0`.

`DocumentStore` holds versioned `TextDocument` values keyed by URI. `open()`
starts a document at version one; `change()` accepts either one full-text change
or a list of range edits and increments the version when no explicit version is
supplied. Range edits are applied from the end of the document backward so their
positions remain stable. `close()` removes a document, and `digest()` hashes the
sorted document snapshots. Every digest excludes wall-clock and host-specific
values.

`LspV2Server` exposes deterministic language features. Diagnostics use the
PeaLang lexer and parser and publish stable ranges and messages. Document symbols
cover functions, bindings, type aliases, protocols, and traits. Workspace
symbols filter those declarations across open documents. Completion combines
keywords, builtins, standard-library hints, and local declarations. Hover and
definition resolve the word under a zero-based LSP position; references and
rename use the same identifier boundary rules. Formatting trims trailing spaces
and preserves a terminal newline. Semantic tokens use the published legend and
LSP delta encoding; folding ranges follow balanced brace lines; inlay hints are
currently empty.

`handle_message()` dispatches one JSON-RPC message and returns a response only
for requests; notifications mutate state and return `None`. `lsp_v2_report()`
summarizes version, format, protocol version, root URI, document count, store
digest, capabilities, per-document diagnostics, and a stable report digest.
`lsp_v2_gate()` recomputes PASS/FAIL from the report version, format, required
capability keys, and digest shape.

The `pea lsp FILE.pea [--check] [--symbols] [--hover LINE CHAR] [--emit FILE.json]`
command exposes diagnostics and optional report evidence.
`pea lsp --capabilities` prints the versioned capability set. The
`editor.lsp_v2` feature flag records availability.
