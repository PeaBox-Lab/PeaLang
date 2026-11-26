# PeaLang Cross-Sector Adoption Plan

This plan answers one question: **what must PeaLang build so it belongs in the same
conversation as the dominant languages of every major sector?**

The target lists are:

| Region / sector | Dominant languages today |
|---|---|
| Enterprise / Finance / Banking | Java, SQL |
| Data Science / AI / ML | Python, R, SQL |
| Frontend Web | JavaScript, TypeScript |
| Mobile (Android) | Kotlin, Java |
| Mobile (iOS) | Swift, Objective-C |
| Game Development | C++, C# (Unity), C++ (Unreal) |
| Embedded / IoT / Operating Systems | C, C++, Rust |
| Cloud Infrastructure / DevOps | Go, Python, Bash, TypeScript (CDK/Terraform) |

## Definition of “on the list”

PeaLang should not be added to a list by slogan. It earns a place in a sector when
all four gates are true:

1. **Capability gate** — the language, runtime, and stdlib cover the sector’s core work.
2. **Interop gate** — PeaLang works with the sector’s existing platforms and data formats.
3. **Evidence gate** — reference apps, conformance tests, and published benchmarks exist.
4. **Tooling gate** — editors, builds, packages, debugging, and CI are production-quality.

## Execution waves

### Wave 0 — Trust foundation (Phases 52–60)

Required by every row: deterministic lockfiles, registry resolution, signed
publish/install, reproducible packages, workspaces, strict quality gates, offline
cache, plugins, and an extension SDK.

### Wave 1 — Language core (Phases 61–70)

Error handling v2, generics v2, protocols/traits, iterators, async/concurrency,
module system v2, safe metaprogramming, resource scopes, conformance suite,
and a frozen 3.0 core.

**Phase 61 — Structured Error Handling v2** starts Wave 1 with a shared error
value schema. Interpreter and bytecode runs now expose the same typed catch
records, error codes, cause chains, context, and source spans, so libraries and
hosts can route failures consistently.

**Phase 62 — Generics v2** adds a real static generic layer: scoped type
parameters, preserved contracts, call-site inference, protocol bounds, and
recursive generic compatibility. Runtime annotations remain erased, so existing
programs continue to execute unchanged.

**Phase 63 — Protocols/Traits** completes the structural contract layer:
marker traits, optional `=` protocol bodies, signature-aware conformance checks,
and conformance diagnostics scoped to protocols actually used as generic bounds.
Extension types can now publish name-only protocol contracts, and all contracts
remain static and erased before execution.

**Phase 64 — Iterators** turns iteration into an explicit shared protocol.
Interpreter, bytecode VM, and async VM expose `iter`, `next`, `has_next`, and
`peek`;
loops use one cleanup path so `break` no longer leaks VM stack values. Static
analysis understands `Iterable<T>` and `Iterator<T>`, while existing eager
helpers and comprehensions keep their current behavior.

**Phase 65 — Async/Concurrency v2** exposes a `concurrency` namespace inside the
async VM for spawning, gathering, timeouts, and cancellation. Cancellation
tokens now propagate into structured child scopes, and static analysis models
`async function` declarations as `Future<T>` so `await` can infer element types
and report `A201` for known non-futures.

**Phase 66 — Module System v2** shares one resolver across the interpreter,
bytecode VM, and async VM. Imports now accept dotted project paths with
`__init__.pea` candidates, use project manifests and normalized dependencies,
cache aliased imports, and reject cycles. Project analysis exposes a module
graph with `M201` unresolved-import and `M203` cycle diagnostics.

**Phase 67 — Safe Metaprogramming** adds an explicit, validated macro layer.
Definitions are bounded, metavariables are checked for consistency, and hygiene
markers generate fresh identifiers so macro temporaries cannot capture caller
code. Expansion reports `MG101`-`MG203` issues and is opt-in through
`compile_source_with_macros()`, leaving legacy string macros and existing
programs unchanged.

