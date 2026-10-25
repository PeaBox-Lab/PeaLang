

# PeaLang 0.91 Release Candidate Validation I

## Purpose
0.91 is a validation release after the 0.90 API freeze. It adds no new feature family.

## Validation contracts
- Cross-platform soak matrix: Windows, Linux and macOS.
- Python runtime matrix: 3.10, 3.11, 3.12 and 3.13.
- Upgrade fixtures must prove migration, rollback and data integrity.
- Frozen API, diagnostics and bytecode compatibility must not drift from the 0.90 contract.
- Security, performance, packaging and offline-install evidence must individually pass.
- Blocker, critical and high-severity defects must be closed or have a valid explicit waiver.

## Important evidence boundary
The framework can validate evidence produced by CI and certification labs. A local Linux run does not itself prove Windows/macOS or all Python versions. Those matrix cells must be populated by actual runs before a production release decision.


