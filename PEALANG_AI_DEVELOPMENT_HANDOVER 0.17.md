# PeaLang AI Development Handover 0.17

## Baseline

Version 0.17.0 builds on the tested 0.16.0 source package. The release adds a centralized `pealang.help_system` module and integrates it with the command-line interface and REPL.

## Delivered

- General and topic-specific help through `pea help [topic]`.
- REPL aliases: `help`, `:help`, and `?`.
- REPL commands: `:topics`, `:commands`, `:examples`, and `:version`.
- Help pages for language syntax, variables, functions, collections, file operations, errors, debugging, and CLI commands.
- Unknown-topic handling with suggestions.
- Dedicated documentation and automated help tests.
- Full preservation of the 0.16 debugger and DAP work.

## Primary implementation files

- `pealang/help_system.py`
- `pealang/cli.py`
- `tests/test_help_v017.py`
- `help/REPL.md`
- `help/HELP_SYSTEM.md`

## Recommended 0.18 direction

Introduce an explicit instruction pointer or bytecode VM so continuation no longer relies on top-level line filtering. Preserve the public interpreter and debugger APIs during the experiment. Add differential tests that execute identical programs through the tree-walking runtime and VM.

## Release documentation rule

Every future release must include a cumulative changelog, detailed release notes, README, roadmap, version history, help files, complete user guides, basics/foundations documentation, automated tests, examples, and an updated AI development handover.
