
# External Security Review Preparation
## Review scope
- Python and VM embedding permission boundaries
- instruction/time/memory/output/file/HTTP resource controls
- HMAC backward-compatible signing and Ed25519 recommended signing
- signed registry indexes, namespace ownership and anti-replay
- archive extraction traversal/link defenses
- browser-safe capabilities and WASM policy metadata
## Required evidence
Threat model, security-boundary tests, CI coverage report, fuzz corpus/crash artifacts, dependency inventory, release hashes and remediation log.
## Status
Preparation complete. Independent external security review has not been performed and is not claimed.

