# PeaLang 0.12.0

PeaLang is a compact, readable language for automation, workflows, local tools, and AI-oriented applications. Version 0.12.0 is the **Dependency Integrity** release, building on the 0.11 hardening baseline. It preserves the 0.10 syntax while improving diagnostics, imports, project validation, packaging, tests, and release discipline.

## Install

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e .
pea --version
```

Requires Python 3.9 or newer.

## First program

```pea
let name = "PeaLang"
function greet(who = "world") { return "Hello {who}" }
print greet(name)
```

Save as `hello.pea`, then run `pea run hello.pea`.

## Commands

- `pea run FILE` executes a program.
- `pea repl` opens the interactive shell.
- `pea fmt PATH...` formats source.
- `pea check PATH...` performs static checks.
- `pea test [PATH...]` runs `.pea` tests.
- `pea docs FILE` generates API notes.
- `pea init PATH` creates a project.
- `pea start` runs the project entry point.
- `pea add NAME PATH` and `pea remove NAME` manage local dependencies.

## Included language features

Variables and constants, lists and dictionaries, functions with defaults and closures, conditions and loops, imports and exports, exceptions, assertions, interpolation, parallel expressions, project manifests, standard namespaces, AI-provider adapters, tools, agents, and reusable skills.

## Security

PeaLang is not a sandbox. Process execution is disabled unless `--allow-process` is explicitly supplied. Run untrusted programs only in an OS-level container or restricted account. See `docs/SECURITY.md`.

## Documentation

Start with `docs/BASICS.md`, `docs/USER_GUIDE.md`, `LANGUAGE.md`, `docs/PROJECTS.md`, and `docs/TROUBLESHOOTING.md`.

## Dependency integrity

After `pea add NAME PATH`, run `pea lock` to create `pea.lock`. Commit the lockfile. Use `pea verify` in CI or before deployment; exit code 1 indicates missing, removed, or hash-mismatched dependencies.
