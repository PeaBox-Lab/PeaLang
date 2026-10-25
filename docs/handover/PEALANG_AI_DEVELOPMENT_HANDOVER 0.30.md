

# PeaLang AI Development Handover 0.30

## Delivered

- VM profiler and source coverage
- general instrumentation and observer hooks
- benchmark API and CLI
- baseline benchmark workload
- interpreter vs VM differential test
- source inventory and SHA-256 comparison utility
- mandatory release no-removal gate
- release manifest/integrity reporting

## Primary files

- `pealang/observability.py`
- `pealang/benchmark.py`
- `pealang/release_integrity.py`
- `benchmarks/basic.pea`
- `tests/test_hardening_v030.py`

## Next release

0.31 should secure the package ecosystem: trusted registry configuration, HTTPS-only remote transport, signed manifests/packages, trust-store key IDs, SHA-256 verification, safe archive extraction with path traversal defenses, Git commit pinning/verification metadata, dependency-confusion defenses, offline mode, and auditable installation receipts.

## Release requirement

Continue cumulative documentation, full tests/examples, integrity inventory, no-regression source gate, deterministic artifacts, and updated AI handover on every release.


