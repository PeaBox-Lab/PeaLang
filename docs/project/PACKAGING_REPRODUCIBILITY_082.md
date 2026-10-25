
# PeaLang 0.82 Packaging and Reproducibility Hardening

## Delivered
- Deterministic source-file manifests with size, SHA-256 and a canonical root digest.
- Tamper verification reporting added, missing and changed files.
- CycloneDX SBOM integrity verification against local release contents.
- SLSA/in-toto provenance subject verification against built artifacts.
- Detached Ed25519 release-manifest signing and verification.
- Dependency lockfile evidence and offline wheelhouse readiness checks.
- One packaging quality gate combining manifest, SBOM, provenance, signature, dependency and offline-install evidence.

## Release policy
A releasable package must pass all quality-gate checks. Ed25519 private keys must remain external to the repository. Reproducibility evidence is content based, so timestamps are not part of deterministic source manifests.

