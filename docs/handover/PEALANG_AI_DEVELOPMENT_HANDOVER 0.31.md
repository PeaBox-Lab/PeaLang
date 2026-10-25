

# PeaLang AI Development Handover 0.31

## Delivered

- HMAC-SHA256 package signing and verification
- 256-bit signing key generation and key IDs
- publisher/registry trust store
- HTTPS-only registry policy foundation
- hardened tar extraction against traversal and links
- installation provenance receipts
- dependency-confusion guard foundation
- signing CLI commands
- signed-package regression tests

## Important limitation

HMAC uses a shared secret. It is suitable for controlled/internal publisher workflows but is not the final design for a public ecosystem. Do not present 0.31 as public-key signing.

## Next release

0.32 should add Ed25519 public/private keys, signature envelopes, signed registry indexes, trusted public keys only, key rotation/revocation metadata, authenticated HTTPS fetch, verified remote install, offline cache, lockfile provenance, and end-to-end tamper/replay tests.

## Release requirement

Preserve cumulative changelog, detailed README, release notes, roadmap, version history, basics/foundations, user/help/embedding/security docs, tests/examples, integrity manifest, no-removal gate, and updated handover.


