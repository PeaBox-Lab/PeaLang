


# PeaLang 0.88 Developer Tooling Stabilization

## Delivered
- Explicit LSP capability certification for initialize, diagnostics, hover, completion and definition.
- DAP certification for initialize, launch, breakpoints, continue, next, stack trace, scopes, variables and disconnect.
- Stable diagnostic code, severity and source contracts with snapshot support.
- Deterministic editor/server capability negotiation.
- Reproducible debug snapshots covering break reason, source line, function, variables and stack.
- Debug-session SHA-256 fingerprints for regression fixtures.
- A combined tooling certification gate.

## Stabilization policy
Diagnostic codes and severities are treated as compatibility contracts. Debug fixtures must be deterministic and contain no machine-specific paths. Tooling certification requires the mandatory LSP and DAP surfaces plus diagnostic and debug reproducibility evidence.



