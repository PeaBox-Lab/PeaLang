# PeaLang v0.3.0 Test Report

- **Validation date:** 2026-10-20
- **Environment:** Linux container, Python 3.12.15
- **Unit command:** `PYTHONPATH=. python -m unittest discover -s tests -v`
- **Result:** 27 tests passed, 0 failures, 0 errors
- **Compilation:** `python -m compileall -q pealang tests` passed
- **CLI:** `python -m pealang --version` returned `PeaLang 0.3.0`
- **Wheel:** `python -m pip wheel . --no-deps --no-build-isolation` passed
- **Examples:** automation, CSV report, and opt-in process examples passed

## Tested areas

The complete 18-test v0.2 regression suite remains. Nine v0.3 tests validate JSON, paths, regex, environment variables, file/JSON/CSV integration, date/time, default-denied processes, opt-in processes, and HTTP against an isolated local HTTP server.

## Validation boundaries

The HTTP test used a local loopback server, so no external web service was required. The GitHub Actions matrix is configured for Python 3.9 through 3.13 but has not been run remotely in this packaging session. PeaLang remains unsandboxed.
