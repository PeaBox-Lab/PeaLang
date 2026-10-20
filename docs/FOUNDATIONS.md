# PeaLang Foundations

## Design goals
PeaLang favors readability, a small grammar, predictable automation and beginner-friendly diagnostics. It is a tree-walk interpreted language hosted by Python 3.9+.

## Execution pipeline
1. The lexer converts characters into tokens and records source positions.
2. The recursive-descent parser converts tokens into typed AST dataclasses.
3. The checker can inspect the AST without executing it.
4. The interpreter evaluates statements and expressions using chained lexical environments.
5. The standard library exposes host capabilities through named dictionaries such as `json`, `csv`, and `http`.

## Scope and closures
Each function captures the environment where it is declared. Blocks and function calls create child scopes. Variables are resolved from the nearest scope outward.

## Truth and control flow
Conditions use host-style truthiness in v0.4. `and` and `or` short-circuit. Internal control-flow signals implement return, break and continue.

## Mutability
`const` prevents rebinding of a name. It does not deeply freeze a list or dictionary stored under that name. Lists and dictionaries remain mutable through index/property assignment.

## Data boundary
Automation APIs convert between PeaLang values and standard formats. JSON preserves compatible nested values. CSV reads cells as strings. HTTP responses are dictionaries. Date/time helpers use ISO text to remain portable.

## Compatibility principle
Existing valid programs should continue to run unless a breaking change is explicitly approved, versioned and documented. New developer tooling is additive and the `runtime.py` facade preserves the public Python API.

## Safety boundary
The interpreter is not a security sandbox. Language simplicity does not limit operating-system permissions. Use restricted accounts, filesystem controls and network egress policies for sensitive execution.
