# PeaLang 0.33.0 Release Notes

PeaLang 0.33 completes another layer of package-registry supply-chain policy around the Ed25519 foundation delivered in 0.32.

## Added

- Canonical deterministic registry-index representation.
- Registry sequence numbers and stale/replay rejection.
- Immutable package-version SHA-256 policy.
- Duplicate index-record rejection.
- Package metadata expiration checks.
- HTTPS-only package and signature URLs in indexes.
- Publisher-key-to-namespace authorization policy.
- Persistent registry state for accepted sequence/version history.
- Environment-based Bearer authentication helpers without lockfile secret storage.
- Twelve registry metadata and authentication tests.

## Compatibility

Ed25519 package signatures, HMAC compatibility, package cache, offline installation, package manager, VM/runtime, integrations, and existing language features remain available.
