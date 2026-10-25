
# PeaLang 0.95 Final RC Acceptance

v0.95 remains feature-frozen. It turns the v0.94 release-engineering contracts into a final acceptance model.

## Gates
- Real evidence ingestion for installation matrix, security review, license review, runbooks and reproducibility.
- Zero unresolved critical/high release blockers; waivers must carry explicit expiry.
- Wheel, sdist and container digest/signature/provenance verification.
- Full staging release dry-run including rollback.
- Explicit manual release-owner and security-owner approval before GO.

The code validates evidence. It never fabricates external CI runs, signatures, human reviews or approvals. Until those are supplied, the correct final decision is NO-GO.

