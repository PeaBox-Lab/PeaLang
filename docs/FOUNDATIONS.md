# PeaLang Foundations v0.10.0

PeaLang remains an interpreted language built around Lexer -> Parser -> typed AST -> Interpreter.

## Module environments
An aliased module executes in an `Env` whose parent is the interpreter global environment. Module-local declarations therefore do not pollute the caller. Explicitly exported local values are copied into a namespace dictionary bound to the alias.

## Visibility
`export` controls namespace visibility. It is not an access-control or sandbox mechanism. Module code still executes with ordinary PeaLang runtime privileges.

## Compatibility
Unaliased imports keep the v0.2-v0.9 shared-scope semantics. This allows old programs to run while new code adopts namespaces.

## Direction
The next language milestone is optional typing and checker enforcement. Runtime compilation remains deferred until semantics are stable.
