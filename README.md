# PeaLang v0.2.0

**A small language for big ideas.** PeaLang is a readable Python-hosted language for learning, scripting, business automation, and future AI workflows.

## What is new

v0.2.0 replaces the brittle tuple AST with typed dataclasses, splits the runtime into focused modules, adds source-aware diagnostics, `break`, `continue`, string interpolation, dictionary property access, indexed/property assignment, and quoted-file imports.

## Quick start

```bash
python -m pip install -e .
pea examples/hello.pea
python -m unittest discover -s tests -v
```

```pea
let employee = {"name": "Rajesh", "skills": ["HR", "AI"]}
employee.skills[1] = "PeaLang"
print "Hello {employee.name}. Skill: {employee.skills[1]}"
```

## Commands

- `pea file.pea` runs a program.
- `pea` opens the persistent REPL.
- `pea --version` prints the installed version.
- `pealang` remains an alias for compatibility.

## Project map

- `pealang/lexer.py` tokenization
- `pealang/parser.py` recursive-descent parser
- `pealang/ast_nodes.py` typed AST
- `pealang/interpreter.py` execution
- `pealang/environment.py` lexical scope
- `pealang/runtime.py` compatibility facade
- `docs/` language, architecture, guides and help
- `examples/` runnable `.pea` programs
- `tests/` regression and feature tests

## Current boundaries

Imports execute a local `.pea` file once in the same global environment. They are foundations, not yet namespaces or packages. File and import access are not sandboxed. PeaLang has no exceptions, concurrency, HTTP, package manager, static typing, or AI provider layer yet.

## Documentation

Start with `docs/GETTING_STARTED.md`, then read `LANGUAGE.md`, `docs/USER_GUIDE.md`, `docs/ARCHITECTURE.md`, and `ROADMAP.md`.

## License

MIT. See `LICENSE`.
