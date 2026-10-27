# Security Hardening 0.99.6

## Threats addressed
1. SSH machine-in-the-middle exposure caused by automatically trusting unknown host keys.
2. Duplication of legacy HMAC shared secrets into clear-text JSON trust metadata.
3. CPU denial of service from ambiguous regular expressions over uncontrolled PeaLang source.

## Decisions
- SSH unknown-host acceptance is removed, not deprecated.
- Legacy HMAC remains compatibility-only; public package authenticity uses the existing Ed25519 subsystem.
- Type analysis rejects type expressions over 65,536 characters and source inputs over 2,000,000 characters. Structural matching avoids unconstrained dot-star expressions.
