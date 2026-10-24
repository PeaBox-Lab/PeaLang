
# PeaLang AI Development Handover 0.32

## Delivered

- Ed25519 publisher keypairs
- package signature envelopes and SHA-256 binding
- public-key trust store
- key revocation metadata
- HTTPS authenticated transport through system CA roots
- content-addressed package cache
- verified extraction/install
- offline cache mode
- expected lockfile SHA-256 enforcement
- Ed25519 package CLI
- security regression tests

## Architecture decision

Ed25519 is now the recommended package authenticity mechanism. HMAC from 0.31 remains for backwards-compatible controlled/internal workflows only.

## Next release

0.33 should complete registry metadata security: signed canonical registry indexes, publisher identities/namespaces, key rotation proofs and revocation distribution, package expiration/version anti-replay rules, authenticated registry credentials, dependency provenance in pea.lock, and end-to-end registry simulation tests.
