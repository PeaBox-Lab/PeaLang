# PeaLang v0.9.0

**A small language for big ideas.** v0.9.0 shifts the roadmap decisively back to the programming language itself.

PeaLang is currently an **interpreted language**. Users write `.pea` files and execute them with the `pea` runtime:

```bash
pea hello.pea
# or
pea run hello.pea
```

The runtime performs: source -> lexer -> parser -> typed AST -> interpreter -> output. A native compiler is not required to use PeaLang today.

## Install and run
```bash
python -m pip install -e .
pea --version
pea examples/hello.pea
```

## v0.9 language additions
### Exceptions
```pea
try {
    throw "something failed"
} catch err {
    print "Error: {err.message}"
} finally {
    print "cleanup"
}
```
`catch` also catches ordinary PeaLang runtime errors. The optional error object contains `message`, `source`, `line`, and `column`.

### Default function arguments
```pea
function greet(name, greeting="Hello") {
    return "{greeting} {name}!"
}
print greet("Rajesh")
print greet("Rajesh", "Welcome")
```
Required parameters must come before parameters with defaults.

## Core language
PeaLang supports bindings, arithmetic/comparison/logic, conditions, loops, break/continue, functions/closures/recursion, lists/dictionaries, interpolation, imports, assertions, exception handling, default arguments and bounded parallel expressions.

## Execution commands
```text
pea FILE                   Execute a source file
pea run FILE               Explicit execution
pea repl                   Interactive interpreter
pea start                  Run project entry from pea.json
pea check PATH             Static checks
pea fmt PATH               Format source
pea test PATH              Language tests
```

## Why interpreter, not compiler yet?
The interpreter keeps language development fast while syntax and semantics are still evolving. The long-term roadmap now prioritises language maturity, modules/namespaces, optional typing, standard-library contracts, standalone runtime distribution, editor tooling and only then a bytecode VM/compiler prototype.

## Documentation
Read `docs/LANGUAGE_BASICS.md`, `docs/FOUNDATIONS.md`, `docs/EXECUTION_MODEL.md`, `docs/USER_GUIDE.md`, `LANGUAGE.md`, and help files under `docs/help/`.

## Compatibility
v0.9 retains v0.1-v0.8 functionality. AI/agent APIs remain available but are no longer the roadmap focus.

## License
MIT.
