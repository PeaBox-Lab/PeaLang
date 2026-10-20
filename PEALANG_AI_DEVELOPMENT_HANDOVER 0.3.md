# PeaLang AI Development Handover v0.3.0
## Identity
PeaLang by PeaBox Lab, Python 3.9+, `.pea`, preferred CLI `pea`, MIT.
## Architecture
Lexer -> recursive-descent Parser -> typed dataclass AST -> Interpreter. `runtime.py` preserves the public API. `stdlib.py` builds namespaced automation modules represented by dictionaries, which work with v0.2 property access.
## Implemented through v0.3.0
All v0.1/v0.2 behavior plus `file`, `path`, `json`, `csv`, `env`, `datetime`, `regex`, `http`, and `process`. Process execution is disabled by default, uses `shell=False`, and requires `--allow-process` or `allow_process=True`.
## Compatibility
Legacy flat built-ins remain. The automation APIs are namespaced and preferred for new code.
## Validation
Run `python -m unittest discover -s tests -v`, `python -m compileall -q pealang tests`, and all bundled non-network examples. Do not claim the GitHub Actions matrix ran until it runs remotely.
## Known limitations
No sandbox, package manager, import namespaces, formatter/checker/LSP, exception syntax, concurrency, database layer or AI provider abstraction. Regex behavior is Python-compatible in this release. CSV values are strings when read.
## Next release
v0.4.0 Developer Experience: formatter, checker, test runner/syntax, richer REPL, docs generator, syntax highlighting and LSP foundations.
## Release discipline
Update README, full changelog, roadmap, release notes, language/feature/user guides, help, additions, security, test report, examples, cumulative history, and this handover every release.
