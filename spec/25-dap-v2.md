# Debug Adapter Protocol v2

Wave 3 continues with an additive DAP v2 debug layer. It does not change the
frozen 3.0 language surface, and it does not replace the existing `dap` or
`vm_dap` stdio servers. Those namespaces remain available.

`dap_v2_capabilities()` returns the versioned DAP v2 capability set. It declares
configuration-done, conditional and hit-conditional breakpoints, hover
evaluation, exception info, restart, and variable support. It explicitly declines
step-back and step-in-target requests. `DAP_V2_PROTOCOL_VERSION` records the
Debug Adapter Protocol version `1.68.0`, and `DAP_V2_COMMANDS` is a sorted tuple
covering the required conformance commands plus attach, configuration-done,
continue, evaluate, exception-info, next, step-in, step-out, terminate, and
threads.

`DapV2Session` is a reproducible VM-backed session. `initialize()` emits an
initialized event and returns the capability set. `launch()` accepts source text
or a path, compiles or loads the bytecode, and creates a `VirtualMachine` with a
bounded instruction budget. It returns verified status, the source name,
instruction count, and the available source lines. `setBreakpoints()` validates
requested lines against the compiled instructions, creates ordered
`DapBreakpoint` records, installs breakpoints on the VM, and returns verified
DAP breakpoints. Breakpoints carry stable identifiers, optional `condition` and
`hitCondition`, enabled state, and hit counters.

Conditions are limited to deterministic comparisons of a local name with an
integer, such as `x == 1` or `count >= 3`, or a truthy local name. Hit conditions
compare the stable hit counter with an integer using `hits == 2` syntax. A
breakpoint whose conditions are not met emits a `continued` event with reason
`conditionNotMet` and resumes execution without changing the program result.
Built-in VM helper bindings are excluded from variable evidence so that
snapshots contain only program values.

`configurationDone()` starts the program; `continueRun()`, `next()`, `stepIn()`,
and `stepOut()` advance the VM through deterministic status objects. Stopped
events record the reason, source basename, line, and function. Termination
events record the program output. `stackTrace()`, `scopes()`, `variables()`,
`evaluate()`, `exceptionInfo()`, and `threads()` expose reviewable state.
`handleMessage()` dispatches one DAP request and always returns a response with
monotonic sequence numbers; request errors are reported in the response body
rather than raised.

`dap_v2_report()` summarizes version, format, protocol version, launch and
termination state, command coverage, conformance, breakpoints, events, output,
and snapshot fingerprint. The report digest excludes wall-clock values, VM
helper functions, and host-specific directory prefixes; source paths are reduced
to their basenames for digest purposes. `dap_v2_gate()` recomputes PASS/FAIL from
the report version, format, gate state, conformance, and digest shapes.

The `pea dap-v2 FILE.pea [--check] [--breakpoint LINE] [--emit FILE.json]`
command runs a bounded session, optionally installs one or more breakpoints, and
prints the resulting stops and output. `pea dap-v2 --capabilities` prints the
versioned capability set. The `debug.dap_v2` feature flag records availability.
