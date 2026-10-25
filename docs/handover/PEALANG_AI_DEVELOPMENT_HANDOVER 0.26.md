


# PeaLang AI Development Handover 0.26

## Delivered

- async/await lexer, parser, AST, compiler, and bytecode support
- AWAIT suspension and resume in the VM
- AsyncVirtualMachine
- capability-safe AsyncVMRuntime
- async exported-function calls
- Python coroutine host functions
- cancellation token
- execution timeout
- async documentation and regression tests

## Architecture

Synchronous VM execution returns `AsyncSuspension` when an AWAIT instruction receives a Python awaitable. The async driver awaits it without losing VM frames, instruction pointers, locals, stack state, source mapping, or instruction accounting, then resumes execution.

## Known limitations

- User async functions currently share normal compiled function metadata rather than a separate async function flag.
- Task groups and `all` syntax need deeper language-level design.
- Cancellation is checked at suspension/resume boundaries.
- Async module imports and async DAP stepping need further hardening.

## Next release

Version 0.27 should deliver the package ecosystem foundation: `pea.toml`, `pea.lock`, semantic version constraints, local/Git/private-feed sources, deterministic resolution, checksums, permission manifests, package archives, install/update/audit commands, and reproducible builds.



