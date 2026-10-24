
# Signed Registry Index and Publisher Policy

PeaLang 0.33 adds canonical registry metadata, namespace ownership, replay protection, immutable package-version policy, expiration checks, and environment-based registry authentication.

## Canonical index

Registry indexes serialize as deterministic JSON with sorted keys and no insignificant whitespace. This representation is suitable for Ed25519 signing with the existing v0.32 package-signature primitives.

Each package record carries package name, version, SHA-256, package URL, signature URL, publisher key ID, publication timestamp, and optional expiration timestamp.

## Anti-replay

Each registry index has a monotonically increasing sequence number. `RegistryState` persists the highest accepted number and rejects stale or replayed index versions.

## Immutable versions

Once `acme/demo` version `1.0.0` is observed with a SHA-256 digest, the same registry may not later associate that version with another digest.

## Namespace ownership

`NamespacePolicy` binds publisher key IDs to namespaces such as `acme`. A different publisher key cannot publish `acme/...` unless explicitly authorized.

## Authentication

Registry access tokens are read from environment variables such as:
