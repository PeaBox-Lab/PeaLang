# PeaLang AI Development Handover 0.16

Baseline: 0.17.0 reconstructed from the complete 0.15 source context.

## Delivered

- Function metadata and captured call frames
- Per-frame debugger locals
- Conditional, hit-count, log, and exception breakpoints
- Source-path-aware breakpoints
- DAP lifecycle and output events
- Expanded tests and release documentation

## Next release

Build 0.17 around a resumable instruction or bytecode engine. Replace line-based top-level replay with instruction-pointer continuation so nested loops, function calls, step-over, and step-out preserve exact execution state.

## Release rule

Every future release must include the full cumulative changelog, detailed release notes and README, help files, comprehensive user guides, dedicated basics/foundations documentation, roadmap, version history, tests, examples, and an updated AI development handover.
