
# PeaLang AI Development Handover 0.23

## Delivered

- Capability-safe `VMRuntime`
- Permission-protected host functions and namespaces
- RuntimeOptions-based VM limits
- Portable host-value conversion
- VM-backed DAP server
- VM source breakpoints, stepping, frames, scopes, variables, output, and lifecycle events
- Fifty-five passing tests

## Primary implementation files

- `pealang/vm_embedding.py`
- `pealang/vm_dap.py`
- `pealang/vm.py`
- `tests/test_vm_security_dap_v023.py`

## Known limitations

- DAP evaluate resolves variable names only.
- Conditional breakpoints are advertised but condition execution requires further implementation.
- ExceptionInfo provides a generic VM error record.
- VM wall-clock enforcement is checked around exported calls, not preemptively during every instruction.
- Hostile extensions still require out-of-process isolation.

## Next release

Version 0.24 should mature semantic analysis: typed expression inference, record field conformance, function-call argument checking, return-path validation, null narrowing, unreachable-code diagnostics, imported contract loading, and at least 100 type conformance tests.

