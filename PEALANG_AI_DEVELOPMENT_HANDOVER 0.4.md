# PeaLang AI Development Handover v0.4.0

## Current architecture
Lexer -> recursive-descent Parser -> typed AST -> optional Checker/Docs tooling -> Interpreter. `stdlib.py` supplies v0.3 automation namespaces. `tooling.py` supplies formatter, checker, discovery and API-document generation. `cli.py` exposes run/repl/fmt/check/test/docs while preserving direct file execution.

## Implemented through v0.4.0
All v0.1-v0.3 features plus formatter, static diagnostics, language-level test discovery, Markdown API docs, REPL meta-commands and comprehensive language-learning documentation.

## Tooling contracts
- Formatter is idempotent but currently drops comments.
- Checker reports P100 parser, P101 undefined, P102 duplicate and P104 unused diagnostics; it is not a type checker and does not resolve imports.
- Test runner considers normal completion a pass.
- Docs generator lists top-level non-private functions and source lines.

## Required documentation in every future release
Always include a detailed README, cumulative changelog, full release notes, roadmap, additions/improvements, user guide, language basics, language foundations, help articles, feature/reference documentation, test report, cumulative version history and updated AI handover.

## Next recommended release
v0.4.1 tooling hardening before concurrency: comment-preserving formatter, cross-file checks, native assertions/expected output, CLI tests, doc comments and LSP protocol foundations.
