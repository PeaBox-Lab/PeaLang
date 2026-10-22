# PeaLang 0.16.0 Release Notes

PeaLang 0.16.0 is an advanced debugging release. It upgrades the 0.15 DAP foundation with source-aware breakpoints, condition evaluation, hit-count rules, log points, exception stops, captured function call frames, per-frame locals, and explicit DAP lifecycle events.

## Compatibility

Language syntax and public runtime entry points remain compatible with 0.15.0. Existing `pea run`, `pea repl`, project, formatting, checking, testing, documentation, AI, tool, agent, and skill workflows continue to work.

## Known limitation

The interpreter is still synchronous and tree-walking. Debug execution is single-threaded, and the resume engine remains conservative for deeply nested control-flow continuation. A resumable execution engine is a candidate for the 0.17 bytecode experiment.
