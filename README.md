# PeaLang 0.30.0

PeaLang is an embeddable extension language for Python, FastAPI, Java, Spring Boot, TypeScript, React, APIs, workflows, and business applications.

## Production hardening

Profile a program:

```bash
pea profile app.pea
```

Benchmark it:

```bash
pea benchmark app.pea
```

The VM now exposes opt-in profiling, line coverage, instruction/opcode/function statistics, and transport-neutral observability events.

## Integration coverage

- Python / FastAPI
- Java / Spring Boot runtime sidecar
- TypeScript / React clients
- Sync and native async VM
- Optional static typing and semantic analysis
- DAP debugging
- Package manifests, locks, auditing, reproducible packages
- Release integrity and conformance gates

See `docs/PROFILING_COVERAGE.md`, `docs/RELEASE_INTEGRITY.md`, `docs/TYPESCRIPT_REACT.md`, and `docs/JAVA_RUNTIME.md`.
