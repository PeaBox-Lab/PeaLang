
# PeaLang 0.81 Compatibility and Migration Hardening

## Delivered
- Machine-readable deprecation ledger with removal-version validation.
- Deterministic forward and reverse migration planning.
- Resumable migration markers and before/after SHA-256 evidence.
- Public API symbol/signature snapshots and semantic diffs.
- Approval gates for removed or signature-changed public APIs.
- Versioned upgrade fixtures for config and schema tests.

## Release policy
A deprecated API must name its replacement and have a removal version later than its introduction. Every persistent schema change must have an ordered migration; rollback-sensitive changes also require a downgrade function. Removed or changed public APIs fail the compatibility gate unless explicitly reviewed and approved.

