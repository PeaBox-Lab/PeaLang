# PeaLang 0.17.0 Release Notes

PeaLang 0.17.0 is the usability and discoverability release. It introduces a complete built-in help system for both Windows command-line use and the interactive REPL while retaining the advanced debugging capabilities delivered in 0.16.

## Highlights

- `pea help` and `pea help TOPIC` from CMD, PowerShell, and terminals.
- Friendly `help`, `help TOPIC`, and `? TOPIC` aliases inside the REPL.
- New `:topics`, `:commands`, `:examples`, and `:version` REPL commands.
- Clear guidance separating PeaLang statements from operating-system commands.
- Topic pages for setup, syntax, variables, functions, collections, files, errors, debugging, and CLI commands.
- Helpful response for an unknown topic, including partial-match suggestions.
- Dedicated REPL and built-in-help Markdown documentation.
- Five new automated help-system tests.

## Upgrade compatibility

PeaLang syntax, runtime behavior, CLI entry points, project files, and the 0.16 debugger/DAP APIs remain compatible. Existing `.pea` programs require no migration.

## Known limitations

The runtime remains a synchronous tree-walking interpreter. Exact resumable state for deeply nested debugger operations is still planned for a future VM-focused release.
