



# PeaLang 0.85 Data and Connector Conformance

## Delivered
- Explicit connector capability profiles.
- Required and optional certification cases with stable IDs.
- SQL contracts for SQLite, PostgreSQL, MySQL, Microsoft SQL Server and Oracle.
- Parameter-binding count validation and transaction commit/rollback probes.
- Streaming checkpoint monotonicity, replay-after-checkpoint and duplicate suppression.
- Object-store pagination cycle detection, range-read validation and multipart abort evidence.
- Machine-readable certification reports and SHA-256 report digests.

## Certification policy
A connector is certified only when every required case for its declared capabilities passes. Optional undeclared capabilities are skipped; missing required capabilities fail. Production adapters should add vendor-specific fixtures without weakening the common contract.




