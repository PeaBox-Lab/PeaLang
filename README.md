# PeaLang 0.32.0

PeaLang is an embeddable extension language with bytecode/VM execution, optional typing and semantic analysis, async execution, multi-stack integration, package management, observability, and signed package supply-chain controls.

## Ed25519 package signing

```bash
pea keygen-ed25519 publisher.private publisher.public
pea build
pea sign-ed25519 demo-1.0.0.peapkg publisher.private
pea verify-ed25519 demo-1.0.0.peapkg demo-1.0.0.peapkg.sig publisher.public
```

Public keys can be distributed to consumers without exposing publisher private keys. v0.32 also provides public trust/revocation records, verified HTTPS retrieval, content-addressed caching, verified extraction, offline installs, and expected SHA-256 enforcement.

See `docs/ED25519_REGISTRY.md`, `docs/SIGNED_PACKAGES.md`, `docs/PACKAGES.md`, and `docs/RELEASE_INTEGRITY.md`.
