# Ed25519 Packages and Verified Registry Transport

PeaLang 0.32 upgrades package authenticity from shared-secret HMAC to Ed25519 publisher signatures.

## Generate keys

```bash
pea keygen-ed25519 publisher.private publisher.public
```

The private key must remain with the publisher. Hosts and registries receive only the public key.

## Sign and verify

```bash
pea sign-ed25519 demo-1.0.0.peapkg publisher.private
pea verify-ed25519 demo-1.0.0.peapkg demo-1.0.0.peapkg.sig publisher.public
```

The signature envelope binds the Ed25519 signature to the package SHA-256 and a 24-character public-key fingerprint.

## Trust and revocation

`PublicTrustStore` stores public keys only, named HTTPS registries, and revocation records. Revoked keys cannot configure registries or validate packages when supplied to verification policy.

## Verified installation

`install_verified` verifies the signature and package hash before hardened extraction. `remote_install` requires HTTPS URLs, supports lockfile SHA-256 checking, stores downloads in a content-addressed cache, and supports offline installation from an existing cache entry.

## Security boundaries

The HTTP client uses the operating system/Python CA trust through `ssl.create_default_context`. Package verification remains independent of TLS, so a valid package must pass both transport and Ed25519 integrity checks before installation.
