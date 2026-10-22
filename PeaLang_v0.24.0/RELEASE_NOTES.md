# PeaLang 0.25.0 Release Notes

PeaLang 0.24 substantially strengthens semantic analysis for typed extension contracts.

## Added

- `SemanticAnalyzer`, `SemanticResult`, and `FunctionContract` APIs.
- Flow-aware function body analysis.
- Return-type validation and missing-return diagnostics.
- Unreachable-code warnings.
- Function call arity and literal argument validation.
- Record field completeness, unknown-field, and field-type validation.
- Basic arithmetic and string expression inference.
- Nullable member-access diagnostics and null-narrowing foundation.
- `pea semantic` for files and folders.
- Fifteen new semantic regression tests.

## Compatibility

Typing remains optional. Existing untyped programs, compiled PEAC modules, VM embedding, capability boundaries, and the VM debugger remain available.
