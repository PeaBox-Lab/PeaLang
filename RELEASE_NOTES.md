# PeaLang 0.32.0 Release Notes

PeaLang 0.32 upgrades the package supply-chain foundation to public-key Ed25519 signatures and verified registry installation primitives.

## Added

- Ed25519 private/public publisher key generation.
- Public-key fingerprints and signature envelopes.
- Ed25519 signing and verification over package SHA-256.
- Public-key-only trust store.
- Signing-key revocation records and registry rejection of revoked keys.
- HTTPS registry fetch using the system CA trust store.
- Content-addressed package cache.
- Verified install and offline-cache install primitives.
- Optional lockfile SHA-256 verification during download.
- `pea keygen-ed25519`, `pea sign-ed25519`, and `pea verify-ed25519`.
- `cryptography>=42` runtime dependency.
- Ten Ed25519/registry security tests.

## Compatibility

The v0.31 HMAC commands remain for controlled internal workflows. Ed25519 is the recommended signing mode from v0.32 onward.
