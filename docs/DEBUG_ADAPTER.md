# Debug Adapter Protocol

Run `pea dap` as a stdio child process. Messages use standard `Content-Length` framed JSON.

## v0.16 capabilities

- Conditional breakpoints
- Hit conditions: exact count, `>=N`, and `%N`
- Log points
- Exception breakpoint filter `all`
- Function-aware stack frames
- Per-frame local variables and globals
- Source-aware breakpoints for imported files
- `initialized`, `stopped`, `output`, and `terminated` events
- Hover/watch expression evaluation

The adapter remains synchronous and single-threaded. Thread ID `1` represents the PeaLang main execution thread.
