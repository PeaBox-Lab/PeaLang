# Signed Packages and Trust

PeaLang 0.31 adds package signing, signature verification, trusted-key storage, HTTPS-only registry policy, safe archive extraction, and installation receipts.

## Generate a signing key

```bash
pea keygen publisher.key
```

## Build and sign

```bash
pea build
pea sign my-package-1.0.0.peapkg publisher.key
```

The signature file contains the algorithm, key ID, package SHA-256, signature value, and creation timestamp.

## Verify

```bash
pea verify my-package-1.0.0.peapkg my-package-1.0.0.peapkg.sig publisher.key
```

## Trust store

```bash
pea trust ~/.pealang/trust.json publisher.key "Internal Publisher"
```

Registry configuration accepts HTTPS URLs only and requires known key IDs.

## Extraction security

`safe_extract` rejects absolute/path-traversal members and symbolic/hard links before extraction. Installation receipts record package hash, signature path, signing key ID, source, and installation timestamp.

## Cryptography scope

Version 0.31 uses HMAC-SHA256 shared publisher keys as the implemented signing foundation. This provides tamper detection and authenticity when the signing secret remains protected, but it is not public-key package signing. Ed25519 publisher signatures and key rotation/revocation should replace this model before enabling a public third-party registry.
