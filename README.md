# PeaLang v0.10.0

**A small language for big ideas.** PeaLang is an interpreted programming language. Write `.pea` files and execute them with `pea file.pea` or `pea run file.pea`.

v0.10.0 is the **Modules & Namespaces** release. It introduces explicit module exports and aliased namespace imports while preserving legacy shared-scope imports for compatibility.

## Install and run
```bash
python -m pip install -e .
pea --version
pea examples/namespaces.pea
```

## Namespace imports
Module:
```pea
# math.pea
function square(x) { return x * x }
function internal() { return 999 }
export square
```
Application:
```pea
import "math.pea" as math
print math.square(9)
```
Only exported names appear in `math`. `internal` remains private to the module environment.

## Legacy compatibility
The earlier form remains valid:
```pea
import "helpers.pea"
```
It executes once and places declarations in shared scope. New code should prefer `import "..." as namespace` plus explicit `export` statements because that prevents accidental global-name collisions.

## Projects
Bare project modules continue resolving through `modules/` and local dependencies. They can now be imported into namespaces:
```pea
import "math" as math
print math.square(10)
```

## Execution model
PeaLang still uses source -> lexer -> parser -> typed AST -> interpreter. A compiler is not required. The project remains interpreter-first while the language stabilises.

## Core language
Variables/constants, operators, conditions, loops, closures/recursion, collections, interpolation, assertions, exceptions, default arguments, modules/namespaces and bounded parallel expressions are supported. Earlier automation/AI/agent features remain compatible but are not the roadmap focus.

## Documentation
Read `docs/LANGUAGE_BASICS.md`, `docs/FOUNDATIONS.md`, `docs/MODULES_AND_NAMESPACES.md`, `docs/EXECUTION_MODEL.md`, `docs/USER_GUIDE.md`, and `docs/help/`.

## License
MIT.
