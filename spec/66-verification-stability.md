# Verification stability and SDK contract hardening

Phase 123 at version 5.23.0 is a Wave 9 maintenance release.
It is additive in metadata and documentation only, and it does not change the
frozen 3.0 language surface, the public API snapshot, or the stable feature
registry.

Phase 123 hardens verification and SDK contracts. Timing-sensitive async
tests are changed to use never-completing pending operations with explicit event
gates instead of short sleeps against tiny deadlines. The Java client test
asserts the documented `health`, `ready`, `compile`, `loadModule`, and `invoke`
surface through reflection. Python-side checks assert that Java and browser SDK
metadata match the active runtime version. Performance evidence remains in the
existing `perf-gate` workflow; no new wall-clock-based deterministic gate is
introduced.

The release keeps `SECTIONS` at 13, preserves every pinned component version,
and leaves the core freeze digest unchanged.
