# PeaLang 0.34.0 Release Notes

PeaLang 0.34 returns focus to unfinished language foundations. It introduces the first implementation-independent language specification and explicit feature compatibility contract.

## Added
- `spec/` normative specification tree covering introduction, lexical grammar, types, expressions, statements, functions, modules, errors, async, host interop, security and compatibility.
- `spec/grammar.ebnf` grammar foundation.
- Feature stability states: Experimental, Preview, Stable, Deprecated, Removed.
- Programmatic feature registry and deprecation-window validation.
- `pea spec` specification completeness verification.
- `pea features` feature stability listing.
- Revised foundational roadmap through the 1.0 gate.
- Specification/compatibility regression tests.

## Why this release
The original roadmap explicitly requires an implementation-independent specification and compatibility policy before maturity. PeaLang had built many runtime/integration layers ahead of those gates; 0.34 starts closing that debt.
