# PeaLang AI Development Handover v0.5.0

## Architecture
Lexer -> Parser -> typed AST -> optional tooling -> Interpreter. `stdlib.py` exposes automation/task/workflow namespaces; `tooling.py` handles formatter/checker/docs; CLI handles run/repl/fmt/check/test/docs.

## New v0.5 nodes
`AssertStmt` is a statement. `ParallelExpr` is an expression producing an ordered list. The interpreter uses `ThreadPoolExecutor` capped at min(8, expression count).

## New v0.5 standard library
`workflow.step`, `workflow.result`, `task.sleep`, and `task.retry`. Workflow helpers are structural only. Parallel work shares the interpreter/process and is not isolated.

## Testing
`assert` raises `PeaError` when false. `pea test` compares optional sibling `.out` fixtures exactly by printed lines.

## Documentation invariant
Every future release must include a detailed README, full cumulative changelog, release notes, roadmap, additions/improvements, language basics, foundations, user guide, help articles, reference/feature docs, test report, cumulative version history and updated handover.

## Next direction
v0.6.0 AI workflow identity after v0.5 hardening: provider-neutral AI contracts, structured outputs, tool contracts, external credential configuration and portable skills. Do not embed secrets.
