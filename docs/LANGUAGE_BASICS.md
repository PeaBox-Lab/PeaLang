# PeaLang Language Basics v0.9.0

## First program
```pea
let name = "World"
print "Hello {name}!"
```
Run it with `pea hello.pea`.

## Values
Numbers, strings, booleans, `null`, lists and dictionaries.

## Bindings
`let` is reassignable. `const` prevents rebinding.

## Decisions and loops
Use `if/else`, `for`, `while`, `break`, and `continue`.

## Functions
```pea
function add(a, b=1) { return a + b }
```
Functions use lexical closures, support recursion and now support trailing default arguments.

## Collections
Use `items[0]`, `person["name"]` and `person.name`; indexes/properties can be assigned.

## Errors
```pea
try {
    throw "bad input"
} catch err {
    print err.message
} finally {
    print "finished"
}
```
`throw` raises a PeaLang error. `catch` handles it or other `PeaError` runtime failures. `finally` always runs.

## Assertions
`assert total > 0, "total must be positive"`.

## Modules/projects
Local file imports, project modules and local path dependencies remain supported.

## Quality workflow
`pea fmt`, `pea check`, `pea test`, then `pea run`/`pea start`.
