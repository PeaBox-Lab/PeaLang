# VM Debug Adapter Protocol

Start the VM debugger adapter:

```bash
pea vm-dap
```

Supported requests include initialize, launch, attach, setBreakpoints, configurationDone, continue, next, stepIn, stepOut, threads, stackTrace, scopes, variables, evaluate, exceptionInfo, disconnect, and terminate.

The adapter emits initialized, output, stopped, and terminated events. It accepts `.pea` source or `.peac` bytecode. Evaluation currently supports variable-name lookup. Complex expression evaluation and conditional breakpoint execution are planned refinements.