**Phase 68 — Resource Scopes** introduces `using` bindings with guaranteed LIFO
cleanup across the interpreter and bytecode VM. Scopes own bounded child budgets,
nesting inherits limits, and cleanup runs on both normal and exceptional exits.
Hosts receive the same `ResourceScope`/`ResourceScopeManager` primitives, while
static analysis reports `R201`/`R202` for duplicate or reassigned bindings.

**Phase 69 — Conformance Suite** adds a curated portable suite for the language
core. Cases run on the interpreter, bytecode VM, macro expander, and static
project analysis with normalized outputs and stable diagnostic-code checks.
Reports are per-case and per-runtime, and a deterministic PASS/FAIL gate makes
the suite usable as a CI prerequisite without changing the legacy harness.

**Release version alignment** updates current package, SDK, container, runtime,
registry, manifest, and specification metadata to the tagged `v3.1.36` release
line. Historical phase notes and older versioned documents remain unchanged.

**Phase 70 — Frozen 3.0 Core** closes Wave 1 with a stable, additive-only core
contract. `pea freeze` combines the v2 conformance suite, public API removal
checks, specification verification, version agreement, and an explicit manifest
of frozen surfaces into one PASS/FAIL gate. Wave 2 can optimize and extend the
runtime without changing the frozen language surface.

### Wave 2 — Runtime and performance (Phases 71–80)

Bytecode optimizer, fast interpreter, JIT, native backend, WASM backend, parallel
runtime, profiler, and 4.0 performance gates.

**Phase 71 — Bytecode Optimizer** opens Wave 2 with conservative peephole
passes on portable `.peac` bytecode: constant folding, dead literal push/pop
removal, and unreachable-code removal with jump remapping. `pea optimize`
reports pass counts and a deterministic digest, and `--verify` proves VM
output/result parity before a release adopts the optimized artifact. The frozen
3.0 language surface and its manifest digest remain unchanged.

**Phase 72 — Fast Interpreter** adds a direct-handler execution path that
pre-binds supported instructions to closures instead of walking a dispatch
chain. Programs using calls, handlers, imports, iterators, or object access
automatically fall back to the standard VM. `pea fast --verify` proves output
and result parity, so hot scripts and small loops can adopt the fast path
without changing the frozen language surface.

**Phase 73 — Bytecode JIT** adds a profile-guided trace JIT on the same portable
bytecode. A non-emitting profiling pass records instruction counts, hot loop
back-edges become bounded compiled traces, and integer arithmetic is specialized
behind type guards. Guard failures deoptimize to the standard VM, and
`pea jit --verify` requires identical VM and JIT output and results. The frozen
3.0 language surface and manifest digest remain unchanged.

**Phase 74 — Native backend** lowers the same portable bytecode subset to a
deterministic native IR and a self-contained C source artifact. Modules outside
the supported instruction or constant set remain on the standard VM, and
`pea native --verify` requires identical VM and native output and results. Hosts
can compile the emitted artifact for deployment without changing the frozen 3.0
language surface or manifest digest.

**Phase 75 — WASM backend** lowers the same portable bytecode subset to typed
WASM IR in a custom-section WebAssembly module, with a reviewable `.wat` text
form and an artifact inspector. Unsupported modules remain on the standard VM,
and `pea wasm-backend --verify` requires identical VM and backend output and
results. Browser and edge hosts can consume the artifact without changing the
frozen 3.0 language surface or manifest digest.

**Phases 76–78 — Runtime performance** complete Wave 2. The parallel runtime
executes isolated bytecode tasks in a bounded worker pool and publishes ordered
output, falling back to the standard VM when a task uses async suspension or
module imports. The runtime profiler records deterministic opcode, function, and
line counters with VM parity checks. The 4.0 performance gates combine timing
budgets with parity, conformance, and frozen-core evidence. Each surface is
additive and leaves the frozen 3.0 manifest digest unchanged.

### Wave 3 — Developer experience (Phases 81–90)

LSP v2, DAP debugger, formatter v3, linter v3, test framework v2, incremental
build system, versioned docs, migration assistants, and project templates v2.

