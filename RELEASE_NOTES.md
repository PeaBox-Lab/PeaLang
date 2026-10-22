# PeaLang 0.20.0 Release Notes

PeaLang 0.20 introduces the first bytecode compiler and stack virtual machine.

## Added

- Versioned `PEAC` bytecode artifact and JSON serialization.
- Constant pool, instructions, top-level code, and function code objects.
- AST-to-bytecode compiler.
- Stack VM with explicit instruction pointer and call frames.
- Arithmetic, comparisons, variables, collections, control flow, functions, calls, returns, property access, and exports.
- Source-line metadata on every instruction.
- VM instruction-budget enforcement.
- Bytecode disassembler.
- `pea compile`, `pea dis`, and `pea vm` commands.
- Direct execution of `.peac` files.
- Compiler, VM, round-trip, disassembly, export, and budget tests.

## Compatibility

The tree-walking interpreter remains available and is still the compatibility runtime for language constructs outside the initial compiler subset. The bytecode format is preview in 0.20.
