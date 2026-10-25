
# Runtime Limits and Structured Concurrency 0.37

PeaLang now exposes explicit limits for execution time, instructions, memory accounting, recursion depth, stack depth, collection items, output bytes, HTTP requests, and file-read bytes. `ResourceBudget.snapshot()` provides auditable usage.

Structured concurrency provides `CancellationScope`, `TaskGroup`, `PeaTask`, and `gather_structured`. Child cancellation follows the parent scope and task groups await all children.