**Phase 81 — LSP v2** opens Wave 3 with a deterministic editor layer additive to
the v1 server. It advertises versioned capabilities, synchronizes full and
incremental document changes in a digest-stable store, and exposes diagnostics,
symbols, hover, completion, references, rename, formatting, folding, inlay hints,
and semantic tokens as reviewable functions. `pea lsp --check` and
`lsp_v2_gate()` provide CI-ready evidence without changing the frozen 3.0
language surface or manifest digest.

**Phase 82 — DAP debugger v2** continues Wave 3 with a deterministic debug layer
additive to the existing DAP servers. It launches bytecode on the VM with a
bounded instruction budget, verifies conditional and hit-conditional breakpoints,
and records reproducible stop events and snapshot fingerprints. Stack, scope,
variable, evaluation, exception, and disconnect commands are reviewable responses,
while `pea dap-v2 --check` and `dap_v2_gate()` provide CI-ready evidence without
changing the frozen 3.0 contract.

**Phase 83 — Formatter v3** continues Wave 3 with a deterministic formatting
layer additive to the existing formatter. Validated profiles control indentation,
line length, brace style, and EOF newlines while comments and string contents stay
intact. Reviewable diffs, long-line reports, idempotence checks, and bytecode
parity fingerprints make formatting safe for editor and CI automation through
`pea fmt-v3 --check` and `formatter_v3_gate()`.

**Phase 84 — Linter v3** continues Wave 3 with a deterministic diagnostics layer
additive to the existing linter. Validated profiles control line length,
complexity, rule toggles, and strict warning policy. Stable rule codes, fix
hints, sorted findings, and host-path-independent digests make results reviewable
in editors and reproducible in CI through `pea lint-v3 --check` and
`lint_v3_gate()`.

**Phase 85 — Test framework v2** continues Wave 3 with deterministic test
evidence additive to the native test runner. Validated profiles control name
filtering, fail-fast execution, and an allowed failure count. Stable case IDs,
sorted outcomes, and digests that exclude timings and host paths make runs
reviewable in editors and reproducible in CI through `pea test-v2 --check` and
`test_v2_gate()`.

**Phase 86 — Incremental build system v2** continues Wave 3 with deterministic
build evidence additive to the existing `pea build`. Validated profiles control
file limits, test inclusion, import checks, and dirty-failure policy. Stable
topological order, content-digest dirty sets, propagated reasons, and digests
that exclude host paths make plans reviewable and reproducible in CI through
`pea build-v2 --check` and `build_v2_gate()`.

**Phase 87 — Versioned docs** continues Wave 3 with deterministic documentation
evidence additive to the existing `pea docs`. Validated profiles control file
limits, release-note inclusion, link checks, the current version, and drift
policy. Stable entries with digests, version references, and internal links;
sorted stale-version and broken-link issues; and digests that exclude host paths
make documentation reviewable and reproducible in CI through `pea docs-v2 --check`
and `docs_v2_gate()`.

**Phase 88 — Migration assistants** continues Wave 3 with deterministic
migration evidence additive to the existing `pea migrate`. Validated profiles
control migration limits, test-migration inclusion, import checks, the current
version, and dirty policy. Stable nodes with digests, script names, resolved
dependencies, propagated dirty reasons, and topological order; sorted
missing-script, cycle, and limit issues; and digests that exclude host paths
make migration plans reviewable and reproducible in CI through `pea migrate-v2
--check` and `migration_v2_gate()`.

**Phase 89 — Project templates v2** continues Wave 3 with deterministic
project template catalogs additive to the existing scaffold surface. Validated
profiles control template limits, community inclusion, dependency checks, the
current version, and drift policy. Stable nodes with digests, names, versions,
file sets, entrypoints, resolved dependencies, propagated drift reasons, and
topological order; sorted missing-dependency, cycle, invalid-manifest,
bad-entrypoint, and limit issues; and digests that exclude host paths make
template plans reviewable and reproducible in CI through `pea templates-v2
--check` and `templates_v2_gate()`.

**Phase 90 — Developer experience v2** closes Wave 3 with a deterministic
evidence gate over the editor, debug, format, lint, test, build, docs, migration,
and template tooling. Validated profiles control tool limits, experimental
inclusion, evidence checks, the current version, and incomplete policy. Stable
nodes with digests, names, versions, formats, evidence paths, checks, resolved
dependencies, propagated incomplete reasons, and topological order; sorted
missing-dependency, cycle, invalid-manifest, missing-evidence, and limit issues;
and digests that exclude host paths make developer-experience evidence
reviewable and reproducible in CI through `pea devex-v2 --check` and
`devex_v2_gate()`.

