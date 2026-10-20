# Security Model
PeaLang v0.3.0 is not a sandbox. Its standard library uses the permissions and network access of the host Python process.

## Controls
- Process execution is denied by default.
- Opt-in process calls use `shell=False` and separate arguments.
- HTTP calls have a default 15-second timeout.
- Environment helpers avoid placing credentials in source code.

## Operator responsibilities
Run only trusted programs, use a restricted operating-system account, limit filesystem permissions, use egress controls for sensitive environments, store secrets in environment variables or a managed secret store, and do not enable process execution for downloaded scripts.
