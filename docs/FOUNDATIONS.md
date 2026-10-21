# PeaLang Foundations v0.9.0

PeaLang is an interpreted language. Lexer -> recursive-descent Parser -> typed AST -> tree-walk Interpreter is the authoritative v0.9 execution pipeline.

## Scope
Chained environments implement lexical scope and closures. Blocks use child environments; functions capture their declaration environment.

## Errors
`PeaError` is the language runtime error boundary. `throw` creates one; `try/catch/finally` handles it at language level. Catch objects expose message and source-location data.

## Function defaults
Parser `Param` nodes carry optional default expressions. Required parameters must precede defaults. Missing optional arguments evaluate their default expression at call time in the function call environment.

## Runtime direction
PeaLang will remain interpreter-first until grammar, module semantics and standard-library contracts are stable. Bytecode/VM work is a later optimisation and distribution project, not a prerequisite for usability.
