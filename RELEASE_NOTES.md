# PeaLang 0.19.0 Release Notes

PeaLang 0.19 adds the first optional static type layer for embed-friendly extension contracts.

## Added

- Primitive types: `Any`, `Never`, `Null`, `Bool`, `Int`, `Float`, `Number`, and `String`.
- Generic type references such as `List<String>` and `Map<String, Employee>`.
- Nullable types using `?`.
- Union types using `|`.
- Typed `let` and `const` declarations.
- Typed function parameters and return annotations.
- Named record declarations using `type Name = { ... }`.
- Type diagnostic codes and source locations.
- `TypeChecker`, `TypeRef`, `Diagnostic`, and `TypeCheckResult` public APIs.
- `pea typecheck` for files and folders.
- Runtime annotation erasure, preserving compatibility with untyped execution.
- Typed employee-rules example and typed embedding guide.

## Compatibility

Untyped PeaLang programs continue to run. Types are optional and erased before the 0.19 tree-walking runtime executes a program.
