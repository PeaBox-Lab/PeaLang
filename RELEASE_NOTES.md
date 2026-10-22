# PeaLang 0.23.0 Release Notes

PeaLang 0.23 unifies VM embedding with the capability-based host boundary and introduces a VM-powered Debug Adapter Protocol server.

## Added

- Permission-protected host functions in `VMRuntime`.
- Registered host namespaces through `register_module`.
- `RuntimeOptions` support in compiled VM embedding.
- Host-value conversion through `to_pea` and `from_pea`.
- VM execution time and instruction budgets.
- VM-backed DAP server through `pea vm-dap`.
- DAP initialization, launch, source breakpoints, continue, stepping, stack traces, scopes, variables, evaluation, output, exception information, and termination.
- Debugging support for source and PEAC programs.
- Security and DAP regression tests.

## Compatibility

`PeaRuntime` remains available for interpreter-backed extensions. `VMRuntime` now follows the same permission vocabulary and value-conversion model, but advanced hostile-code isolation still requires a separate process or container.