### Wave 4 — Sector packs (Phases 91–98)

One focused pack per row of the table, each with a reference application and
conformance suite.

**Phase 91 — Enterprise/Finance/Banking sector pack** opens Wave 4 with a
deterministic evidence gate for the first row of the sector table, additive to
`std.sql`, connectors, capability controls, and the lock/audit/quality CLI.
Validated profiles control artifact limits, sandbox inclusion, interop and audit
contract checks, the current version, and incomplete policy. Stable nodes with
digests, names, versions, kinds, evidence paths, contracts, resolved
dependencies, propagated incomplete reasons, and topological order; sorted
missing-dependency, cycle, invalid-manifest, missing-evidence, missing-interop-
contract, and missing-audit-rule issues; and digests that exclude host paths make
sector evidence reviewable and reproducible in CI through `pea finance-pack
--check` and `finance_pack_gate()`.

**Phase 92 — Data Science / AI / ML sector pack** continues Wave 4 with a
deterministic governance gate for the second row of the sector table, additive
to `analysis.py`, `timeseries.py`, `forecasting.py`, `ai_ml.py`, `jupyter_kernel.py`,
`serving_runtime.py`, `std.analysis`, and `std.stats`. Validated profiles control
workflow limits, preview inclusion, parity and benchmark checks, the current
version, and incomplete policy. Stable nodes with digests, names, versions,
kinds, evidence paths, published metrics, resolved dependencies, propagated
incomplete reasons, and topological order; sorted missing-dependency, cycle,
invalid-manifest, missing-evidence, missing-parity-suite, and missing-benchmark
issues; and digests that exclude host paths make workflow evidence reviewable and
reproducible in CI through `pea data-pack --check` and `data_pack_gate()`.

**Phase 93 — Frontend Web sector pack** continues Wave 4 with a deterministic
delivery gate for the third row of the sector table, additive to the browser
SDK, React SDK, TypeScript SDK, templates, and web ecosystem. Validated profiles
control app limits, canary inclusion, DSL and interop checks, the current
version, and incomplete policy. Stable nodes with digests, names, versions,
kinds, evidence paths, declared bridges, resolved dependencies, propagated
incomplete reasons, and topological order; sorted missing-dependency, cycle,
invalid-manifest, missing-evidence, missing-state-model, and missing-interop-bridge
issues; and digests that exclude host paths make frontend evidence reviewable and
reproducible in CI through `pea web-pack --check` and `web_pack_gate()`.

**Phase 94 — Mobile (Android) sector pack** continues Wave 4 with a deterministic
delivery gate for the fourth row of the sector table, additive to
`host_bindings.py`, `vm_embedding.py`, and the Java client sidecar. Validated
profiles control app limits, preview inclusion, lifecycle/JVM/Gradle checks, the
current version, and incomplete policy. Stable nodes with digests, names,
versions, kinds, evidence paths, platform bindings, resolved dependencies,
propagated incomplete reasons, and topological order; sorted missing-dependency,
cycle, invalid-manifest, missing-evidence, missing-lifecycle-binding,
missing-JVM-bridge, and missing-gradle-plugin issues; and digests that exclude
host paths make Android evidence reviewable and reproducible in CI through
`pea android-pack --check` and `android_pack_gate()`.

**Phase 95 — Mobile (iOS) sector pack** continues Wave 4 with a deterministic
delivery gate for the fifth row of the sector table, additive to
`host_bindings.py`, `vm_embedding.py`, and the Java client sidecar. Validated
profiles control app limits, preview inclusion, Swift/Objective-C/XCFramework/
Xcode template checks, the current version, and incomplete policy. Stable nodes
with digests, names, versions, kinds, evidence paths, platform bindings,
resolved dependencies, propagated incomplete reasons, and topological order;
sorted missing-dependency, cycle, invalid-manifest, missing-evidence,
missing-Swift-bridge, missing-Objective-C-layer, missing-XCFramework, and
missing-Xcode-template issues; and digests that exclude host paths make iOS
evidence reviewable and reproducible in CI through `pea ios-pack --check` and
`ios_pack_gate()`.

