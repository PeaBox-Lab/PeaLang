# PeaLang v0.9.0 Test Report

- Validation date: 2026-10-21
- Environment: Linux container, Python 3.12.15
- Python unit tests: 56 passed, 0 failures, 0 errors
- PeaLang language tests: 2 passed, 0 failed
- Compilation check: passed
- CLI version: `PeaLang 0.9.0`
- Error-handling example: passed, including catch and finally
- Default-argument example: passed
- Wheel: `pealang-0.9.0-py3-none-any.whl` built successfully

## v0.9 coverage
Five new tests cover default arguments, try/catch, try/finally, catching ordinary runtime errors, and uncaught throw behavior. All 51 v0.8 tests remain.

## Boundaries
No compiler or bytecode VM is included; v0.9 is intentionally interpreter-first. No named/variadic arguments, type annotations, namespace imports or full stack traces yet. GitHub Actions' multi-Python matrix has not run remotely here. Known formatter multiline/comment limitations remain.
