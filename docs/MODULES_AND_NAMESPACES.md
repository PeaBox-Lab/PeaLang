# Modules and Namespaces v0.10.0

## Exporting symbols
Inside an imported module, use `export name` after declaring the symbol.
```pea
function total(a, b) { return a + b }
const version = "1.0"
export total
export version
```

## Importing a namespace
```pea
import "billing.pea" as billing
print billing.total(2, 3)
print billing.version
```
Aliased imports execute in a child module environment. Only explicit exports are copied into the namespace dictionary.

## Privacy
A declaration that is not exported cannot be accessed through the namespace. This is module visibility, not a security sandbox.

## Legacy imports
`import "billing.pea"` retains the historical shared-global behaviour for backward compatibility. Prefer aliases for new programs.

## Projects and dependencies
Bare names still use project resolution: project `modules/`, then a matching local dependency, then the historical current-directory fallback. Alias semantics apply after resolution.

## Current boundaries
There is no `from ... import ...`, wildcard export, nested module path syntax, automatic namespace name, circular-module diagnostic, package registry or semantic-version solver yet.
