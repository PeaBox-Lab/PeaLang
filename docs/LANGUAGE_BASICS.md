# PeaLang Language Basics v0.10.0

Run a file with `pea file.pea`. PeaLang is interpreted, so compilation is not required.

## Values and bindings
Numbers, strings, booleans, `null`, lists and dictionaries. `let` can be rebound; `const` cannot.

## Control flow
`if/else`, `for`, `while`, `break`, and `continue`.

## Functions
Functions use lexical scope, support recursion and trailing default parameters.

## Collections and strings
Lists/dictionaries support index/property access and mutation. Strings support `{expression}` interpolation.

## Errors
Use `try/catch/finally` and `throw`.

## Modules
Prefer namespace imports:
```pea
import "math.pea" as math
print math.square(4)
```
The module must explicitly `export square`.

## Projects
Use `pea init`, `pea start`, project `modules/`, and local path dependencies.

## Quality
Use `pea fmt`, `pea check`, `pea test`, and `pea docs`.
