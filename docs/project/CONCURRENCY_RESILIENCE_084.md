# PeaLang 0.84 Concurrency and Resilience

## Delivered
- Parent-child cancellation tokens with manual, timeout, shutdown and parent reasons.
- Monotonic deadlines and timeout propagation.
- Fail-fast structured task groups that cancel sibling work after failure.
- Retry safety requiring explicit idempotency or an idempotency key.
- Payload-fingerprint protection against unsafe idempotency-key reuse.
- Graceful service draining that stops admission, waits for active work, then cancels overdue work.
- Release gates for cancellation latency, drain time, retry safety and orphan tasks.

## Default operational targets
- Cancellation propagation: at most 1 second.
- Graceful drain: at most 30 seconds before forced cancellation.
- Retry: disabled unless the operation is idempotent or has a stable idempotency key.
- Shutdown completion: zero orphaned tasks.
