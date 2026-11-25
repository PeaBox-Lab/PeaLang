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

### Wave 2 — Runtime and performance (Phases 71–80)

Bytecode optimizer, fast interpreter, JIT, native backend, WASM backend, parallel
runtime, profiler, and 4.0 performance gates.

### Wave 3 — Developer experience (Phases 81–90)

LSP v2, DAP debugger, formatter v3, linter v3, test framework v2, incremental
build system, versioned docs, migration assistants, and project templates v2.

### Wave 4 — Sector packs (Phases 91–98)

One focused pack per row of the table, each with a reference application and
conformance suite.

### Wave 5 — Ecosystem release (Phases 99–100)

Public registry growth, migration guides from Python/JS/Java/Go/Rust/SQL,
certified packages, and the 5.0 ecosystem release.

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
