

# PeaLang AI Development Handover 0.22

## Delivered

- Structured VM exception handlers and frame unwinding
- Literal default parameters serialized in PEAC
- Shared lexical closure environments
- Relative bytecode module imports
- Export namespaces and module caching
- Fifty passing regression and conformance tests

## Primary implementation files

- `pealang/bytecode.py`
- `pealang/compiler.py`
- `pealang/vm.py`
- `tests/test_vm_modules_exceptions_v022.py`

## Known limitations

- Non-literal defaults are rejected by the VM compiler.
- VM imports currently load source `.pea` modules rather than choosing `.peac` automatically.
- Finally runs for normal flow and handled throws, but control-transfer semantics through finally require further hardening.
- Capability enforcement is not yet unified between `PeaRuntime` and `VMRuntime`.
- DAP remains interpreter-backed.

## Next release

Version 0.23 should unify VM embedding permissions with `RuntimeOptions`, add registered host namespaces, structured VM diagnostics, VM-backed DAP lifecycle and scopes, conditional breakpoints, exception breakpoints, and source-aware imported-module debugging.


