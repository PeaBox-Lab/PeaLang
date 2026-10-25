# Debug Adapter Protocol

Start with `pea dap`. Communication uses Content-Length framed JSON over stdin/stdout. Supported requests: initialize, launch, setBreakpoints, configurationDone, continue, next, stepIn, stepOut, threads, stackTrace, scopes, variables, evaluate, disconnect and terminate.
