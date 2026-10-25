


# Security Hardening 0.78

PeaLang 0.78 continues the post-0.77 v1 stabilization program by strengthening host trust boundaries without changing language semantics.

## Added
- `SecurityPolicy` centralizes maximum text/collection/path limits, URL schemes, private-network blocking and allowed filesystem roots.
- `SecurityValidator` validates text, collections, paths and URLs before data reaches an embedded runtime or connector.
- `redact_secrets` recursively removes common password, token, API-key, authorization and cookie values and masks bearer tokens.
- `SignedAuditChain` records redacted events in an append-only SHA-256 chain, optionally authenticated with HMAC-SHA256, and detects mutation/reordering.

## Security position
These controls complement, rather than replace, PeaLang VM resource budgets, permissions, connector policy, package signing and serving security. DNS resolution/rebinding defenses belong in the network transport layer because hostname resolution is environment-specific.