**Phase 96 — Game Development sector pack** continues Wave 4 with a deterministic
delivery gate for the sixth row of the sector table, additive to
`host_bindings.py`, `vm_embedding.py`, and the Java client sidecar. Validated
profiles control game limits, preview inclusion, native/WASM runtime, ECS,
Unity/Unreal bridge, hot-reload, input API, and render API checks, the current
version, and incomplete policy. Stable nodes with digests, names, versions,
kinds, evidence paths, platform bindings, resolved dependencies, propagated
incomplete reasons, and topological order; sorted missing-dependency, cycle,
invalid-manifest, missing-evidence, missing-runtime, missing-ECS-binding,
missing-engine-bridge, missing-hot-reload, missing-input-API, and
missing-render-API issues; and digests that exclude host paths make game evidence
reviewable and reproducible in CI through `pea game-pack --check` and
`game_pack_gate()`.

**Phase 97 — Embedded / IoT / OS sector pack** continues Wave 4 with a deterministic
delivery gate for the seventh row of the sector table, additive to
`host_bindings.py`, `vm_embedding.py`, and the Java client sidecar. Validated
profiles control firmware limits, preview inclusion, native profile, C ABI,
RTOS binding, static binary, GPIO/I2C/SPI/CAN bus, safety audit, bounded-memory,
and signed-update checks, the current version, and incomplete policy. Stable
nodes with digests, names, versions, kinds, evidence paths, platform bindings,
resolved dependencies, propagated incomplete reasons, and topological order;
sorted missing-dependency, cycle, invalid-manifest, missing-evidence,
missing-native-profile, missing-C-ABI, missing-RTOS-binding,
missing-static-binary, missing-bus-API, missing-safety-audit,
missing-bounded-memory, and missing-signed-update issues; and digests that
exclude host paths make firmware evidence reviewable and reproducible in CI
through `pea embedded-pack --check` and `embedded_pack_gate()`.

**Phase 98 — Cloud Infrastructure / DevOps sector pack** completes Wave 4 with a
deterministic delivery gate for the eighth row of the sector table, additive to
the package lifecycle CLI, `frameworks.py` k8s/cloudbuild/edge scaffolds,
`cloud_connectors.py`, `object_storage.py`, and `kafka_connector.py`. Validated
profiles control deployment limits, preview inclusion, container image,
Kubernetes manifest, CI pipeline, observability, IAM policy, Go/Python/Bash/CDK/
Terraform source bridges, lockfile, signed package, and drift checks, the current
version, and incomplete policy. Stable nodes with digests, names, versions,
kinds, evidence paths, platform bindings, resolved dependencies, propagated
incomplete reasons, and topological order; sorted missing-dependency, cycle,
invalid-manifest, missing-evidence, missing-container-image,
missing-Kubernetes-manifest, missing-CI-pipeline, missing-observability,
missing-IAM-policy, missing-source-bridge, missing-lockfile, missing-signed-package,
and missing-drift-check issues; and digests that exclude host paths make cloud
stack evidence reviewable and reproducible in CI through `pea cloud-pack --check`
and `cloud_pack_gate()`. All eight rows of the sector table now have focused
packs with reference evidence and stable gates.

### Wave 5 — Ecosystem release (Phases 99–100)

**Phase 99 — Ecosystem registry and migration guides** opens Wave 5 with a
deterministic delivery gate for the first half of the ecosystem release, additive
to the registry resolution, signing, publishing, and migration-assistant
surfaces. Validated profiles control entry limits, preview inclusion,
Python/JavaScript/Java/Go/Rust/SQL migration guides, registry packages, registry
metadata, signatures, lockfiles, the current version, and incomplete policy.
Stable nodes with digests, names, versions, kinds, evidence paths, platform
bindings, resolved dependencies, propagated incomplete reasons, and topological
order; sorted missing-dependency, cycle, invalid-manifest, missing-evidence,
missing-guide, missing-registry-package, missing-metadata, missing-signature, and
missing-lockfile issues; and digests that exclude host paths make ecosystem
evidence reviewable and reproducible in CI through `pea ecosystem-pack --check`
and `ecosystem_pack_gate()`.

