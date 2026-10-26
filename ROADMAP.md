


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

## 0.88 developer tooling stabilization - delivered
- LSP/DAP compatibility
- diagnostics stability
- reproducible debugging fixtures
- tooling certification gates


## 0.89 release-candidate hardening - delivered
- freeze new feature families
- close blocker and high-severity defects
- complete cross-platform/security/performance evidence
- release-candidate readiness gate


## 0.90 API freeze - delivered
- freeze public syntax, runtime and package APIs for 1.0
- require compatibility review for post-freeze changes
- publish authoritative API baseline
- permit only approved compatibility and blocker fixes


## 0.90 API freeze - delivered
- freeze public syntax, runtime and package APIs for 1.0
- allow only approved compatibility fixes
- publish final API baseline and freeze policy
- start 0.91-0.96 release-candidate soak line


## 0.91 release candidate validation I - delivered
- cross-platform soak and upgrade validation
- frozen-API compatibility surveillance
- security and performance regression soak
- RC blocker and waiver closure


## 0.92 release candidate validation II - delivered
- longer-duration cross-platform soak
- upgrade-path expansion and rollback drills
- compatibility-drift surveillance
- ecosystem/integration certification evidence


## 0.93 release candidate validation III - delivered
- extended-duration soak and repeated-run reliability contracts
- broader ecosystem certification evidence
- disaster-recovery and state-restoration drills
- release evidence provenance and reproducibility checks

## 0.94 release candidate validation IV - delivered
- installation and supported-upgrade matrix closure contracts
- wheel/sdist/container reproducibility and offline-install evidence contracts
- dependency/license and security-review closure gates
- operational runbooks and final 1.0 release-evidence consolidation

## 0.95 final RC acceptance - delivered
- real-evidence ingestion contracts
- blocker burn-down and waiver-validation gates
- signed-artifact and provenance verification contracts
- release dry-run, rollback and explicit GO/NO-GO gate

## 0.96 release readiness closure - delivered
- verified-evidence ingestion contracts
- documentation, support, packaging and operational readiness gates
- residual-risk closure and final 1.0 readiness dossier
- mandatory release/security/operations approvals

## 0.97 1.0 launch candidate - delivered
- frozen-change admissibility
- v0.96 readiness prerequisite
- signed artifact/provenance and operational playbook gates
- measurable rollback and launch approval gates

## 0.98 release dress rehearsal - delivered
- signed staging release evidence contracts
- clean-install, upgrade and rollback integrity drills
- support, incident and rollback operational rehearsal gates
- consolidated rehearsal approval with fail-closed evidence policy

## 0.99 final 1.0 release gate - delivered
- v0.98 rehearsal prerequisite
- blocker, waiver and residual-risk closure contracts
- final documentation and 1.0 signed distribution gates
- explicit GO-1.0/NO-GO dossier

## Next: PeaLang 1.0.0
- release only after all mandatory real evidence passes v0.99
- generate and sign final wheel, sdist and container artifacts
- publish final documentation and migration/support material
- archive the 1.0 release evidence and begin the post-1.0 maintenance line





## 0.99.1 audit closure - delivered
- component maturity and known limitations
- interface completeness classification
- SDK version and changelog normalization
- automated repository audit checks

## Next: 1.0.0 evidence execution
- complete full regression and 12-cell OS/Python CI
- retain real security, packaging, signing and install/upgrade/rollback evidence
- obtain release, security and operations approvals
- release only when v0.99 final gate returns GO-1.0


## 0.99.2 pre-1.0 evidence closure - delivered
- explicit complete external evidence inventory
- fail-closed evidence and approval gate
- release-evidence directory structure
- active version normalization

## Next: 1.0.0
- execute and retain every required real evidence item
- run final GO/NO-GO using genuine artifacts and approvals
- publish 1.0 only on GO


## 0.99.3 historical retention recovery - delivered
- root-normalized retention auditor and protected removals
- historical ledgers and compatibility recovery

## Next: 1.0 evidence execution
- execute genuine CI/security/package/install/upgrade/rollback evidence and release only on GO


## 0.99.4 security closure - delivered
- local code-pattern remediation and regression checks
- embedded Bandit, pip-audit, Semgrep and Trivy workflow

## Next: execute real scanner workflow and close findings before 1.0 GO
