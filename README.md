# PeaLang 0.33.0

PeaLang is an embeddable extension language spanning bytecode/VM execution, optional typing, semantic analysis, native async, Python/FastAPI/Java/TypeScript/React integration, package management, observability, and signed supply-chain controls.

## Registry security additions

Version 0.33 adds canonical registry indexes, anti-replay sequence tracking, immutable version hashes, publisher namespace authorization, metadata expiration, HTTPS-only package URLs, and environment-based Bearer credentials.

Ed25519 remains the recommended publisher signature mechanism introduced in 0.32. Secrets are not stored in package locks.

See `docs/SIGNED_REGISTRY_INDEX.md`, `docs/ED25519_REGISTRY.md`, `docs/SIGNED_PACKAGES.md`, and `docs/PACKAGES.md`.
