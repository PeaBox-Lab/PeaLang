# PeaLang v0.2.0 Test Report

- **Validation date:** 2026-10-20
- **Environment:** Linux container, Python 3.12.15
- **Command:** `PYTHONPATH=. python -m unittest discover -s tests -v`
- **Result:** 18 tests passed, 0 failures, 0 errors
- **Compilation check:** `python -m compileall -q pealang tests` passed
- **CLI check:** `python -m pealang --version` returned `PeaLang 0.2.0`
- **Examples run:** hello, control flow, collections, and imports all completed successfully

## Coverage areas

The suite validates the five documented v0.1 regression behaviors and v0.2 behavior for loop control, typed-AST execution, interpolation, escaped braces, property access, indexed/property mutation, compound indexed assignment, imports, import idempotency, missing imports, missing properties, and source-position diagnostics.

## Validation boundary

Only the environment above was executed in this packaging session. The included GitHub Actions matrix is configured for Python 3.9 through 3.13, but those remote jobs have not yet been run here.

- **Packaging check:** wheel build passed with `python -m pip wheel . --no-deps --no-build-isolation`.
