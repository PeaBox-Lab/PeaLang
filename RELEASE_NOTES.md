# PeaLang 0.31.0 Release Notes

PeaLang 0.31 secures the package ecosystem with signed-package foundations and hardened extraction.

## Added

- HMAC-SHA256 `.peapkg` signatures with package SHA-256 binding.
- Random 256-bit signing-key generation and deterministic key IDs.
- Signature verification with constant-time comparison.
- JSON trust store for publisher keys and named registries.
- HTTPS-only registry configuration policy.
- Safe archive extraction with path-traversal and link rejection.
- Installation receipts with provenance data.
- Dependency-confusion guard foundation.
- `pea keygen`, `pea sign`, `pea verify`, and `pea trust` commands.
- Ten signed-package security tests.

## Security note

This release deliberately uses shared-secret HMAC signing rather than claiming a mature public package-signing PKI. A public registry should not be enabled until Ed25519 signatures, key rotation/revocation, authenticated registry transport, and publisher identity policies are implemented.
