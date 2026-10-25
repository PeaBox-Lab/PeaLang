

# PeaLang AI Development Handover 0.33

## Delivered

- canonical deterministic registry indexes
- package metadata schema with publisher/signature provenance
- monotonic sequence anti-replay validation
- immutable version/digest enforcement
- publisher namespace policy
- metadata expiration and HTTPS URL validation
- persistent accepted registry state
- environment-only registry Bearer credential helper
- registry policy regression tests

## Architecture

Registry index bytes are canonicalized so the existing Ed25519 layer can sign them deterministically. Package payload signatures remain independent of index signatures. Registry state persists sequence/version history to detect replay and version mutation.

## Next release

0.34 should shift back to runtime portability by establishing a WebAssembly target/prototype. Preserve PEAC as the language-neutral contract, define browser-safe imports/capabilities, expose a minimal WASM-compatible execution ABI, and add cross-runtime conformance fixtures rather than expanding syntax.


