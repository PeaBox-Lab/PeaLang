# PeaLang v0.2.0 Release Notes

v0.2.0 is the Foundation and Maintainability release. It modernizes the interpreter architecture while keeping v0.1 programs working.

## Highlights
- Typed AST rather than positional tuples.
- Diagnostics identify source, line and column.
- Loop control with `break` and `continue`.
- Readable interpolation: `"Hello {name}"`.
- Natural dictionary access: `employee.name`.
- Mutable collection targets: `scores[0] += 5`.
- First import foundation: `import "helpers.pea"`.

## Validated
The release test suite and all bundled examples were run locally during packaging. See `TEST_REPORT.md` for the exact environment and results.

## Known limitations
Imports share global scope and have no namespace syntax. Interpolation is currently recognized in ordinary quoted strings and parses expressions independently. The runtime remains unsandboxed.
