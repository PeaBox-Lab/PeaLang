# PeaLang Language Reference

## Values
Numbers, strings, booleans, null, lists, and dictionaries.

## Declarations
`let x = 1` creates a variable. `const x = 1` creates a non-assignable binding.

## Control flow
`if`, `else`, `while`, `for item in collection`, `break`, and `continue`.

## Functions
`function add(a, b = 1) { return a + b }`. Functions are closures and required parameters must precede defaults.

## Modules
`import "module"` executes once. `import "module" as m` creates a namespace from explicit `export name` declarations. Circular imports are rejected.

## Errors
Use `try { ... } catch err { ... } finally { ... }` and `throw value`. `assert condition, "message"` raises an error.

## Parallel expressions
`parallel { expression1; expression2 }` returns ordered results. Do not mutate shared language state inside these expressions.

## Standard namespaces
`file`, `path`, `json`, `csv`, `env`, `datetime`, `regex`, `http`, `process`, `task`, `workflow`, `ai`, `skill`, `tool`, and `agent`.
