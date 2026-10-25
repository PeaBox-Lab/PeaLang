

# PeaLang 0.90 API Freeze

## Frozen for the 1.0 line
- Intended public syntax and semantics.
- Runtime and embedding interfaces.
- Public package and module APIs.
- Stable diagnostic identifiers and severities.
- Versioned bytecode/persistence surfaces where declared compatible.

## Post-freeze policy
Additions are compatible by default only when they do not invalidate a frozen contract. Removed or changed surfaces require explicit approval evidence with reviewer and rationale. Deprecations must use the ledger and migration guidance.

## Evidence
`ApiFreezeManifest` creates canonical SHA-256 API digests. `freeze_gate` blocks unapproved removals or changes. `compatibility_contract` emits the machine-readable contract continuously validated by the 0.91-0.96 release-candidate line.


