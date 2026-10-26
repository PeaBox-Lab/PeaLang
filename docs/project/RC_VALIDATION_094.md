


# PeaLang 0.94 Release Candidate Validation IV

v0.94 keeps the 1.0 feature freeze and closes release-engineering evidence.

## Required evidence
- Install matrix: Windows/Linux/macOS across Python 3.10-3.13; every cell must prove fresh install, supported upgrade, rollback and offline install.
- Reproducibility: at least two wheel, sdist and container builds with identical artifact, SBOM and provenance digests.
- Review closure: dependency audit, third-party license review and security review complete, with zero unresolved critical/high findings.
- Operational runbooks: at least four owner-assigned tested procedures within their recovery target.
- Final gate: v0.93 evidence remains passing and there are no unresolved blockers.

The implementation validates supplied evidence and does not claim external matrices or human reviews ran unless real records are provided.



