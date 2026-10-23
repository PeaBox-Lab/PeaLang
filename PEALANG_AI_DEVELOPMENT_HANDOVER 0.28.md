# PeaLang AI Development Handover 0.28

## Delivered

- Java-oriented RuntimeService
- stdlib HTTP sidecar
- semantic validation before remote compilation
- bytecode compilation cache keyed by SHA-256
- module load and invocation contract
- health/readiness probes
- request IDs, timings, structured errors
- Java 17 client module
- Spring Boot integration guidance
- runtime service tests

## Primary files

- `pealang/runtime_service.py`
- `pealang/runtime_http.py`
- `java-sdk/`
- `examples/spring-boot/`
- `tests/test_java_service_v028.py`

## Next release

0.29 should add a TypeScript client mirroring the Java contract, React hooks for extension invocation/state, schema-driven UI data contracts rather than arbitrary JSX, signed registry transport foundations, and an explicit browser-safe capability profile. Keep server execution as the default until a WASM VM passes the conformance suite.

## Release requirement

Continue cumulative changelog, README, release notes, roadmap, version history, foundations, complete user/embedding/help docs, architecture/security notes, tests, examples, and updated AI handover.

