# Semantic Analysis

PeaLang 0.24 adds a flow-aware semantic pass above the optional type checker.

## Command

```bash
pea semantic src tests
```

The command reports errors and warnings and returns exit code `1` when semantic errors exist.

## Checks

- Function parameter and return contracts
- Function call arity and literal argument types
- Missing typed returns
- Return-type incompatibility
- Unreachable code after `return` or `throw`
- Record object missing fields
- Unknown record fields
- Record field value types
- Numeric and string expression inference
- Nullable record-access warnings and basic null narrowing

## Diagnostic groups

- `F2xx`: function return errors
- `F4xx`: flow warnings
- `R2xx`: record conformance errors
- `C2xx`: call contract errors
- `N2xx`: nullability errors

The analyzer is intentionally additive. Existing untyped programs continue to run.
