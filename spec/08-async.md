# Async

`async function` defines an asynchronously invocable function. Its declared
return type `T` is presented to static analysis as `Future<T>` at call sites;
`await` unwraps that future to `T` and reports `A201` when the awaited value is
known not to be a future.

`await` suspends while preserving VM frames, locals, operand stack and
instruction position. The async VM exposes a `concurrency` namespace with
`sleep`, `spawn`, `gather`, `timeout`, `result`, and `cancel`. Spawned tasks
inherit a structured cancellation scope, and a runtime `CancellationToken`
cancels that scope and all of its children. `gather` accepts a list or tuple of
awaitables and returns their results in source order.

Deadlines are runtime policies. `timeout(seconds, awaitable)` applies a local
deadline by wrapping the awaitable. Structured task groups remain Preview.
