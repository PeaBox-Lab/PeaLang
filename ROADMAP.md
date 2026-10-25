# PeaLang Revised Foundational Roadmap

The original roadmap goal is not yet complete. The implementation has covered much of the VM, embedding and integration work, but foundational maturity still requires specification completion, standard-library stabilization, deeper type semantics, structured concurrency, complete resource accounting, native language testing, larger conformance coverage, migration tooling, cross-platform CI evidence and production pilots.

## 0.34 - Specification and compatibility foundation - delivered
- Normative specification directory and EBNF grammar
- Feature stability registry
- Compatibility/deprecation rules
- Spec verification command

## 0.35 - Standard library stabilization
- `std.collections`, `std.string`, `std.math`, `std.datetime`, `std.json`, `std.csv`, `std.regex`, `std.file`, `std.path`, `std.http`, `std.crypto`, `std.logging`, `std.testing`, `std.concurrent`
- Permission declarations on sensitive modules
- Standard-library compatibility tests

## 0.36 - Type system completion
- Generic functions and substitution
- Protocols/interfaces
- Cross-module type checking
- Exhaustive flow/null narrowing
- Result/Option/Future semantics

## 0.37 - Runtime resource and concurrency completion
- Memory accounting and limits
- Collection/output/file/HTTP quotas
- recursion and call-depth enforcement everywhere
- task groups, spawn, cancellation propagation and structured concurrency

## 0.38 - Native testing and migration
- `test`, `describe`, `before_each`, `expect`
- `pea test --filter`, `--coverage`, `--watch`
- `pea migrate`
- compatibility/deprecation warnings

## 0.39 - Cross-runtime portability
- WebAssembly VM prototype
- browser-safe PEAC runtime
- Python VM/WASM differential fixtures
- Node/browser host capability ABI

## 0.40 - Conformance and platform gate - implementation delivered; CI evidence pending
- 500+ conformance tests
- parser/VM >=90% coverage target
- security-boundary 100% coverage target
- lexer/parser/compiler fuzzing
- Windows/Linux/macOS CI definitions
- Python 3.10-3.13 matrix or documented supported matrix

## 0.41 - Beta/pilot gate - tooling/evidence framework delivered; real pilot validation pending
- Two real application pilots
- three stable host integrations
- performance baselines and regression thresholds
- external security review preparation
- 1.0 migration report

## 1.0 gate
Grammar, type system, standard library, embedding API, package format and PEAC compatibility policy must be Stable; security must be reviewed; LSP/DAP workflows and documentation must be complete; real applications must run without runtime forks.


## 0.74 - Agent governance and repository hygiene - delivered
- Agent tool dry-run planning
- Deterministic deny and approval-required policy gates
- Host-provided approval callback with fail-closed default
- Per-run tool-call budget
- Historical handover archive under `docs/handover/`

## Next: v1 hardening programme
- End-to-end agent audit trails and persistent approval records
- Security review and adversarial agent/tool tests
- Conformance, coverage and cross-platform CI release evidence
- Documentation and migration completeness gate

## 0.75 - Durable agent governance - delivered
- Persistent approval decisions
- Agent/tool audit trail
- Reviewer and reason evidence
- Deterministic approval request IDs

## Next: 0.76 hardening
- adversarial agent/tool security suite
- public API compatibility gate
- conformance and coverage evidence
- security and performance release gates

## 0.76 - Release hardening - delivered
- adversarial agent/tool policy probes
- public API compatibility gate
- regression test threshold
- retention and security gate integration

## Next
- performance and memory optimization
- deeper security hardening
- enterprise integration certification
- public API freeze preparation

## 0.77 - Performance and memory hardening - delivered
- repeatable latency and memory probes
- mean/p95 budget gates
- bounded LRU runtime cache primitive

## Next
- deeper security hardening
- enterprise integration certification
- broader VM/compiler/data-path optimization
- public API freeze preparation


## 0.80 - Observability and operations hardening - delivered
- W3C trace-context propagation
- bounded spans and metric cardinality controls
- liveness/readiness contracts
- redacted diagnostic bundles with integrity manifests

## 0.81 compatibility and migration hardening - delivered
- deprecation ledger
- schema/config migration registry
- public API diff enforcement
- upgrade fixtures


## 0.82 release engineering and supply-chain hardening - delivered
- reproducible build manifests
- SBOM and provenance generation
- signed release verification
- release quality gates


## 0.83 runtime performance II - delivered
- representative benchmark suites
- optimizer/compiler hot-path profiling
- cache instrumentation
- memory-pressure behavior and regression budgets


## 0.84 concurrency and resilience - delivered
- cancellation and timeout propagation
- structured concurrency stress testing
- retry safety and idempotency evidence
- graceful shutdown and drain behavior


## 0.85 data and connector conformance - delivered
- SQL dialect conformance matrices
- streaming failure and recovery semantics
- object-store edge cases
- connector certification fixtures and gates


## Next: 0.86 ML and serving conformance
- model-format compatibility matrix
- deterministic inference fixtures
- overload, reload and rollback tests
- serving certification gates


## 0.86 - ML and serving conformance - delivered

## 0.87 - Agent safety conformance - delivered

## Next: 0.88 developer tooling stabilization
- LSP/DAP compatibility
- diagnostics stability
- reproducible debugging fixtures
- tooling certification gates
