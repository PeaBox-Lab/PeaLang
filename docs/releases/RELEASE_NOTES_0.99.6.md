# PeaLang 0.99.6 Security Hardening Release

## Scope
This release remediates the fourteen high-severity CodeQL findings reported against 0.99.5 without rewriting historical tags.

## Security fixes
- SFTP connections no longer expose an automatic unknown-host trust path. Paramiko uses RejectPolicy and configured or system known-hosts data.
- The legacy HMAC TrustStore records only key identifiers and metadata, not Base64-encoded shared secrets. Ed25519 remains the recommended public signing system.
- Type-system analysis applies bounded input limits and hardened structural patterns that avoid ambiguous arbitrary-text matching over uncontrolled source.

## Compatibility
The HMAC sign and verify functions remain available for controlled internal compatibility. The removed SFTP allow_unknown_host option was insecure and is intentionally not retained.

## Validation
Run `python -m pytest -q` and the GitHub CodeQL workflow. Release acceptance requires zero open High alerts on the 0.99.6 commit.
