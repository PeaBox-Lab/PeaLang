# PeaLang 0.21.0 Release Notes

PeaLang 0.21 expands VM parity and makes compiled extensions usable through a VM-backed embedding API.

## Added

- Bytecode compilation for `break` and `continue` with loop patch stacks.
- Compound assignment for variables: `+=`, `-=`, `*=`, `/=`, and `%=`.
- Property and index assignment opcodes.
- `throw` lowering through the `RAISE` opcode.
- VM breakpoints, continuation, single-instruction stepping, stack traces, locals, source names, and line events.
- `VMRuntime` and `VMModule` for loading compiled extensions and calling exports.
- Interpreter-versus-VM differential tests.
- Expanded PEAC opcode set and VM parity documentation.

## Compatibility

PEAC remains preview. Existing 0.20 source and bytecode format structure remains readable, while 0.21 adds opcodes. The interpreter remains the broadest compatibility runtime.
