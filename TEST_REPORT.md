# PeaLang v0.4.0 Test Report

- **Validation date:** 2026-10-20
- **Environment:** Linux container, Python 3.12.15
- **Unit tests:** 31 passed, 0 failures, 0 errors
- **Compilation:** `python -m compileall -q pealang tests` passed
- **CLI version:** returned `PeaLang 0.4.0`
- **Direct/run command:** passed with the bundled hello example
- **Pea test command:** 1 language smoke test passed
- **Formatter:** rewrite and subsequent `--check` passed
- **Checker:** checked the formatted tooling demo without an error
- **Docs generator:** generated a Markdown API reference successfully
- **Wheel:** `pealang-0.4.0-py3-none-any.whl` built successfully

## Regression coverage

The 27 v0.3 tests remain and cover the v0.1-v0.3 interpreter, diagnostics, collection mutation, imports and automation standard library. Four v0.4 unit tests cover formatter idempotence, undefined-variable checking, unused-variable warnings and API documentation generation.

## Validation boundaries

The GitHub Actions Python 3.9-3.13 matrix has not yet run remotely. The checker is not a type checker and does not resolve imported symbols. The formatter does not preserve comments in v0.4. The language-level test runner validates successful execution but does not yet supply native assertions or expected-output fixtures.