**Phase 100 — Certified packages and 5.0 ecosystem release** closes Wave 5 with
a deterministic delivery gate for certified packages, additive to the registry
resolution, signing, publishing, and migration-assistant surfaces. Validated
profiles control entry limits, preview inclusion, publisher signatures,
provenance attestations, conformance reports, reproducible builds, lockfiles,
registry packages, migration guides, the current version, and incomplete policy.
Stable nodes with digests, names, versions, kinds, evidence paths, platform
bindings, resolved dependencies, propagated incomplete reasons, and topological
order; sorted missing-dependency, cycle, invalid-manifest, missing-evidence,
missing-signature, missing-provenance, missing-conformance-report,
missing-reproducible-build, missing-lockfile, missing-registry-package, and
missing-migration-guide issues; and digests that exclude host paths make release
evidence reviewable and reproducible in CI through `pea certified-pack --check`
and `certified_pack_gate()`.

Wave 5 and all 100 planned phases are delivered. Public registry growth and
migration guides from Python/JS/Java/Go/Rust/SQL shipped in Phase 99; certified
packages and the 5.0 ecosystem release shipped in Phase 100. Wave 6 opens here
with Phase 101, a deterministic observability and SRE sector pack at 5.1.0,
additive to the runtime profiler and performance-gate foundations. The frozen
3.0 core, earlier component versions, and all historical release metadata remain
pinned.

**Phase 101 — Observability and SRE sector pack** adds a deterministic production
reliability gate over `*.observability.json` manifests. Validated profiles
control entry limits, preview inclusion, traces, metrics, logs, SLOs, alert
policies, incident runbooks, dashboards, the current version, and incomplete
policy. Stable nodes with digests, names, versions, kinds, evidence paths,
platform bindings, resolved dependencies, propagated incomplete reasons, and
topological order; sorted missing-dependency, cycle, invalid-manifest,
missing-evidence, missing-trace, missing-metric, missing-log, missing-SLO,
missing-alert-policy, missing-incident-runbook, and missing-dashboard issues; and
digests that exclude host paths make reliability evidence reviewable and
reproducible in CI through `pea observability-pack --check` and
`observability_pack_gate()`.

**Phase 102 — SLO enforcement and incident-response governance** extends Wave 6
with a deterministic governance gate over `*.slo.json` manifests. Validated
profiles control entry limits, preview inclusion, error budgets, incident drills,
escalation policies, postmortems, alert routes, runbooks, SLOs, the current
version, and incomplete policy. Stable nodes with digests, names, versions,
kinds, evidence paths, platform bindings, resolved dependencies, propagated
incomplete reasons, and topological order; sorted missing-dependency, cycle,
invalid-manifest, missing-evidence, missing-error-budget, missing-incident-drill,
missing-escalation-policy, missing-postmortem, missing-alert-route,
missing-runbook, and missing-SLO issues; and digests that exclude host paths make
governance evidence reviewable and reproducible in CI through
`pea slo-pack --check` and `slo_pack_gate()`.

**Phase 103 — Chaos engineering and resilience validation** extends Wave 6 with
a deterministic resilience gate over `*.chaos.json` manifests. Validated
profiles control entry limits, preview inclusion, steady states, hypotheses,
blast radii, abort conditions, rollback plans, game days, resilience reports,
the current version, and incomplete policy. Stable nodes with digests, names,
versions, kinds, evidence paths, platform bindings, resolved dependencies,
propagated incomplete reasons, and topological order; sorted
missing-dependency, cycle, invalid-manifest, missing-evidence,
missing-steady-state, missing-hypothesis, missing-blast-radius,
missing-abort-condition, missing-rollback-plan, missing-game-day, and
missing-resilience-report issues; and digests that exclude host paths make
resilience evidence reviewable and reproducible in CI through
`pea chaos-pack --check` and `chaos_pack_gate()`.

