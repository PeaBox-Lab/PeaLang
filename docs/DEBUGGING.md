# Debugging

Use `pea debug FILE --break=LINE`. The API is `DebugSession(source)`, `add_breakpoint(line)`, `step()`, `continue_run()`, `variables()`, and `stack()`. Breakpoints currently apply to top-level statements. Snapshot values are Python-backed runtime values and JSON output uses string fallback for non-serializable objects.
