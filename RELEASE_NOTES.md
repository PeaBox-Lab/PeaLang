# PeaLang 0.26.0 Release Notes

PeaLang 0.26 introduces native cooperative asynchronous execution in the bytecode VM.

## Added

- `async function` syntax.
- `await` expressions and `AwaitExpr` AST node.
- `AWAIT` PEAC opcode.
- VM suspension records preserving source and line information.
- `AsyncVirtualMachine`, `AsyncVMRuntime`, and `AsyncVMModule`.
- Permission-protected Python async host functions.
- Async exported-function invocation through `call_async`.
- Cooperative `CancellationToken`.
- Wall-clock deadlines through `asyncio.wait_for`.
- Async host-value conversion and typed output conversion.
- Async syntax, permission, timeout, and execution tests.

## Compatibility

Synchronous PeaLang programs and APIs remain available. Async extensions require `AsyncVMRuntime` and must await asynchronous exports from Python.