**Phase 104 — Capacity and cost reliability governance** extends Wave 6 with a
deterministic capacity gate over `*.capacity.json` manifests. Validated profiles
control entry limits, preview inclusion, cost budgets, quotas, headroom,
autoscale policies, resource limits, forecasts, review gates, the current
version, and incomplete policy. Stable nodes with digests, names, versions,
kinds, evidence paths, platform bindings, resolved dependencies, propagated
incomplete reasons, and topological order; sorted missing-dependency, cycle,
invalid-manifest, missing-evidence, missing-cost-budget, missing-quota,
missing-headroom, missing-autoscale-policy, missing-resource-limit,
missing-forecast, and missing-review-gate issues; and digests that exclude host
paths make capacity evidence reviewable and reproducible in CI through
`pea capacity-pack --check` and `capacity_pack_gate()`.

**Phase 105 — Release governance and change safety** extends Wave 6 with a
deterministic release gate over `*.release.json` manifests. Validated profiles
control entry limits, preview inclusion, change records, approvals, canary
plans, rollback plans, feature flags, audit trails, release checklists, the
current version, and incomplete policy. Stable nodes with digests, names,
versions, kinds, evidence paths, platform bindings, resolved dependencies,
propagated incomplete reasons, and topological order; sorted
missing-dependency, cycle, invalid-manifest, missing-evidence,
missing-change-record, missing-approval, missing-canary-plan,
missing-rollback-plan, missing-feature-flag, missing-audit-trail, and
missing-release-checklist issues; and digests that exclude host paths make
release evidence reviewable and reproducible in CI through
`pea release-governance --check` and `release_governance_gate()`.

**Phase 106 — Agent safety and tool-use conformance** extends Wave 7 with a deterministic agent safety and tool-use conformance gate over `*.agent.json` manifests. Validated profiles control entry limits, preview inclusion, tool policy, dry run, approval gate, replay guard, budget, audit log, isolation policy, the current version, and incomplete policy. Stable nodes with digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, propagated incomplete reasons, and topological order; sorted missing-dependency, cycle, invalid-manifest, missing-evidence, missing-tool-policy, missing-dry-run, missing-approval-gate, missing-replay-guard, missing-budget, missing-audit-log, missing-isolation-policy issues; and digests that exclude host paths make evidence reviewable and reproducible in CI through `pea agent-safety --check` and `agent_safety_gate()`.

**Phase 107 — ML and serving conformance** extends Wave 7 with a deterministic ML and serving conformance gate over `*.serving.json` manifests. Validated profiles control entry limits, preview inclusion, model contract, inference fixture, serving profile, overload test, reload test, rollback test, benchmark report, the current version, and incomplete policy. Stable nodes with digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, propagated incomplete reasons, and topological order; sorted missing-dependency, cycle, invalid-manifest, missing-evidence, missing-model-contract, missing-inference-fixture, missing-serving-profile, missing-overload-test, missing-reload-test, missing-rollback-test, missing-benchmark-report issues; and digests that exclude host paths make evidence reviewable and reproducible in CI through `pea serving-conformance --check` and `serving_conformance_gate()`.

## Sector packs

