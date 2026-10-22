# PeaLang 0.22.0 Release Notes

PeaLang 0.22 adds structured VM exceptions, literal default arguments, shared closures, and compiled module imports.

## Added

- `PUSH_HANDLER`, `POP_HANDLER`, and `IMPORT` bytecode operations.
- VM handling for `try`, `catch`, `finally`, and `throw`.
- Exception propagation and handler lookup across VM frames.
- Operand-stack restoration when a handler is entered.
- Literal function-default serialization in PEAC code objects.
- Default-argument arity validation in compiled functions.
- Shared lexical closure environments.
- Relative source-module imports.
- Imported export namespaces and per-VM module caching.
- PEAC round-trip testing for default parameters.
- New exception, closure, default, and module conformance tests.

## Compatibility

The PEAC format remains preview and now stores function defaults. Existing source programs remain compatible. Non-literal default expressions and some advanced interpreter constructs remain outside the VM subset.
