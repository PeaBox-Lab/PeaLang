# PeaLang Development Handover v0.9.0

## Strategic direction
Core language maturity now takes priority over AI tooling. Keep existing AI/agent compatibility but do not lead with it.

## Execution model
PeaLang is interpreter-first: Lexer -> Parser -> typed AST -> Interpreter. End users run `.pea` through `pea`. No compiler is required.

## v0.9 implementation
New AST: `TryStmt`, `ThrowStmt`, `Param`. Parser supports try/catch/finally, throw and trailing default parameters. Interpreter catches `PeaError` into dictionary error objects and evaluates missing defaults at call time.

## Required documentation invariant
Every release includes detailed README, cumulative changelog, detailed release notes, roadmap, additions/improvements, language basics, foundations, user guide, help files, reference/feature docs, test report, cumulative history and handover.

## Next
v0.10 modules/namespaces, then v0.11 optional typing. Standalone runtime comes before compiler/VM work.