| Sector | Current PeaLang evidence | Required additions | Acceptance gate |
|---|---|---|---|
| Enterprise / Finance / Banking | `std.sql` / `pealang/sql.py`, `connectors.py`, `enterprise_connectors.py`, `cloud_connectors.py`, capability controls, lock/audit/quality CLI | Typed domain models, transaction contracts, audit DSL, JVM/SQL interop, banking reference app | Reference ledger/payments app passes conformance, audit, and dry-run deploy |
| Data Science / AI / ML | `analysis.py`, `timeseries.py`, `forecasting.py`, `ai_ml.py`, `jupyter_kernel.py`, `serving_runtime.py`, `std.analysis`, `std.stats` | Promote Preview components to stable, dataframe parity suite, R bridge, published benchmarks | Published benchmarks and a governed end-to-end ML workflow example |
| Frontend Web | `std.web`, `web_sdk.py`, `typescript-sdk`, `react-sdk`, `dashboard.py`, `browser-sdk`, WASM/CLI tooling, `serve-web` | Stable browser PEAC/WASM execution, component DSL, state model, Vite/Next integration | Real web app runs in browser with PeaLang components and TS interop |
| Mobile (Android) | Generic embedding via `host_bindings.py` / `vm_embedding.py`, Java client sidecar | Kotlin/JVM bridge, Gradle plugin, Android lifecycle bindings, sample app | Sample Android app ships with PeaLang rules compiled from Gradle |
| Mobile (iOS) | Generic embeddable runtime and host SDK story only | Swift bridge, Objective-C compatibility layer, XCFramework, Xcode templates | Sample iOS app ships with PeaLang rules compiled from Xcode |
| Game Development | Host bindings and WASM differential fixtures only | Native/WASM game runtime, ECS bindings, Unity/Unreal bridges, hot reload, input/render APIs | Playable Unity/Unreal/WASM demo with PeaLang gameplay scripts |
| Embedded / IoT / OS | `resource_limits.py`, `vm_embedding.py`, bytecode/WASM CLI, capability/sandbox foundations | No-GC native profile, C ABI, RTOS bindings, static binaries, GPIO/I2C/SPI/CAN APIs, safety audit | Firmware/OS demo runs PeaLang logic with bounded memory and signed updates |
| Cloud / DevOps | Package lifecycle CLI, `frameworks.py` scaffolds for k8s/cloudbuild/edge, `cloud_connectors.py`, `object_storage.py`, `kafka_connector.py` | Single-binary builds, Go-style concurrency, IaC DSL, Terraform/CDK bridge, lockfile-driven deploy/drift checks | PeaLang CLI deploys a cloud stack with lockfile, signed packages, and drift checks |

## Current assessment

The strongest existing foundations are **Data/AI**, **Frontend Web**, **Enterprise integration**,
and **Cloud/DevOps**. The weakest are **Android**, **iOS**, **Game Development**, and
**Embedded/IoT/OS**, which currently have embedding or scaffolding stories but not
sector-native runtimes, bindings, and reference applications.

## Build order principle

Every phase must satisfy all of these:

- small enough to land and test independently;
- preserves all existing functionality;
- updates `README.md`, `CHANGELOG.md`, and `ROADMAP.md`;
- adds tests before documentation claims success;
- improves at least one of: simple, usable, scalable, robust, secure, extendable.

## Now building

**Phase 52 — Lockfile Refresh** is complete: deterministic locks and drift
detection provide the reproducible, auditable baseline required by banking, data,
cloud, games, mobile, and embedded delivery pipelines.

**Phase 53 — Registry-Backed Resolution** is complete: cached registry metadata,
semver constraint selection, and offline resolution turn package ranges into
concrete, checksummed lockfile entries.

**Phases 54–55 — Signed Publish/Install and Reproducible Provenance** complete the
Wave 0 supply-chain baseline: publisher signatures, trusted-key rotation and
revocation, verified installs, and reproducible build evidence are now available for
regulated enterprise, finance, cloud, and embedded delivery pipelines.

**Phase 56 — Registry Namespaces and Private Packages** adds namespace ownership,
private visibility, and authorized reader lists so internal libraries can live on a
self-hosted registry without exposing names, versions, or packages to anonymous
callers.

**Phase 57 — Dependency Security Policy** adds local advisory scanning, severity
thresholds, ignored-advisory handling, and license allow/deny rules to `pea deps`,
giving regulated teams a CI-friendly gate before install, build, or deployment.

**Phase 58 — Workspaces and Multi-Package Projects** adds local member graphs,
cycle detection, deterministic build order, and workspace-wide lockfiles so large
enterprise and cloud codebases can manage many PeaLang packages as one unit.

**Phase 59 — Offline Package Cache and Air-Gapped Installs** adds a content-addressed
cache, portable bundles, and verified offline installs so regulated, embedded, and
air-gapped environments can reuse signed packages without reaching a registry.

**Phase 60 — Trusted Plugin Manifests** completes the Wave 0 trust foundation with
checksummed plugin declarations, capability allow-lists, and optional Ed25519 plugin
signatures. Hosts can enable language extensions without importing unverified code.
