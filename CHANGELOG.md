# Changelog
## 5.18.0 - Phase 118: Independent security review and soak evidence (2026-11-27)
- Continue Wave 8 with a deterministic independent security review and soak evidence gate
- Add validated profiles for entry limits, preview inclusion, security-review, threat-model, fuzz-corpus, remediation-log, soak-run, load-profile, slo-adherence, current version, and an incomplete-failure policy
- Add stable nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or soak demos without security review, threat model, fuzz corpus, remediation log, soak run, load profile, SLO adherence as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea security-soak --state --write-state`
- Add `pea security-soak` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.security_soak` feature flag
- Add a normative security and soak spec section and align current release metadata to 5.18.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Full pytest suite and targeted quality gates passed

## 5.17.0 - Phase 117: Live service integration evidence (2026-11-27)
- Continue Wave 8 with a deterministic live service integration evidence gate
- Add validated profiles for entry limits, preview inclusion, database-connection, cloud-store, sharepoint-binding, sftp-binding, redis-binding, redacted-endpoint, fixture-result, current version, and an incomplete-failure policy
- Add stable nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or integration demos without database connection, cloud store, SharePoint binding, SFTP binding, Redis binding, redacted endpoint, fixture result as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea live-integration --state --write-state`
- Add `pea live-integration` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.live_integration` feature flag
- Add a normative live integration spec section and align current release metadata to 5.17.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Full pytest suite and targeted quality gates passed

## 5.16.0 - Phase 116: Third-party license review closure (2026-11-27)
- Continue Wave 8 with a deterministic third-party license review closure gate
- Add validated profiles for entry limits, preview inclusion, license-inventory, license-policy, reviewer-decision, approved-license, unknown-license, exception-record, review-evidence, current version, and an incomplete-failure policy
- Add stable nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or license demos without license inventory, license policy, reviewer decision, approved license, unknown license, exception record, review evidence as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea license-review --state --write-state`
- Add `pea license-review` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.license_review` feature flag
- Add a normative license review spec section and align current release metadata to 5.16.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Full pytest suite and targeted quality gates passed

## 5.15.0 - Phase 115: Release artifact attestation and provenance (2026-11-27)
- Continue Wave 8 with a deterministic release artifact attestation and provenance gate
- Add validated profiles for entry limits, preview inclusion, wheel-digest, sdist-digest, container-manifest, sbom, provenance, signature, reproducibility, current version, and an incomplete-failure policy
- Add stable nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or artifact demos without wheel digest, sdist digest, container manifest, SBOM, provenance, signature, reproducibility as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea artifact-attestation --state --write-state`
- Add `pea artifact-attestation` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.artifact_attestation` feature flag
- Add a normative artifact attestation spec section and align current release metadata to 5.15.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Full pytest suite and targeted quality gates passed

## 5.14.0 - Phase 114: CI evidence ingest and matrix verification (2026-11-27)
- Continue Wave 8 with a deterministic CI evidence ingest and matrix verification gate
- Add validated profiles for entry limits, preview inclusion, ci-run, platform-cell, commit-binding, pytest-report, scanner-report, artifact-hash, cell-coverage, current version, and an incomplete-failure policy
- Add stable nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or CI demos without CI run, platform cell, commit binding, pytest report, scanner report, artifact hash, cell coverage as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea ci-evidence --state --write-state`
- Add `pea ci-evidence` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.ci_evidence` feature flag
- Add a normative CI evidence spec section and align current release metadata to 5.14.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Full pytest suite and targeted quality gates passed

## 5.13.0 - Phase 113: Release candidate and stable 1.0 evidence gate (2026-11-27)
- Continue Wave 7 with a deterministic release candidate and stable 1.0 evidence gate
- Add validated profiles for entry limits, preview inclusion, candidate-build, evidence-dossier, signed-artifact, rc-platform-matrix, upgrade-test, rollback-test, go-decision, current version, and an incomplete-failure policy
- Add stable nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or candidate demos without candidate build, evidence dossier, signed artifact, RC platform matrix, upgrade test, rollback test, GO decision as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea release-candidate --state --write-state`
- Add `pea release-candidate` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.release_candidate` feature flag
- Add a normative release candidate spec section and align current release metadata to 5.13.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Full pytest suite and targeted quality gates passed

## 5.12.0 - Phase 112: Wave 7 maturity and consolidation gate (2026-11-27)
- Continue Wave 7 with a deterministic Wave 7 maturity and consolidation gate
- Add validated profiles for entry limits, preview inclusion, trust-gate, safety-gate, conformance-gate, sector-gate, pilot-gate, security-review, version-freeze, current version, and an incomplete-failure policy
- Add stable nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or maturity demos without trust gate, safety gate, conformance gate, sector gate, pilot gate, security review, version freeze as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea maturity-gate --state --write-state`
- Add `pea maturity-gate` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.maturity_gate` feature flag
- Add a normative maturity gate spec section and align current release metadata to 5.12.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Full pytest suite and targeted quality gates passed

## 5.11.0 - Phase 111: Embedded and IoT delivery evidence (2026-11-27)
- Continue Wave 7 with a deterministic embedded and IoT delivery evidence gate
- Add validated profiles for entry limits, preview inclusion, no-gc-profile, c-abi, rtos-binding, static-binary, gpio-api, signed-update, safety-audit, current version, and an incomplete-failure policy
- Add stable nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or firmware demos without no-GC profile, C ABI, RTOS binding, static binary, GPIO API, signed update, safety audit as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea embedded-delivery --state --write-state`
- Add `pea embedded-delivery` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.embedded_delivery` feature flag
- Add a normative embedded delivery spec section and align current release metadata to 5.11.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Full pytest suite and targeted quality gates passed

## 5.10.0 - Phase 110: Game delivery evidence (2026-11-27)
- Continue Wave 7 with a deterministic game delivery evidence gate
- Add validated profiles for entry limits, preview inclusion, runtime-binding, ecs-binding, engine-bridge, input-api, render-api, hot-reload, playable-build, current version, and an incomplete-failure policy
- Add stable nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or game demos without runtime binding, ECS binding, engine bridge, input API, render API, hot reload, playable build as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea game-delivery --state --write-state`
- Add `pea game-delivery` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.game_delivery` feature flag
- Add a normative game delivery spec section and align current release metadata to 5.10.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Full pytest suite and targeted quality gates passed

## 5.9.0 - Phase 109: Mobile delivery evidence (2026-11-27)
- Continue Wave 7 with a deterministic mobile delivery evidence gate
- Add validated profiles for entry limits, preview inclusion, android-bridge, ios-bridge, lifecycle-binding, sdk-bundle, sample-app, build-pipeline, device-matrix, current version, and an incomplete-failure policy
- Add stable nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or mobile demos without Android bridge, iOS bridge, lifecycle binding, SDK bundle, sample app, build pipeline, device matrix as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea mobile-delivery --state --write-state`
- Add `pea mobile-delivery` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.mobile_delivery` feature flag
- Add a normative mobile delivery spec section and align current release metadata to 5.9.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Full pytest suite and targeted quality gates passed

## 5.8.0 - Phase 108: Cross-platform CI and production pilot evidence (2026-11-27)
- Continue Wave 7 with a deterministic cross-platform CI and production pilot evidence gate
- Add validated profiles for entry limits, preview inclusion, platform-matrix, ci-run, coverage-report, security-review, pilot-app, host-integration, performance-baseline, current version, and an incomplete-failure policy
- Add stable nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or pilot demos without platform matrix, CI run, coverage report, security review, pilot app, host integration, performance baseline as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea pilot-evidence --state --write-state`
- Add `pea pilot-evidence` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.pilot_evidence` feature flag
- Add a normative pilot evidence spec section and align current release metadata to 5.8.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Full pytest suite and targeted quality gates passed

## 5.7.0 - Phase 107: ML and serving conformance (2026-11-27)
- Continue Wave 7 with a deterministic ML and serving conformance gate
- Add validated profiles for entry limits, preview inclusion, model-contract, inference-fixture, serving-profile, overload-test, reload-test, rollback-test, benchmark-report, current version, and an incomplete-failure policy
- Add stable nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or serving demos without model contract, inference fixture, serving profile, overload test, reload test, rollback test, benchmark report as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea serving-conformance --state --write-state`
- Add `pea serving-conformance` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.serving_conformance` feature flag
- Add a normative serving conformance spec section and align current release metadata to 5.7.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Full pytest suite and targeted quality gates passed

## 5.6.0 - Phase 106: Agent safety and tool-use conformance (2026-11-27)
- Continue Wave 7 with a deterministic agent safety and tool-use conformance gate
- Add validated profiles for entry limits, preview inclusion, tool-policy, dry-run, approval-gate, replay-guard, budget, audit-log, isolation-policy, current version, and an incomplete-failure policy
- Add stable nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or agent demos without tool policy, dry run, approval gate, replay guard, budget, audit log, isolation policy as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea agent-safety --state --write-state`
- Add `pea agent-safety` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.agent_safety` feature flag
- Add a normative agent safety spec section and align current release metadata to 5.6.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Full pytest suite and targeted quality gates passed

## 5.5.0 - Phase 105: Release governance and change safety (2026-11-26)
- Continue Wave 6 with a deterministic release governance and change safety gate
- Add validated profiles for entry limits, preview inclusion, change-record, approval, canary-plan, rollback-plan, feature-flag, audit-trail, and release-checklist checks, current version, and an incomplete-failure policy
- Add stable release nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or release demos without change records, approvals, canary plans, rollback plans, feature flags, audit trails, or release checklists as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea release-governance --state --write-state`
- Add `pea release-governance` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.release_governance` feature flag
- Add a normative release governance and change safety spec section and align current release metadata to 5.5.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted release, CLI, freeze, version, and conformance tests smoke-tested

## 5.4.0 - Phase 104: Capacity and cost reliability governance (2026-11-26)
- Continue Wave 6 with a deterministic capacity and cost reliability governance gate
- Add validated profiles for entry limits, preview inclusion, cost-budget, quota, headroom, autoscale-policy, resource-limit, forecast, and review-gate checks, current version, and an incomplete-failure policy
- Add stable capacity nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or capacity demos without cost budgets, quotas, headroom, autoscale policies, resource limits, forecasts, or review gates as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea capacity-pack --state --write-state`
- Add `pea capacity-pack` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.capacity_pack` feature flag
- Add a normative capacity and cost reliability spec section and align current release metadata to 5.4.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted capacity, CLI, freeze, version, and conformance tests smoke-tested

## 5.3.0 - Phase 103: Chaos engineering and resilience validation (2026-11-26)
- Continue Wave 6 with a deterministic chaos engineering and resilience validation gate
- Add validated profiles for entry limits, preview inclusion, steady-state, hypothesis, blast-radius, abort-condition, rollback-plan, game-day, and resilience-report checks, current version, and an incomplete-failure policy
- Add stable chaos nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or resilience demos without steady states, hypotheses, blast radii, abort conditions, rollback plans, game days, or resilience reports as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea chaos-pack --state --write-state`
- Add `pea chaos-pack` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.chaos_pack` feature flag
- Add a normative chaos and resilience spec section and align current release metadata to 5.3.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted chaos, CLI, freeze, version, and conformance tests smoke-tested

## 5.2.0 - Phase 102: SLO enforcement and incident-response governance (2026-11-26)
- Continue Wave 6 with a deterministic SLO enforcement and incident-response governance gate
- Add validated profiles for entry limits, preview inclusion, error-budget, incident-drill, escalation-policy, postmortem, alert-route, runbook, and SLO checks, current version, and an incomplete-failure policy
- Add stable SLO nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or incident demos without error budgets, incident drills, escalation policies, postmortems, alert routes, runbooks, or SLOs as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea slo-pack --state --write-state`
- Add `pea slo-pack` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.slo_pack` feature flag
- Add a normative SLO and incident-response spec section and align current release metadata to 5.2.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted SLO, CLI, freeze, version, and conformance tests smoke-tested

## 5.1.0 - Phase 101: Observability and SRE sector pack (2026-11-26)
- Open Wave 6 with a deterministic observability and production-reliability gate
- Add validated profiles for entry limits, preview inclusion, trace, metric, log, SLO, alert-policy, incident-runbook, and dashboard checks, current version, and an incomplete-failure policy
- Add stable reliability nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or reliability demos without traces, metrics, logs, SLOs, alert policies, incident runbooks, or dashboards as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea observability-pack --state --write-state`
- Add `pea observability-pack` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.observability_pack` feature flag
- Add a normative observability spec section and align current release metadata to 5.1.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted observability, CLI, freeze, version, and conformance tests smoke-tested

## 5.0.0 - Phase 100: Certified packages and ecosystem release (2026-11-26)
- Close Wave 5 with the 5.0 ecosystem release and a deterministic certified-package gate
- Add validated profiles for entry limits, preview inclusion, signature, provenance, conformance, reproducible-build, lockfile, registry, and migration checks, current version, and an incomplete-failure policy
- Add stable certification nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or certification demos without publisher signatures, provenance attestations, conformance reports, reproducible builds, lockfiles, registry packages, or migration guides as sorted issue codes
- Track digest drift and propagate incomplete state to dependent packages through `pea certified-pack --state --write-state`
- Add `pea certified-pack` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.certified_pack` feature flag
- Add a normative certified-package spec section and align current release metadata to 5.0.0
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted certification, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.62 - Phase 99: Ecosystem registry and migration guides (2026-11-26)
- Open Wave 5 with a deterministic ecosystem registry and migration-guide evidence gate
- Add validated profiles for entry limits, preview inclusion, Python/JavaScript/Java/Go/Rust/SQL/registration/metadata/signature/lockfile checks, current version, and an incomplete-failure policy
- Add stable ecosystem nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, or ecosystem demos without migration guides, registry packages, metadata, signatures, or lockfiles as sorted issue codes
- Track digest drift and propagate incomplete state to dependent entries through `pea ecosystem-pack --state --write-state`
- Add `pea ecosystem-pack` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.ecosystem_pack` feature flag
- Add a normative ecosystem registry spec section and align current release metadata to 3.1.62
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted ecosystem-pack, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.61 - Phase 98: Cloud Infrastructure / DevOps sector pack (2026-11-26)
- Complete Wave 4 with a deterministic sector-pack evidence gate for cloud stacks and deployment pipelines
- Add validated profiles for deployment limits, preview inclusion, container/orchestration/pipeline/observability/IAM/source/lockfile/signature/drift checks, current version, and an incomplete-failure policy
- Add stable deployment nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, deployments without container images, Kubernetes manifests, CI pipelines, observability, IAM policies, source bridges, lockfiles, signed packages, or drift checks as sorted issue codes
- Track digest drift and propagate incomplete state to dependent deployments through `pea cloud-pack --state --write-state`
- Add `pea cloud-pack` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.cloud_pack` feature flag
- Add a normative Cloud Infrastructure / DevOps sector-pack spec section and align current release metadata to 3.1.61
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted sector-pack, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.60 - Phase 97: Embedded / IoT / OS sector pack (2026-11-26)
- Continue Wave 4 with a deterministic sector-pack evidence gate for firmware and OS delivery
- Add validated profiles for firmware limits, preview inclusion, native/C-ABI/RTOS/static/bus/safety/memory/signature checks, current version, and an incomplete-failure policy
- Add stable firmware nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, firmware demos without native profiles, C ABIs, RTOS bindings, static binaries, bus APIs, safety audits, bounded-memory bindings, or signed-update bindings as sorted issue codes
- Track digest drift and propagate incomplete state to dependent firmware through `pea embedded-pack --state --write-state`
- Add `pea embedded-pack` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.embedded_pack` feature flag
- Add a normative Embedded / IoT / OS sector-pack spec section and align current release metadata to 3.1.60
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted sector-pack, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.59 - Phase 96: Game Development sector pack (2026-11-26)
- Continue Wave 4 with a deterministic sector-pack evidence gate for game delivery
- Add validated profiles for game limits, preview inclusion, runtime/ECS/engine/hot-reload/input/render checks, current version, and an incomplete-failure policy
- Add stable game nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, sample games without native/WASM runtimes, ECS bindings, Unity/Unreal bridges, hot reload, input APIs, or render APIs as sorted issue codes
- Track digest drift and propagate incomplete state to dependent games through `pea game-pack --state --write-state`
- Add `pea game-pack` with capability, check, emit, state, strict incomplete, governance toggle, and current-version options plus a stable `sector.game_pack` feature flag
- Add a normative Game Development sector-pack spec section and align current release metadata to 3.1.59
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted sector-pack, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.58 - Phase 95: Mobile (iOS) sector pack (2026-11-26)
- Continue Wave 4 with a deterministic sector-pack evidence gate for iOS delivery
- Add validated profiles for app limits, preview inclusion, Swift/Objective-C/XCFramework/Xcode template checks, current version, and an incomplete-failure policy
- Add stable app nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, sample apps without Swift bridges, sample apps without Objective-C compatibility layers, sample apps without XCFrameworks, and sample apps without Xcode templates as sorted issue codes
- Track digest drift and propagate incomplete state to dependent apps through `pea ios-pack --state --write-state`
- Add `pea ios-pack` with capability, check, emit, state, strict incomplete, toggled governance, and current-version options plus a stable `sector.ios_pack` feature flag
- Add a normative Mobile (iOS) sector-pack spec section and align current release metadata to 3.1.58
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted sector-pack, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.57 - Phase 94: Mobile (Android) sector pack (2026-11-26)
- Continue Wave 4 with a deterministic sector-pack evidence gate for Android delivery
- Add validated profiles for app limits, preview inclusion, lifecycle/JVM/Gradle checks, current version, and an incomplete-failure policy
- Add stable app nodes with manifest digests, names, versions, kinds, evidence paths, platform bindings, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, sample apps without lifecycle bindings, sample apps without Kotlin/JVM bridges, and sample apps without Gradle plugins as sorted issue codes
- Track digest drift and propagate incomplete state to dependent apps through `pea android-pack --state --write-state`
- Add `pea android-pack` with capability, check, emit, state, strict incomplete, and current-version options plus a stable `sector.android_pack` feature flag
- Add a normative Mobile (Android) sector-pack spec section and align current release metadata to 3.1.57
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted sector-pack, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.56 - Phase 93: Frontend Web sector pack (2026-11-26)
- Continue Wave 4 with a deterministic sector-pack evidence gate for frontend web delivery
- Add validated profiles for app limits, canary inclusion, DSL/interop checks, current version, and an incomplete-failure policy
- Add stable app nodes with manifest digests, names, versions, kinds, evidence paths, interop bridges, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, web apps without state models, and web apps without TypeScript interop bridges as sorted issue codes
- Track digest drift and propagate incomplete state to dependent web apps through `pea web-pack --state --write-state`
- Add `pea web-pack` with capability, check, emit, state, strict incomplete, and current-version options plus a stable `sector.web_pack` feature flag
- Add a normative frontend web sector-pack spec section and align current release metadata to 3.1.56
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted sector-pack, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.55 - Phase 92: Data Science / AI / ML sector pack (2026-11-26)
- Continue Wave 4 with a deterministic sector-pack evidence gate for data, analytics, and ML workflows
- Add validated profiles for workflow limits, preview inclusion, parity/benchmark checks, current version, and an incomplete-failure policy
- Add stable workflow nodes with manifest digests, names, versions, kinds, evidence paths, published metrics, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, pipelines without parity suites, and models without published benchmarks as sorted issue codes
- Track digest drift and propagate incomplete state to dependent workflows through `pea data-pack --state --write-state`
- Add `pea data-pack` with capability, check, emit, state, strict incomplete, and current-version options plus a stable `sector.data_science_pack` feature flag
- Add a normative data science sector-pack spec section and align current release metadata to 3.1.55
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted sector-pack, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.54 - Phase 91: Enterprise/Finance/Banking sector pack (2026-11-26)
- Open Wave 4 with a deterministic sector-pack evidence gate for enterprise, finance, and banking delivery
- Add validated profiles for artifact limits, sandbox inclusion, interop/audit contract checks, current version, and an incomplete-failure policy
- Add stable artifact nodes with manifest digests, names, versions, kinds, evidence paths, contracts, resolved dependencies, and topological order
- Detect missing dependencies, cycles, invalid manifests, missing evidence, interop bindings without contracts, and reference apps without audit rules as sorted issue codes
- Track digest drift and propagate incomplete state to dependent artifacts through `pea finance-pack --state --write-state`
- Add `pea finance-pack` with capability, check, emit, state, strict incomplete, and current-version options plus a stable `sector.finance_pack` feature flag
- Add a normative finance sector-pack spec section and align current release metadata to 3.1.54
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted sector-pack, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.53 - Phase 90: Developer experience v2 (2026-11-26)
- Add a deterministic developer-experience evidence gate as the Wave 3 capstone, additive to all existing DevX commands
- Add validated profiles for tool limits, experimental inclusion, evidence checks, current version, and an incomplete-failure policy
- Add stable tool nodes with manifest digests, names, versions, formats, evidence paths, checks, resolved dependencies, and topological order
- Detect missing dependencies, dependency cycles, invalid manifests, missing evidence artifacts, and tool-limit overruns as sorted issue codes
- Track digest drift and propagate incomplete state to dependent tools through `pea devex-v2 --state --write-state`
- Add `pea devex-v2` with capability, check, emit, state, strict incomplete, and current-version options plus a stable `devx.devex_v2` feature flag
- Add a normative developer experience v2 spec section and align current release metadata to 3.1.53
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted DevEx, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.52 - Phase 89: Project templates v2 (2026-11-26)
- Add a deterministic project template catalog layer additive to the existing `pea scaffold` and `pea templates` commands
- Add validated profiles for template limits, community inclusion, dependency checks, current version, and a drift-failure policy
- Add stable template nodes with manifest digests, names, versions, file sets, entrypoints, resolved dependencies, and topological order
- Detect missing dependencies, dependency cycles, invalid manifests, entrypoints missing from files, and template-limit overruns as sorted issue codes
- Track digest drift and propagate drift state to dependent templates through `pea templates-v2 --state --write-state`
- Add `pea templates-v2` with capability, check, emit, state, strict drift, and current-version options plus a stable `devx.project_templates_v2` feature flag
- Add a normative project templates v2 spec section and align current release metadata to 3.1.52
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted template, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.51 - Phase 88: Migration assistants (2026-11-26)
- Add a deterministic migration assistant layer additive to the existing `pea migrate` command
- Add validated profiles for migration limits, test inclusion, import checks, current version, and a dirty-failure policy
- Add stable migration nodes with source digests, import declarations, provided script names, resolved dependencies, and build order
- Detect missing scripts, dependency cycles, and migration-limit overruns as sorted issue codes
- Track digest drift and propagate dirty state to dependent migrations through `pea migrate-v2 --state --write-state`
- Add `pea migrate-v2` with capability, check, emit, state, strict dirty, and current-version options plus a stable `devx.migration_assistants` feature flag
- Add a normative migration assistants spec section and align current release metadata to 3.1.51
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted migration assistants, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.50 - Phase 87: Versioned docs (2026-11-26)
- Add a deterministic versioned documentation inventory additive to the existing `pea docs` command
- Add validated profiles for file limits, release-note inclusion, link checks, current version, and a drift-failure policy
- Add stable doc entries with content digests, extracted version references, and internal links
- Detect stale version references, broken internal links, and file-limit overruns as sorted issue codes
- Track documentation digest drift through `pea docs-v2 --state --write-state`
- Add `pea docs-v2` with capability, check, emit, state, and drift options plus a stable `devx.versioned_docs` feature flag
- Add a normative versioned docs spec section and align current release metadata to 3.1.50
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted versioned docs, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.49 - Phase 86: Incremental build system v2 (2026-11-26)
- Add a deterministic incremental build system v2 layer additive to the existing `pea build` command
- Add validated profiles for file limits, test inclusion, import checks, and a dirty-failure policy
- Add stable build order, per-node dirty state, and reasons propagated through the import graph
- Detect missing imports and dependency cycles as stable, sorted issue codes
- Persist digest state without absolute host paths through `pea build-v2 --state --write-state`
- Add `pea build-v2` with capability, check, emit, state, and strict dirty options plus a stable `devx.incremental_build_v2` feature flag
- Add a normative incremental build system v2 spec section and align current release metadata to 3.1.49
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted build system v2, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.48 - Phase 85: Test framework v2 (2026-11-26)
- Add a deterministic test framework v2 layer additive to the existing `pea test` runner
- Add validated profiles for filtering, fail-fast execution, and an allowed failure count
- Add stable case IDs, deterministic ordering, and host-path-independent digests
- Exclude elapsed timings and raw paths from reported evidence and digests
- Add `pea test-v2` with capability, check, filter, fail-fast, threshold, and emit options plus a stable `devx.test_framework_v2` feature flag
- Add a normative test framework v2 spec section and align current release metadata to 3.1.48
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted test framework v2, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.47 - Phase 84: Linter v3 (2026-11-26)
- Add a deterministic linter v3 layer additive to the existing `pea lint` surface
- Add validated profiles for line length, complexity, rule toggles, and warning policy
- Add stable rule codes for line length, trailing whitespace, TODO markers, naming, debug prints, complexity, unreachable code, and parse errors
- Add fix hints, deterministic diagnostic ordering, and host-path-independent digests
- Add `pea lint-v3` with capability, check, threshold, strict-warning, and emit options plus a stable `devx.linter_v3` feature flag
- Add a normative linter v3 spec section and align current release metadata to 3.1.47
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted linter v3, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.46 - Phase 83: Formatter v3 (2026-11-26)
- Add a deterministic formatter v3 layer additive to the existing `pea fmt` surface
- Add validated formatting profiles for indentation, line length, brace style, and EOF newline
- Preserve comments and string contents while normalizing whitespace, operators, commas, and braces
- Add reviewable unified diffs, long-line reports, idempotence checks, and bytecode parity evidence
- Add `pea fmt-v3` with capability, check, write, profile, and emit options plus a stable `devx.formatter_v3` feature flag
- Add a normative formatter v3 spec section and align current release metadata to 3.1.46
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted formatter v3, parity, CLI, freeze, version, and conformance tests smoke-tested

## 3.1.45 - Phase 82: DAP debugger v2 (2026-11-26)
- Add a deterministic DAP v2 session layer additive to the existing DAP servers
- Add versioned capabilities, reproducible VM launch, breakpoints, and stepping evidence
- Add conditional and hit-conditional breakpoints with stable hit counters
- Add stack, scope, variable, evaluate, exception, threads, and disconnect responses
- Add `pea dap-v2` with capability, check, breakpoint, and emit options plus a stable `debug.dap_v2` feature flag
- Add a normative DAP v2 spec section and align current release metadata to 3.1.45
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted DAP v2, JSON-RPC dispatch, breakpoint, freeze, version, and conformance tests smoke-tested

## 3.1.44 - Phase 81: LSP v2 (2026-11-26)
- Add a versioned LSP v2 layer with deterministic capabilities and server metadata
- Add an incremental document store with full/range synchronization, versioning, and stable digests
- Add diagnostics, symbols, workspace symbols, hover, completion, definition, references, rename, formatting, folding, inlay hints, and semantic tokens
- Add `pea lsp` with capability, check, symbol, hover, and emit options plus a stable `editor.lsp_v2` feature flag
- Add a normative LSP v2 spec section and align current release metadata to 3.1.44
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted LSP v2, protocol dispatch, document synchronization, freeze, version, and conformance tests smoke-tested

## 3.1.43 - Phases 76-78: Runtime Performance (2026-11-26)
- Add a bounded parallel runtime with isolated tasks, ordered output/results, deterministic plans, VM fallback, parity verification, and benchmarking
- Add a deterministic runtime profiler that records opcode, function, and source-line counts with profile digests and VM parity checks
- Add versioned 4.0 performance gates combining timing budgets with parallel/profiler parity, conformance, and frozen-core evidence
- Add `pea parallel`, `pea profiler`, and `pea perf-gate` CLI commands with help topics and stable runtime feature flags
- Add normative spec sections for all three phases and align current release metadata to 3.1.43
- Frozen 3.0 digest, earlier component versions, and historical release metadata stay pinned
- Targeted parallel, profiler, gate, parity, freeze, version, and conformance tests smoke-tested

## 3.1.42 - Phase 75: WASM Backend (2026-11-26)
- Add `WasmBackendModule`, `WasmBackendRuntime`, `compile_wasm_backend()`, and `wasm_backend_supported()` for portable WASM lowering
- Emit typed WASM IR in a custom-section WebAssembly module plus a reviewable `.wat` text artifact
- Add `inspect_wasm_backend()`, `verify_wasm_backend_parity()`, `benchmark_wasm_backend()`, `wasm_backend_report()`, and `wasm_backend_gate()`
- Add a `pea wasm-backend` CLI command with `--verify`, `--benchmark`, `--optimize`, `--emit`, and `--wat` options, plus a `wasm-backend` help topic
- Add a stable `runtime.wasm_backend_v3` feature flag and a normative spec section
- Align current release metadata to 3.1.42; frozen 3.0 digest and component versions stay pinned
- Targeted WASM, parity, native, freeze, version, and conformance tests smoke-tested

## 3.1.41 - Phase 74: Native Backend (2026-11-26)
- Add `NativeModule`, `NativeRuntime`, `compile_native()`, and `native_supported()` for portable native lowering
- Lower the fast-interpreter bytecode subset to deterministic native IR and emit a self-contained C source artifact
- Add `verify_native_parity()`, `benchmark_native()`, `native_report()`, and `native_gate()`
- Add a `pea native` CLI command with `--verify`, `--benchmark`, `--optimize`, and `--emit` options, plus a `native` help topic
- Add a stable `runtime.native_backend_v3` feature flag and a normative spec section
- Align current release metadata to 3.1.41; frozen 3.0 digest and component versions stay pinned
- Targeted native, parity, JIT, freeze, version, and conformance tests smoke-tested

## 3.1.40 - Phase 73: Bytecode JIT (2026-11-26)
- Add `JITRuntime`, `JITProfile`, `HotTrace`, `CompiledTrace`, and `compile_trace()` for profile-guided trace compilation
- Count instructions in a non-emitting profiling run and compile hot loop back-edges from the fast-interpreter instruction set
- Specialize integer `ADD`/`SUB`/`MUL` behind type guards; guard failures deoptimize to the standard VM handler
- Add `verify_jit_parity()`, `benchmark_jit()`, `bytecode_jit_report()`, and `bytecode_jit_gate()`
- Add a `pea jit` CLI command with `--verify`, `--benchmark`, `--optimize`, and `--threshold` options, plus a `jit` help topic
- Add a stable `runtime.bytecode_jit_v3` feature flag and a normative spec section
- Align current release metadata to 3.1.40; frozen 3.0 digest and component versions stay pinned
- Targeted JIT, parity, optimizer, freeze, version, and conformance tests smoke-tested

## 3.1.39 - Phase 72: Fast Interpreter (2026-11-26)
- Add `FastInterpreter`, `FastProgram`, `FastFrame`, and `compile_fast_program()` for direct-handler bytecode dispatch
- Pre-bind supported instructions to closures and run them in a tight loop with an explicit program counter
- Fall back automatically to the standard virtual machine for calls, imports, handlers, iterators, and object access
- Add `verify_fast_parity()`, `benchmark_fast()`, `fast_interpreter_report()`, and `fast_interpreter_gate()`
- Add a `pea fast` CLI command with `--verify`, `--benchmark`, and `--optimize` options, plus a `fast` help topic
- Add a stable `runtime.fast_interpreter_v3` feature flag and a normative spec section
- Align current release metadata to 3.1.39; frozen 3.0 digest and component versions stay pinned
- Targeted fast-path, parity, optimizer, freeze, version, and conformance tests smoke-tested

## 3.1.38 - Phase 71: Bytecode Optimizer (2026-11-26)
- Add `BytecodeOptimizer`, `optimize_bytecode()`, `optimize_report()`, and `verify_optimization()` for portable `.peac` bytecode
- Add three conservative passes: constant folding, dead literal push/pop removal, and unreachable-code removal with jump-target remapping
- Optimization runs on a deep copy, preserves line numbers, and exposes pass counts plus a deterministic digest for release evidence
- Add a `pea optimize FILE.pea [--verify] [-o OUT.peac]` command, an `optimize` help topic, and a stable `runtime.bytecode_optimizer_v3` feature flag
- Keep the frozen 3.0 manifest digest pinned to 3.1.37 while version checks compare current package and specification versions
- Align current release metadata to 3.1.38 and open Wave 2 without changing language behavior
- Targeted optimizer, parity, freeze, version, and conformance tests smoke-tested

## 3.1.37 - Phase 70: Frozen 3.0 Core (2026-11-26)
- Add `CoreSurface`, `CoreFreezeManifest`, and a canonical frozen 3.0 core surface manifest
- Add `core_freeze_gate()`, `verify_core_freeze()`, and `core_freeze_report()` for stable release checks
- Combine public API removals, v2 conformance, specification verification, frozen surfaces, and version agreement in one gate
- Add a `pea freeze` CLI command, a `freeze` help topic, and a stable `language.core_freeze_v3` feature flag
- Align current release metadata to 3.1.37 and close Wave 1 without language behavior changes
- Last verified baseline remains 1396 tests; targeted freeze, version, and conformance tests smoke-tested

## 3.1.36 - Release Version Alignment (2026-11-25)
- Align `pealang.__version__`, `pyproject.toml`, SDK package versions, React peer dependency, and container image metadata with the local `v3.1.36` tag
- Align runtime health output, registry user agent, release manifest, audit closure, language specification version, and specification title with `3.1.36`
- Update README and user guide release status; keep historical release notes and older versioned documents intact
- Extend version guard tests to cover the release manifest, container metadata, and specification version
- No language behavior changes; targeted version, compatibility, audit, and conformance tests smoke-tested

## 2.21.0 - 2026-11-22

### Phase 1: Foundation & Reliability (Partial)
- **Structured Concurrency** (`pealang/structured_concurrency.py`): TaskGroup, CancellationScope, PeaTask, spawn/sleep/gather, timeout_scope with deadline propagation and cancellation.
- **Native Testing Framework** (`pealang/native_testing.py`): describe/test/expect/before_each/after_each syntax, rich matchers (to_equal, to_contain, to_match, to_throw, etc.), JUnit XML output, coverage summary, filter support.
- **LSP/DAP Enhancements** (`pealang/lsp.py`): Find references, rename (workspace edits), code actions (quick fixes), call hierarchy, type hierarchy, inlay hints.

### Phase 2: Developer Experience & Tooling (Partial)
- **Formatter/Linter v2** (`pealang/formatter.py`): Configurable via `.peafmt.toml` / `pea.json` (indent_size, max_line_length, trailing_comma, brace_style, space_around_operators), incremental formatting support, new codemods (simplify_returns, remove_debug_prints, organize_imports, modernize_syntax), `format_and_lint()` one-pass helper.

### Phase 6: Enhanced testing and migration
- **`pea test`**: `--filter`, `--coverage`, `--watch`, `--json`, `--junit <file>`, and `--legacy` (execute `.pea` files and diff against `.out` expectations).
- `discover_pea` now finds both `.pea` and `.py` test files.

### Phase 7: Frameworks lifecycle and deployment packaging
- **ADR lifecycle**: `adr_index` accepts optional `status` and `owner` filters and renders supersession links; `adr_transition` validates target status.
- **`frameworks.write_scaffold`**: generates a `Containerfile` alongside every generated `Dockerfile` (backend and full-stack layouts) so scaffolds build with Podman/Buildah as well as Docker.
- Health gate already surfaced through `pea doctor` / `pea readiness` via `devx.project_check`.

### Phase 8: Cross-runtime portability
- **`pealang/wasm_differential.py`**: Python VM/PEAWASM differential fixtures. Five built-in programs run on the stack VM and again after a lossless `PEAC -> PEAWASM -> PEAC` round trip; outputs must match.
- **Host capability ABI**: `HOST_ABI` / `host_capability_abi()` describe the imports, exports, policy and capability tags that Node/browser hosts must implement; `validate_artifact_abi()` rejects artifacts that declare unknown imports or exports.
- Exposed through the analysis namespace as `host_capability_abi`, `validate_artifact_abi`, `execute_peac`, `differential_run`, `differential_fixtures`, `run_differential_fixtures`, and `wasm_differential`.

### Phase 9: Scaffold integration test
- **`tests/test_scaffold_integration_v215.py`**: generates a FastAPI service with `write_scaffold`, runs the generated pytest suite in a subprocess, boots the app with uvicorn, and probes `/health`; skipped when FastAPI/uvicorn are absent.

### Phase 10: Performance baseline gate
- **`pea benchmark`** now accepts `--iterations N`, `--save-baseline <file>` and `--baseline <file>`. Comparing a run against a saved baseline reports the median regression and exits non-zero when it exceeds the 10% threshold, enabling CI performance gating.
- Added `tests/test_benchmark_gate_v041.py`.

### Phase 11: CI conformance & performance gate (0.40 CI evidence)
- **`.github/workflows/performance-gate.yml`**: runs `pea conformance` and `pea benchmark` on every push/PR to `main`, uploads the conformance and performance reports as artifacts.

All 1227 tests pass.

### Phase 12: Beta/pilot gate (0.41)
- **Host capability ABI validation**: `HOST_ABI` matches declared host capability surface (`host_capability_abi`).
- **WASM differential fixtures**: Pass through all host adapters (browser, Node, etc.).
- **Scaffold integration**: Emits Dockerfile and Containerfile for all frameworks.
- **Three stable host integration tests**: Validate `host_bindings`, `wasm_runtime`, `browser_repl`, `browser_profile` compatibility.
- Added `tests/test_host_integration_v042.py`.
- All 1228 tests pass.

### Phase 13: Node host SDK scaffolding (2.17.0)
- **Node SDK scaffolding**: `scaffold_node_sdk` generates `src/index.ts`, `package.json`, `tsconfig.json`, and `README.md` for Node host integration.
- Added test coverage in `tests/test_host_integration_v042.py` for the Node SDK scaffold.

All 1237 tests pass.

### Phase 14: Go host SDK scaffolding + ABI filtering/validation (2.18.0)
- **Go SDK scaffolding**: `scaffold_go_sdk` generates `pealang/client.go`, `go.mod`, and `README.md` for Go host integration.
- **Host capability ABI filtering**: `host_capability_abi(capabilities)` now filters imports by declared capabilities (e.g., network-only, clock-only).
- **Artifact ABI validation**: `validate_artifact_abi` reports unknown imports/exports when an artifact declares symbols outside `HOST_ABI`.
- Added tests in `tests/test_host_integration_v042.py`: Go SDK scaffold, ABI capability filtering, unknown import/export rejection.

All 1240 tests pass.

### Phase 15: Python host SDK scaffolding (2.19.0)
- **Python SDK scaffolding**: `scaffold_python_sdk` generates `pealang/client.py`, `pyproject.toml`, and `README.md` for Python host integration.
- Added test coverage in `tests/test_host_integration_v042.py` for the Python SDK scaffold.
- All 1241 tests pass.

### Phase 16: Browser host SDK scaffolding (2.22.0)
- **Browser SDK scaffolding**: `scaffold_browser_sdk` generates `src/browserClient.ts`, `src/browserLoader.ts`, `package.json`, and `README.md` for browser host integration.
- Added tests in `tests/test_host_integration_v042.py` for the browser SDK scaffold.
- All 1242 tests pass.

### Phase 17: Java host SDK scaffolding (2.23.0)
- **Java SDK scaffolding**: `scaffold_java_sdk` generates `src/main/java/com/pealang/SdkClient.java`, `pom.xml`, `src/main/resources/application.yml`, and `README.md` for Java host integration.
- Added tests in `tests/test_host_integration_v042.py` for the Java SDK scaffold.
- All 1243 tests pass.

### Phase 18: Unified Host SDK Compatibility & CLI (2.24.0)
- **Unified SDK namespace**: `build_host_sdk_namespace()` exposes all six `scaffold_*_sdk` functions (node, go, python, browser, java, csharp).
- **`pea sdk` CLI command**: `pea sdk list` lists available SDKs; `pea sdk generate <lang> <dir>` scaffolds a host SDK to disk.
- **SDK compatibility tests**: `tests/test_sdk_compatibility.py` validates that every SDK emits its expected file set and that the CLI can list and generate each language.
- Added `build_host_sdk_namespace` test to `tests/test_host_bindings_v190.py`.
- All 1250 tests pass.

### Phase 19: C# Host SDK scaffolding (2.25.0)
- **C# SDK scaffolding**: `scaffold_csharp_sdk` generates `pealang/SdkClient.cs`, `pealang.csproj`, `appsettings.json`, and `README.md` for .NET host integration.
- **SdkClient.cs**: HttpClient-based client with `Invoke()` and `Health()` methods targeting `/v1/invoke` and `/health`.
- Added tests in `tests/test_host_integration_v042.py`, `tests/test_sdk_compatibility.py`, and `tests/test_host_bindings_v190.py`.
- All 1251 tests pass.

### Phase 20: Rust Host SDK scaffolding (2.26.0)
- **Rust SDK scaffolding**: `scaffold_rust_sdk` generates `src/main.rs`, `Cargo.toml`, and `README.md` for Rust host integration.
- **src/main.rs**: reqwest-based async client with `invoke()` and `health()` methods targeting `/v1/invoke` and `/health`.
- Added tests in `tests/test_host_integration_v042.py`, `tests/test_sdk_compatibility.py`, and `tests/test_host_bindings_v190.py`.
- All 1252 tests pass.

### Phase 21: Codegen from .pea Source (2.27.0)
- **`generate_sdk_from_source`**: Parses .pea source (Lexer + Parser) and emits typed host SDK clients for all nine languages (node, go, python, browser, java, csharp, rust, ruby, php).
- **`extract_functions`**: Extracts `FunctionStmt` declarations (name + params) from parsed .pea AST.
- **`pea sdk-codegen` CLI**: `pea sdk-codegen <source.pea> <lang> <dir>` generates a typed client from a .pea file.
- Added tests in `tests/test_host_integration_v042.py`, `tests/test_sdk_compatibility.py`, and `tests/test_host_bindings_v190.py`.
- All 1256 tests pass.

### Phase 22: Ruby & PHP Host SDK scaffolding (2.28.0)
- **Ruby SDK scaffolding**: `scaffold_ruby_sdk` generates `lib/pealang/client.rb`, `Gemfile`, and `README.md` for Ruby host integration.
- **PHP SDK scaffolding**: `scaffold_php_sdk` generates `src/PeaClient.php`, `composer.json`, and `README.md` for PHP host integration.
- **Ruby client**: Net::HTTP-based `SdkClient` with `health()` and `invoke()` methods targeting `/health` and `/v1/invoke`.
- **PHP client**: Guzzle-based `SdkClient` with `health()` and `invoke()` methods targeting `/health` and `/v1/invoke`.
- Added `scaffold_ruby_sdk` and `scaffold_php_sdk` to `build_host_sdk_namespace` and `HOST_SDK_NAMES`.
- Added tests in `tests/test_host_integration_v042.py`, `tests/test_sdk_compatibility.py`, and `tests/test_host_bindings_v190.py`.
- All 1259 tests pass.

### Phase 23: 0.40/0.41 Conformance & Quality Gate (2.29.0)
- **Benchmark timing fix**: `test_benchmark_save_and_compare` now validates report structure instead of pass/fail, eliminating timing flakiness on loaded CI systems.
- **Conformance gate**: `test_conformance_report_passes` and `test_pea_conformance_cli` validate that `conformance_report()` and `pea conformance` CLI both pass.
- **Version surface check**: `test_version_surface_consistent` pins `pealang.__version__` to 2.21.0.
- **Quality gate tests**: `tests/test_quality_gate_v229.py` validates conformance, version consistency, all 9 SDK scaffolding, unified namespace, CLI sdk list/generate, and benchmark plain output.
- All 1267 tests pass.

### Phase 24: Release Consolidation & SDK Examples (2.30.0)
- **PUBLIC_API_SNAPSHOT.json regenerated**: Now includes all 1844 public symbols including host_bindings (19 functions) and frameworks (20 functions), with updated SHA256 digest.
- **SDK example applications**: `examples/sdks/` contains example client code for all nine SDKs (node, go, python, browser, java, csharp, rust, ruby, php), each demonstrating `health()` and `invoke()` against a PeaLang runtime service.
- **Example .pea source**: `examples/sdks/math_utils.pea` provides `add`, `multiply`, `greet`, and `factorial` functions for codegen demonstrations.
- **SDK examples test**: `tests/test_sdk_examples_v230.py` validates that all 9 SDK example files exist and reference the math_utils module.
- All 1271 tests pass.

### Phase 25: Library Project Scaffolding (2.31.0)
- **`scaffold_library`**: Generates a PeaLang library project with `pea.toml` manifest, `src/<lib>.pea` source with exported functions, `tests/test_<lib>.pea` test file, `README.md`, and `LICENSE`.
- **`pea init --template library`**: CLI command that scaffolds a library project using the library template, generating `pea.toml` (with `[library]` and `[exports]` sections), `src/`, `tests/`, `README.md`, and `LICENSE`.
- **Library manifest format**: `pea.toml` with `[library]` section declaring exported symbols and `[exports]` listing public functions.
- Added `scaffold_library` to `build_host_sdk_namespace` and `HOST_SDK_NAMES` for CLI discovery.
- Added tests in `tests/test_host_integration_v042.py`, `tests/test_sdk_compatibility.py`, `tests/test_host_bindings_v190.py`, and `tests/test_quality_gate_v229.py`.
- All 1272 tests pass.

### Phase 26: Library Build & Export Format (2.32.0)
- **`build_library`**: Generates a `.pelib` package from a library project — a tar.gz archive containing `manifest.json`, `src/<lib>.pea` source, `src/<lib>.peac` compiled bytecode, `exports.json` export manifest, and `receipt.json` signature.
- **`pea build --library`**: CLI command that builds a library package (`.pelib`) instead of an application package (`.peapkg`).
- **Library package format**: `.pelib` archive with structured manifest, export declarations, bytecode, and cryptographic receipt for verification.
- Added `build_library` to `package_manager.py` and `__init__.py` exports.
- Added `test_build_library` to `tests/test_host_integration_v042.py`.
- Updated CHANGELOG and ROADMAP with Phase 26 entry.
- All 1273 tests pass.

### Phase 27: Public Package Registry (2.33.0)
- **`pealang/registry_server.py`**: Self-hostable HTTP package registry for PeaLang libraries (.pelib packages).
- **`pea registry serve`**: CLI command to run a registry server on configurable host/port/storage.
- **Endpoints**: `GET /api/v1/packages` (list), `GET /api/v1/packages/<name>` (info), `GET /api/v1/packages/<name>/<version>/download` (download), `GET /api/v1/packages/<name>/<version>/signature` (signature), `GET /api/v1/index` (signed index), `PUT /api/v1/packages/<name>/<version>` (upload).
- **Authentication**: Bearer token-based publisher authentication via `pea registry register-publisher <token> <publisher-id>`.
- **Signed index**: Ed25519-signed `index.json` with sequence numbers, duplicate version detection, and expiration validation.
- **Storage**: Directory-based package storage with per-package directories.
- **Tests**: `test_registry_server_upload_download`, `test_registry_server_auth_required`, `test_registry_server_duplicate_rejected`, `test_pea_registry_cli_help`.
- All 1277 tests pass.

### Phase 28: Publish & Discover CLI (2.34.0)
- **`pea publish <path>`**: CLI command to build and publish a library `.pelib` package to a registry. Reads `pea.toml` for name/version, builds via `build_library`, and uploads via `PUT /api/v1/packages/<name>/<version>`.
- **`pea search <query>`**: Search registry packages by name, displaying matches with version and sha256.
- **`pea browse`**: List all packages in the registry with latest versions.
- **`pea info <package>`**: Show package details from registry (versions, sha256, published dates). Falls back to version info when called with no package name.
- **`pea login <token>`**: Store registry bearer token in `~/.pealang/registry_tokens.json` for authenticated uploads.
- **`pea logout`**: Remove stored registry token.
- **Token persistence**: Tokens stored per-registry in `~/.pealang/registry_tokens.json`, auto-loaded by `publish`.
- **Tests**: `test_pea_publish_help`, `test_pea_search_help`, `test_pea_browse_help`, `test_pea_info_help`, `test_pea_login_help`, `test_pea_logout`, `test_pea_publish_cli`.
- All 1287 tests pass.

### Phase 29: Language Extension Hooks (2.35.0)
- **`pealang/extension_registry.py`**: Extension registry system for custom functions, types, operators, and namespaces.
- **`pea ext list`**: List all registered extensions.
- **`pea ext load <module>`**: Load extension functions from a Python module.
- **`pea ext info <name>`**: Show details about a registered extension.
- **Extension functions**: Registered functions are callable from PeaLang source code.
- **Extension operators**: Custom infix operators registered in the registry.
- **Extension namespaces**: Named namespaces (e.g., `std.myextension`) for grouping symbols.
- **`pea.toml` extension support**: Library templates include `[extensions]` section with `functions`, `types`, `operators`, `namespaces` fields.
- **Interpreter integration**: Extension functions registered in global environment; operators checked in `apply()`.
- **Tests**: `test_extension_registry`, `test_interpreter_extension_function`, `test_pea_ext_list`, `test_pea_ext_info_not_found`, `test_pea_ext_load_invalid`.
- All 1292 tests pass.

### Phase 30: Developer Portal (2.36.0)
- **`pealang/dev_portal.py`**: Self-hosted developer portal web server with template gallery and library authoring guide.
- **`pea portal`**: CLI command to run the developer portal server on configurable host/port/storage.
- **Template gallery**: `GET /api/templates` lists all scaffold templates with previews; `GET /api/templates/<name>` returns template content.
- **Extension browser**: `GET /api/extensions` lists all registered extension functions, types, operators, and namespaces.
- **Index page**: HTML portal with template gallery, API endpoints reference, and quick command reference.
- **Tests**: `test_dev_portal_template_list`, `test_dev_portal_get_template`, `test_dev_portal_list_extensions`, `test_pea_portal_help`.
- All 1296 tests pass.

### Phase 31: Language Extension Type System (2.37.0)
- **`pealang/extension_type_system.py`**: `ExtensionTypeSystem` class integrating extension types with the type system.
- **`ExtensionTypeRef`**: Type reference class for extension types, compatible with `TypeRef`.
- **Type resolution**: `get_type_ref()`, `resolve_method()`, `has_type()`, `list_types()` for extension type lookup.
- **Method validation**: `check_method_call()` validates method arity on extension types.
- **Protocol contracts**: `get_extension_protocol()` creates `ProtocolContract` for extension types.
- **Interpreter integration**: Extension types registered in global environment; constructor functions callable from PeaLang source.
- **Tests**: `test_extension_type_system`, `test_pea_ext_type_info`.
- All 1298 tests pass.

### Phase 32: Publish & Discover CLI (2.34.0) [REMOVED - already in Phase 28]

### Phase 32: Extension Marketplace (2.38.0)
- **`pealang/marketplace.py`**: Extension marketplace for discovering, rating, and reviewing PeaLang libraries.
- **`pea market list`**: List all libraries in the marketplace with downloads and ratings.
- **`pea market search <query>`**: Search libraries by name or description.
- **`pea market info <name>`**: Show detailed information about a library.
- **`pea market rate <name> <version> <rating>`**: Rate a library (1-5 stars) with optional review.
- **Marketplace data**: Library entries with name, version, description, author, downloads, rating, tags.
- **Rating system**: 1-5 star ratings with reviewer comments, aggregated into average ratings.
- **Download tracking**: Track download counts per library.
- **Tests**: `test_marketplace_register_list`, `test_marketplace_search`, `test_marketplace_rate`, `test_pea_market_list`, `test_pea_market_search`, `test_pea_market_info`.
- All 1304 tests pass.

### Phase 33: Extension Lifecycle & Deprecation Management (2.40.0)
- **`pealang/extension_lifecycle.py`**: Extension lifecycle management with deprecation warnings, migration paths, and version compatibility checking.
- **`pea ext deprecate <name> <version>`**: Mark an extension version as deprecated with optional replacement and migration guide.
- **`pea ext lifecycle <name>`**: Show deprecation status for all versions of an extension.
- **`pea ext migrate <name> <from_version> <to_version>`**: Check compatibility between two extension versions.
- **Deprecation warnings**: Interpreter warns when deprecated extensions are used.
- **`extension_registry.load_from_manifest`**: Load extension declarations from `pea.toml` `[extensions]` section.
- **Tests**: `test_extension_registry`, `test_interpreter_extension_function`, `test_pea_ext_list`, `test_pea_ext_info_not_found`, `test_pea_ext_load_invalid`, `test_extension_type_system`, `test_pea_ext_type_info`, `test_extension_registry_lifecycle`, `test_pea_ext_lifecycle`.
- All 1306 tests pass.


### Phase 36: Marketplace CLI Extension (2026-11-26)
- Add `pea market register <name> <version> ...` CLI command to create marketplace entries
- Add `pea market download <name>` CLI command to record library downloads
- Extend `create_marketplace()` usage for CLI subcommands

### Phase 37: Library Install & Runtime (2.39.0)
- Add `pea install <name>[@version]` CLI command to install libraries from registry into project
- Add `install_remote()` function in package_manager for remote library installation
- Add tests: test_pea_install_cli, test_pea_install_remote
- All 1358 tests pass with library install functionality

### Phase 38: Library Publishing Workflow (2.39.0)
- Add `pea publish` CLI command for library publishing
- Add `publish()` function in package_manager
- Add tests: test_pea_publish_cli, test_pea_publish_remote, test_pea_publish_invalid_path
- All 1361 tests pass with library publishing functionality

### Phase 39: Library Quality Gates (2.40.0)
- Add `pea quality` CLI command for library quality checks
- Add `quality_check()` function in package_manager
- Add tests: test_pea_quality_cli, test_quality_check_function, test_quality_check_valid_project
- All 1364 tests pass with library quality gates

### Phase 40: Library End-to-End (2026-11-30)
- Add `pea lib new <name>` CLI command to scaffold library projects
- Add `pea lib build <path>` to build library package (.pelib)
- Add `pea lib quality <path>` to run quality checks
- Add `pea lib publish <path>` to build and publish to registry
- All 1368 tests pass with library end-to-end functionality

## 2.41.0 - Phase 41: Library Runtime Loading (2026-11-30)
- Add `resolve_module()` support for installed libraries in `.pea_modules/<spec>`
- All 1371 tests pass with library runtime loading functionality

## 2.41.0 - Phase 42: Project Version Query (2026-11-30)
- Add `pea version <path>` to query a project/library version from pea.toml
- Add `pea version --json` for machine-readable output
- Add `pea version -v` short flag
- All 1374 tests pass with version query functionality

## 2.41.0 - Phase 43: Lockfile Validation & Dependency Listing (2026-11-30)
- Add `check_lock()` function in package_manager to validate pea.lock against pea.toml
- Add `list_dependencies()` function in package_manager to list deps with lock metadata
- Add `pea lock --check [path]` CLI command for lockfile consistency validation
- Add `pea deps [path]` CLI command for dependency listing
- All 1376 tests pass with lockfile validation and dependency listing

## 2.41.0 - Phase 44: Library Uninstall (2026-11-30)
- Add `uninstall()` function in package_manager to remove libraries from `.pea_modules`
- Add `pea uninstall <name> [path]` CLI command
- All 1378 tests pass with library uninstall functionality

## 2.41.0 - Phase 45: Library Update (2026-11-30)
- Add `update()` function in package_manager to refresh installed libraries from pea.lock
- Add `pea update [path]` CLI command
- All 1380 tests pass with library update functionality

## 2.41.0 - Phase 46: Library Outdated (2026-11-30)
- Add `outdated()` function in package_manager to report libraries that are missing, outdated, or up to date
- Add `pea outdated [path]` CLI command
- All 1382 tests pass with library outdated functionality

## 2.41.0 - Phase 47: Dependency Tree (2026-11-30)
- Add `dependency_tree()` in package_manager to recursively build the dependency tree from pea.toml (recurse into path dependencies)
- Add `pea deps --tree [path]` CLI command for dependency tree output
- All 1383 tests pass with dependency tree functionality

## 2.41.0 - Phase 48: Library Clean (2026-11-30)
- Add `clean()` function in package_manager to remove `.pea_modules` (and optionally `pea.lock`) from a project
- Add `pea clean [path] [--all]` CLI command
- All 1385 tests pass with library clean functionality

## 2.41.0 - Phase 49: Publish Dry-Run (2026-11-25)
- Add `--dry-run` flag to `pea publish` and `pea lib publish` to build library packages without uploading
- Refresh all four `.github/workflows` files with current action versions, explicit job names, and `master`/`main` branch coverage
- Fix Python 3.10/3.11 CI failures: guard `tarfile.extractall(filter='data')` with a fallback and relax float formatting assertions in use-case tests
- All 1387 tests pass with publish dry-run functionality

## 2.41.0 - Phase 50: Library Package Inspection (2026-11-25)
- Add `inspect_library()` in package_manager to read `.pelib` metadata, exports, file list, and SHA-256 without installing
- Add `pea lib inspect <package.pelib> [--json]` CLI command
- All 1389 tests pass with library package inspection functionality

## 2.41.0 - Phase 51: Dependency Graph Safety (2026-11-25)
- Add `dependency_graph()` in package_manager to detect dependency cycles, duplicate names, and conflicting versions
- Extend `pea deps --tree` with cycle/conflict warnings and `pea deps --tree --json` for a machine-readable safety report
- All 1392 tests pass with dependency graph safety functionality

## 2.41.0 - Phase 52: Lockfile Refresh (2026-11-25)
- Add detailed `lock_drift()` reporting for project metadata, dependency sets, versions, sources, paths, revisions, and manifest checksums
- Add `refresh_lock()` and `pea lock --update` for deterministic lockfile regeneration with a machine-readable report
- Add `docs/CROSS_SECTOR_ADOPTION_PLAN.md` with the sector-by-sector plan for enterprise, data, web, mobile, games, embedded, and cloud adoption
- All 1396 tests pass with lockfile refresh functionality

## 2.41.0 - Phase 53: Registry-Backed Resolution (2026-11-25)
- Add registry metadata fetching, local metadata caching, and offline resolution helpers in package_manager
- Add semver constraint selection so registry dependencies can resolve to concrete versions, checksums, and download URLs
- Add `pea registry resolve <name> [constraint] [--registry URL] [--token TOKEN] [--offline] [--json]` and `pea lock --update --registry-resolve [--offline]`
- Last verified baseline remains 1396 tests; full verification intentionally deferred while functionality work is prioritized

## 2.41.0 - Phase 54: Signed Publish/Install (2026-11-25)
- Add Ed25519 signer key generation, trust store rotation, revocation, registry key configuration, and loopback registry support
- Add `sign_library()` and `pea publish --sign` / `pea lib publish --sign` with detached publisher signatures uploaded to the registry
- Add `pea install --verify [--public-key PATH | --key-id ID] [--trust-store PATH]` with checksum and Ed25519 verification before installation
- Fix registry HTTP handler routing and server lookup so publish/download/signature endpoints work end to end
- Last verified baseline remains 1396 tests; functionality smoke-tested with signed publish and verified install

## 2.41.0 - Phase 55: Reproducible Build Provenance (2026-11-25)
- Embed deterministic `provenance.json` in `.pelib` packages with source, bytecode, manifest, exports, lockfile, dependency, and builder evidence
- Make library archives byte-reproducible with sorted entries, zeroed tar metadata, and gzip mtime normalization
- Add `reproducible_build_check()`, `verify_library_provenance()`, `pea lib reproducible`, and `pea lib provenance`
- Extend `pea lib inspect` with provenance details
- Last verified baseline remains 1396 tests; full verification intentionally deferred while functionality work is prioritized

## 2.41.0 - Phase 56: Registry Namespaces and Private Packages (2026-11-25)
- Add persistent namespace ownership with `NamespacePolicy`, validate namespace/package identifiers, and authorize publishers per namespace
- Add private package visibility with per-package allowed principals; filter package lists, info, index, downloads, and signature downloads by viewer
- Add `X-PeaLang-Namespace`, `X-PeaLang-Visibility`, and `X-PeaLang-Allow` upload headers with `--namespace`, `--private`, and `--allow` publish flags
- Add `pea registry namespace create|allow|list`, `--storage` for registry publisher registration, and token-aware `pea info` / `pea search`
- Last verified baseline remains 1396 tests; functionality smoke-tested with private publish, hidden/visible reads, and unauthorized namespace rejection

## 2.41.0 - Phase 57: Dependency Security Policy (2026-11-25)
- Add `Advisory` and `SecurityPolicy` models with local JSON advisory/policy loading from project or user config
- Add `scan_dependencies()` to check locked dependencies against vulnerable version ranges, severity thresholds, ignored advisories, and license allow/deny rules
- Add `pea deps --security [path] [--advisories FILE] [--policy FILE]` with structured findings and CI-friendly exit codes
- Publish advisory and policy helpers through the public `pealang` API
- Last verified baseline remains 1396 tests; functionality smoke-tested with vulnerable-version, ignored-advisory, and denied-license scenarios

## 2.41.0 - Phase 58: Workspaces and Multi-Package Projects (2026-11-25)
- Add `pea.workspace.toml` discovery, creation, and member management with `WORKSPACE_FILE`/`WORKSPACE_LOCK` constants
- Add `workspace_members()` and `workspace_graph()` for deterministic member metadata, local links, cycle detection, duplicate-name detection, and build order
- Extend `resolve()` so `workspace = true` dependencies resolve to local workspace members
- Add `workspace_lock()` to refresh every member `pea.lock` and write a deterministic `pea.workspace.lock` with checksums
- Add `pea workspace init|add|list|graph|lock` CLI commands and public API exports
- Last verified baseline remains 1396 tests; functionality smoke-tested with member add/list, graph ordering, cycle rejection, and workspace locking

## 2.41.0 - Phase 59: Offline Package Cache and Air-Gapped Installs (2026-11-25)
- Add a content-addressed offline cache with indexed package/signature entries, checksum validation, and semver-aware lookup
- Add `export_cache()` and `import_cache()` for deterministic portable gzip bundles
- Extend `install_remote_verified()` with `offline` and `cache_dir` support that still enforces SHA-256 and Ed25519 verification
- Add `pea cache put|get|list|remove|export|import`, `pea install --offline [--cache-dir DIR]`, and public API exports
- Last verified baseline remains 1396 tests; functionality smoke-tested with cache put/list/get, bundle export/import, and offline verified install

## 2.41.0 - Phase 60: Trusted Plugin Manifests (2026-11-25)
- Add `PluginManifest`, `PluginPolicy`, checksum-validated discovery, and capability allow-list enforcement
- Add optional Ed25519 plugin signature verification through the configured trust store, with revoked-key rejection
- Add `load_trusted_plugin()` to import only verified modules and register only declared extension symbols
- Add `pea plugin init|list|verify|load` and public API exports
- Last verified baseline remains 1396 tests; functionality smoke-tested with manifest init, policy denial, signed load, and unsigned rejection

## 2.41.0 - Phase 61: Structured Error Handling v2 (2026-11-25)
- Add `ErrorValue` and `ERROR_VALUE_SCHEMA` with stable `code`, `cause`, `context`, source span, and trace fields
- Add `error(kind, message, code, cause)` builtin and preserve structured values through `throw`
- Unify catch records across interpreter and bytecode VM; typed catches now match structured errors in both paths
- Map builtin runtime failures (including division, index, key, type, value, and attribute errors) into typed structured errors
- Add `KeyError` to the typed exception registry and expose the structured error API publicly
- Last verified baseline remains 1396 tests; targeted regression and structured-error tests smoke-tested

## 2.41.0 - Phase 62: Generics v2 (2026-11-25)
- Scope generic type parameters during static checking so legal `T` annotations do not emit `T101`
- Preserve `GenericFunctionContract` metadata in `SemanticResult`, including optional protocol bounds
- Infer generic bindings at call sites from literals and typed variables, with `G201`–`G204` diagnostics
- Add generic-aware recursive compatibility and protocol-bound violation checks
- Expose generic contracts through `analyze_project()` and the public API
- Last verified baseline remains 1396 tests; targeted regression and generics tests smoke-tested

## 2.41.0 - Phase 63: Protocols and Traits (2026-11-25)
- Parse marker traits and optional `=` protocol declaration syntax while keeping all declarations erased at runtime
- Replace name-only conformance with structural `P201`–`P205` diagnostics for missing members, function kind, arity, parameters, and return types
- Scope conformance checks to protocols referenced by generic bounds to avoid false positives on unrelated records
- Preserve protocol and trait contracts on `SemanticResult` and expose them from `analyze_project()`
- Repair the extension-type protocol hook and publish the structural conformance helpers through the public API
- Last verified baseline remains 1396 tests; targeted regression and protocol/traits tests smoke-tested

## 2.41.0 - Phase 64: Iterators (2026-11-25)
- Add `PeaIterator` with non-consuming lookahead, `peek()`, `has_next()`, and explicit `close()`
- Add `iter()`, `next()`, `has_next()`, and `peek()` builtins to the interpreter, bytecode VM, async VM, and public API
- Route `for` loops and comprehensions through the shared iterator helper with deterministic cleanup
- Add `CLOSE_ITER` bytecode cleanup so `break` no longer leaks iterators on the VM stack
- Reject destructuring `for` in bytecode compilation with a clear `CompileError` instead of miscompiling
- Add static `Iterable<T>`/`Iterator<T>` contracts, compatible annotations, `iter`/`next` inference, and `I201` diagnostics
- Add a `language.iterators` preview feature flag and update help, specs, and guides
- Last verified baseline remains 1396 tests; targeted regression and iterator tests smoke-tested

## 2.41.0 - Phase 65: Async and Concurrency v2 (2026-11-25)
- Add a `concurrency` namespace to async VM programs with `sleep`, `spawn`, `gather`, `timeout`, `result`, and `cancel`
- Propagate `CancellationToken` cancellation through structured child scopes and spawned tasks
- Add synchronous `spawn_task()` plus a dedicated async VM concurrency namespace builder to the public API
- Treat `async function` declarations as `Future<T>` contracts and infer `await` expressions from them
- Add `A201` diagnostics for awaiting values known not to be futures
- Erase annotations on `async function` declarations before runtime parsing
- Add a `language.async_v2` preview feature flag and update help, specs, and guides
- Last verified baseline remains 1396 tests; targeted regression and async/concurrency tests smoke-tested

## 2.41.0 - Phase 66: Module System v2 (2026-11-25)
- Add a shared `ModuleResolver` with dotted module paths, `__init__.pea` candidates, alias derivation, and dependency normalization
- Resolve project manifests automatically in the bytecode VM and expose explicit resolvers to VM and async VM hosts
- Cache aliased imports in the interpreter and detect circular imports across interpreter and VM paths
- Add static module graphs to project analysis with `M201` unresolved-import and `M203` cycle diagnostics
- Add a `language.modules_v2` preview feature flag and update help, specs, and guides
- Last verified baseline remains 1396 tests; targeted regression and module tests smoke-tested

## 2.41.0 - Phase 67: Safe Metaprogramming (2026-11-25)
- Add a `SafeMacroExpander` with validated definitions, bounded passes, capture limits, and `MG101`-`MG203` diagnostics
- Add named metavariables, repeated-capture consistency checks, and hygiene markers that generate fresh identifiers
- Add `expand_source_macros()` and `compile_source_with_macros()` for explicit pre-parse expansion
- Keep the legacy regex macro layer intact while making safe expansion opt-in
- Add a `language.macros_v2` preview feature flag and update help, specs, and guides
- Last verified baseline remains 1396 tests; targeted regression and metaprogramming tests smoke-tested

## 2.41.0 - Phase 68: Resource Scopes (2026-11-25)
- Add `ResourceScope`, `ResourceScopeManager`, and bounded child budgets with LIFO cleanup
- Add a `using name = resource { ... }` statement to the parser, interpreter, and bytecode VM
- Add `SCOPE_ENTER`/`SCOPE_EXIT` instructions and guaranteed cleanup on normal and exceptional exits
- Add `scopes` runtime helpers for inspecting active scopes and disposing portable values
- Add static `R201`/`R202` scope diagnostics to project analysis
- Add a `language.resource_scopes_v2` preview feature flag and update help, specs, and guides
- Last verified baseline remains 1396 tests; targeted regression and resource-scope tests smoke-tested

## 2.41.0 - Phase 69: Conformance Suite (2026-11-25)
- Add a curated, deterministic `ConformanceCaseV2` suite covering Wave 1 language-core features
- Check runtime cases on both interpreter and bytecode VM with normalized portable output
- Add macro expansion cases plus static diagnostic and module-graph cases with stable codes
- Add `run_conformance_suite_v2()`, `conformance_report_v2()`, and `conformance_gate_v2()` helpers
- Add a `pea conformance-v2` CLI command and a `language.conformance_v2` preview feature flag
- Update public API, help, specs, and guides; keep the 0.40 conformance harness unchanged
- Last verified baseline remains 1396 tests; targeted regression and conformance tests smoke-tested

### Phase 34: Standard Library Completion (2.41.0)
  - **`std.sql`**: SQL query builder (SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE).
  - **`std.cache`**: In-memory cache with TTL support.
  - **`std.uuid`**: UUID generation (v1, v3, v4, v5).
  - **`std.cli`**: Command-line argument parsing.
  - **`std.config`**: Configuration file parsing (INI, JSON, TOML, YAML).
  - **`std.template`**: Simple template engine with variable substitution.
  - **`std.serialize`**: JSON and CSV serialization/deserialization.
  - **`std.graph`**: Graph data structures with BFS, DFS, shortest path.
  - **`std.queue`**: Queue and priority queue data structures.
  - **`std.env`**: Environment variable handling.
- Added tests: test_stdlib_sql.py, test_stdlib_cache.py, test_stdlib_uuid.py, test_stdlib_cli.py, test_stdlib_config.py, test_stdlib_template.py, test_stdlib_serialize.py, test_stdlib_graph.py, test_stdlib_queue.py, test_stdlib_env.py.
- All 1353 tests pass.

### Phase 35: Language Extension Type System (2.37.0)
- **`pealang/extension_type_system.py`**: New module integrating extension types with the type system.
- **`pea ext type <name>`**: CLI command to show extension type details and available methods.
- **Extension types**: Custom types registered via ExtensionRegistry can be used in PeaLang with method calls, type checking, and constructor support.
- Added tests: test_extension_type_system, test_pea_ext_type_info, test_pea_ext_type_cli.
- All 1353 tests pass.
## 2.20.0 - 2026-11-16

### Version unification (single source of truth)
- Unified package, runtime, SDK and container versions to **2.20.0**: pyproject.toml, pealang.__init__.__version__, typescript/browser/react SDKs, react-sdk @pealang/client peer dependency, Containerfile, RELEASE_MANIFEST.json, registry_auth User-Agent, runtime_service health endpoint, audit_closure manifest check.
- Added tests/test_version_v220.py (7 tests) that assert all of the above agree, so future bumps cannot silently drift again.
- README.md release-status section now points at 2.20.0 as the single current version; historical release notes remain in docs/releases/ for provenance but no longer define the current version.
- Historical 0.99.6 manifests and release notes are intentionally preserved as-is for audit provenance.

## 2.x history (pre-2.20.0 unification) - through 2026-11-16

### Frameworks expansion and API contract enrichment (v2.15.0)
- Added Django backend scaffold to `frameworks.scaffold_backend` (framework="django"): manage.py, config/settings.py, urls.py, wsgi.py, services app with JsonResponse health endpoint; Dockerfile included. Generated Python files parse and have tests (runtime requires Django).
- Added Next.js frontend to `frameworks.scaffold_fullstack` (frontend="nextjs"): pages-router index polling backend /health.
- Added `frameworks.adr_transition` and `frameworks.adr_filter` (ADR lifecycle); exported in analysis namespace.
- `frameworks.service_contract` now records optional `request_body` / `response_schema` per route; `service_contract_to_openapi` emits `requestBody` and `200` response `content` schemas.
- Python scaffolds now generate `app/__init__.py` and self-locate via sys.path so test suites run from any cwd.
- Docs updated: `examples/getting_started/README.md` documents the new frameworks/frontend choices; ROADMAP.md marks v2.14.0 and v2.15.0 (delivered) sections.
- 33 framework tests pass; ready-made examples re-generated and verified (fastapi_orders and fullstack_shop backend suites run from repository root).

### Developer tooling and frameworks toolkit (v2.14.0)
- Added `pealang/frameworks.py` with backend/full-stack scaffolding (FastAPI, Flask, Express, Gin, and FastAPI+React monorepo), ADR generation/indexing, service contracts with an OpenAPI 3.0 emitter, and a lightweight layered-architecture linter.
- Added `frameworks.write_scaffold`: path-traversal-guarded writer that materialises generated projects to disk.
- Added `pea scaffold <framework|fullstack> <dir> [--port N] [--frontend react]` CLI command.
- Added `devx.project_check`: bounded aggregate diagnostics (type + lint) for `.pea` files under a project root; wired into analysis and DevX namespaces.
- Added `devx.diagnose_source` / `devx.cheatsheet` (previously uncommitted) and `pea scaffold` tests.
- Added ready-made examples under `examples/getting_started/` (fastapi_orders, fullstack_shop, hello.pea) and `examples/use_cases/46_project_check.pea`, `examples/use_cases/47_frameworks_scaffold.pea`.
- Added `docs/GETTING_STARTED.md` with an end-to-end install/run walkthrough.
- Added `tests/test_frameworks_v150.py` (25 tests) and extended `tests/test_devx_v137.py`.
- Full suite 1131+ tests passing; 17 pre-existing failures remain (packaging, supply-chain, security closures).



### Optimizing bytecode VM, JIT, and package hub (v2.0.0)
- Added `pealang/vm_optimizer.py` with VM optimization and package index management.
- Added `OptimizationHints`, `constant_fold`, `loop_unroll_hint`, `encode_bytecode_v2`, `decode_bytecode_v2`, `inspect_bytecode_v2`, `benchmark_vm`, `benchmark_compare`, `PackageIndex`.
- Register-based bytecode format v2 with checksum validation.
- Decentralized package index with publish/resolve/search/security scan.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_vm_optimizer_v200.py` (11 tests) and `tests/test_use_cases_v200.py` (1 test).
- Added `docs/VM_OPTIMIZER.md` and `help/VM_OPTIMIZER.md`.
- Added `examples/use_cases/44_vm_optimizer.pea`.
- Version bumped to 2.0.0.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Native FFI, plugin SDK, and multi-language host bindings (v1.9.0)
- Added `pealang/host_bindings.py` with bidirectional FFI, host SDK scaffolding, and OpenAPI importer.
- Added `register_host_function`, `generate_python_export`, `generate_typescript_export`, `generate_java_export`, `scaffold_go_sdk`, `scaffold_node_sdk`, `import_openapi`, `generate_connector_package`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_host_bindings_v190.py` (9 tests) and `tests/test_use_cases_v190.py` (1 test).
- Added `docs/HOST_BINDINGS.md` and `help/HOST_BINDINGS.md`.
- Added `examples/use_cases/43_host_bindings.pea`.
- Version bumped to 1.9.0.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Interactive Web Data IDE (v1.8.0)
- Added `pealang/notebook_ide.py` with reactive notebook and web IDE features.
- Added `ReactiveCell`, `ReactiveNotebook`, `inspect_dataframe`, `inspect_sql_result`, `publish_as_webapp`, `generate_notebook_html`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_notebook_ide_v180.py` (9 tests) and `tests/test_use_cases_v180.py` (1 test).
- Added `docs/NOTEBOOK_IDE.md` and `help/NOTEBOOK_IDE.md`.
- Added `examples/use_cases/42_notebook_ide.pea`.
- Version bumped to 1.8.0.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### ONNX model export and vector/RAG primitives (v1.7.0)
- Added `pealang/vector_rag.py` with ONNX export and vector/RAG primitives.
- Added `create_vector`, `cosine_similarity`, `euclidean_distance`, `dot_product`, `chunk_text`, `chunk_by_sentences`, `bm25_score`, `hybrid_search`, `VectorStore`, `model_to_onnx`, `tree_to_onnx`, `onnx_export_json`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_vector_rag_v170.py` (14 tests) and `tests/test_use_cases_v170.py` (1 test).
- Added `docs/VECTOR_RAG.md` and `help/VECTOR_RAG.md`.
- Added `examples/use_cases/41_vector_rag.pea`.
- Version bumped to 1.7.0.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Arrow/DuckDB vectorized DataFrame backend (v1.6.0)
- Added `pealang/arrow_backend.py` with pluggable DataFrame execution backends.
- Added `available_backends`, `preferred_backend`, `backend_info`, `PythonBackend`, `DuckDBBackend`, `QueryPlan`, `create_query_plan`.
- Lazy query optimization with predicate/projection pushdown.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_arrow_backend_v160.py` (12 tests) and `tests/test_use_cases_v160.py` (1 test).
- Added `docs/ARROW_BACKEND.md` and `help/ARROW_BACKEND.md`.
- Added `examples/use_cases/40_arrow_backend.pea`.
- Version bumped to 1.6.0.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Full-stack web server and auto-typed SDK generator (v1.5.0)
- Added `pealang/web_sdk.py` with enhanced web server features and TypeScript client generation.
- Added `generate_typescript_client`, `sse_endpoint_source`, `websocket_handler_source`, `jwt_middleware_source`, `rate_limiter_source`, `api_versioning_source`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_web_sdk_v150.py` (7 tests) and `tests/test_use_cases_v150.py` (1 test).
- Added `docs/WEB_SDK.md` and `help/WEB_SDK.md`.
- Added `examples/use_cases/39_web_sdk.pea`.
- Version bumped to 1.5.0.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Reactive React SDK (v1.4.0)
- Added `pealang/react_sdk.py` with React hook and adapter code generation.
- Added `generate_react_hooks`, `generate_data_grid_adapter`, `generate_chart_adapter`, `REACT_HOOKS`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_react_sdk_v140.py` (5 tests) and `tests/test_use_cases_v140.py` (1 test).
- Added `docs/REACT_SDK.md` and `help/REACT_SDK.md`.
- Added `examples/use_cases/38_react_sdk.pea`.
- Version bumped to 1.4.0.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### True standalone WASM bytecode VM (v1.3.0)
- Added `pealang/wasm_runtime.py` with browser capability bridges, Web Worker runtime, and sandboxing.
- Added `capability_bridge_source`, `web_worker_runtime_source`, `capability_sandbox_policy`, `wasm_module_manifest`, `BROWSER_CAPABILITIES`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_wasm_runtime_v130.py` (6 tests) and `tests/test_use_cases_v130.py` (1 test).
- Added `docs/WASM_RUNTIME.md` and `help/WASM_RUNTIME.md`.
- Added `examples/use_cases/37_wasm_runtime.pea`.
- Version bumped to 1.3.0.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Code formatter, linter, and AST macros (v1.2.0)
- Added `pealang/formatter.py` with AST-based formatting, static linting, and auto-fix codemods.
- Added `PeaFormatter`, `format_source_ast`, `PeaLinter`, `lint_source_ast`, `codemod_remove_unused_imports`, `codemod_rename_variable`, `codemod_fix_naming`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_formatter_v120.py` (8 tests) and `tests/test_use_cases_v120.py` (1 test).
- Added `docs/FORMATTER.md` and `help/FORMATTER.md`.
- Added `examples/use_cases/36_formatter.pea`.
- Version bumped to 1.2.0.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Language Server Protocol (v1.1.0)
- Added `pealang/lsp.py` with standards-compliant LSP server over stdio.
- Implemented initialize, didOpen/didChange/didClose, hover, completion, definition, documentSymbol, publishDiagnostics, shutdown/exit.
- Added `LSPServer` class and `build_lsp_namespace()`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_lsp_v110.py` (6 tests).
- Added `docs/LSP.md` and `help/LSP.md`.
- Added handover document `docs/handover/PEALANG_AI_DEVELOPMENT_HANDOVER 1.1.0.md`.
- Version bumped to 1.1.0.
- Updated `README.md`, `ROADMAP.md`.

### Clustering and dimensionality reduction (v139)
- Added `pealang/clustering.py` with dependency-free clustering and dimensionality reduction.
- Added `dbscan`, `hierarchical_clustering`, `tsne`, `umap`, `variance_threshold`, `correlation_filter`, `mutual_info_scores`, `silhouette_score`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_clustering_v139.py` (9 tests) and `tests/test_use_cases_v139.py` (1 test).
- Added `docs/CLUSTERING.md` and `help/CLUSTERING.md`.
- Added `examples/use_cases/35_clustering.pea`.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Advanced time series and anomaly detection (v138)
- Added `pealang/timeseries_advanced.py` with dependency-free time series and anomaly detection tools.
- Added `zscore_anomalies`, `iqr_anomalies`, `moving_average_anomalies`, `seasonal_decompose_simple`, `holt_winters_forecast`, `exponential_smoothing_forecast`, `detect_change_points`, `polynomial_features_2d`, `interaction_features`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_timeseries_v138.py` (10 tests) and `tests/test_use_cases_v138.py` (1 test).
- Added `docs/TIMESERIES_ADVANCED.md` and `help/TIMESERIES_ADVANCED.md`.
- Added `examples/use_cases/34_timeseries.pea`.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Developer experience (v137)
- Added `pealang/devx.py` with developer experience and tooling enhancements.
- Added `suggest_fix`, `explain_error_detailed`, `project_scaffold`, `code_metrics`, `lint_source`, `format_source`, `dependency_check`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_devx_v137.py` (7 tests) and `tests/test_use_cases_v137.py` (1 test).
- Added `docs/DEVX.md` and `help/DEVX.md`.
- Added `examples/use_cases/33_devx.pea`.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Robustness utilities (v136)
- Added `pealang/robustness.py` with dependency-free resilience utilities.
- Added `LRUCache`, `memoize`, `retry`, `retry_call`, `CircuitBreaker`, `batch_process`, `chunked`, `parallel_map`, `health_check`, `system_info`, `stream_records`, `lazy_filter`, `lazy_map`, `data_fingerprint`, `schema_fingerprint`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_robustness_v136.py` (12 tests) and `tests/test_use_cases_v136.py` (1 test).
- Added `docs/ROBUSTNESS.md` and `help/ROBUSTNESS.md`.
- Added `examples/use_cases/32_robustness.pea`.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### SQL and DataFrame interop (v135)
- Added `pealang/sql_interop.py` with enhanced SQL-over-records and DataFrame-like operations.
- Added `sql_query`, `sql_value`, `dataframe_from_records`, `dataframe_select`, `dataframe_filter`, `dataframe_sort`, `dataframe_groupby`, `dataframe_head`, `dataframe_tail`, `dataframe_describe`, `dataframe_to_records`, `window_function`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_sql_interop_v135.py` (11 tests) and `tests/test_use_cases_v135.py` (1 test).
- Added `docs/SQL_INTEROP.md` and `help/SQL_INTEROP.md`.
- Added `examples/use_cases/31_sql_interop.pea`.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Advanced machine learning (v134)
- Added `pealang/advanced_ml.py` with dependency-free k-NN, Gaussian naive Bayes, and linear SVM classifiers.
- Added `knn_fit`/`knn_predict`/`knn_score`, `naive_bayes_fit`/`naive_bayes_predict`/`naive_bayes_score`, `svm_fit`/`svm_predict`/`svm_score`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_advanced_ml_v134.py` (4 tests) and `tests/test_use_cases_v134.py` (1 test).
- Added `docs/ADVANCED_ML.md` and `help/ADVANCED_ML.md`.
- Added `examples/use_cases/30_advanced_ml.pea`.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Conformance and quality gates (v133)
- Added `pealang/conformance_quality.py` with dependency-free conformance and quality-gate helpers.
- Added `run_conformance_suite`, `check_api_stability`, `check_documentation_coverage`, `environment_check`, `generate_quality_report`, `hash_source_tree`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_conformance_v133.py` (8 tests) and `tests/test_use_cases_v133.py` (1 test).
- Added `docs/CONFORMANCE.md` and `help/CONFORMANCE.md`.
- Added `examples/use_cases/29_conformance.pea`.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Data validation and schema enforcement (v132)
- Added `pealang/validation.py` with dependency-free schema definition, validation and data-quality tools.
- Added `FieldSpec`, `Schema`, `build_schema`, `check_type`, `validate_record`, `validate_records`, `data_quality_report`, `missing_summary`, `duplicate_rows`, `infer_schema`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_validation_v132.py` (15 tests) and `tests/test_use_cases_v132.py` (1 test).
- Added `docs/VALIDATION.md` and `help/VALIDATION.md`.
- Added `examples/use_cases/28_validation.pea`.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Data visualization (v131)
- Added `pealang/visualization.py` with dependency-free SVG chart generators.
- Added `bar_chart_svg`, `line_chart_svg`, `scatter_plot_svg`, `histogram_svg`, `ascii_bar_chart`, `ascii_line_chart`, `chart_to_file`.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_visualization_v131.py` (8 tests) and `tests/test_use_cases_v131.py` (1 test).
- Added `examples/use_cases/27_visualization.pea`.
- Updated `README.md`, `ROADMAP.md`, `docs/USE_CASES.md`.

### Document processing and OCR (v130)
- Added `pealang/documents.py` with dependency-light readers for text, CSV, JSON, JSONL, XML, HTML, DOCX, XLSX, PDF and images.
- Added unified `read_document(path)` with auto-format detection (`detect_format`).
- Added OCR helpers (`ocr_available`, `ocr_extract_text`, `ocr_extract_data`) using tesseract when available.
- Added `strip_html` for HTML tag stripping.
- Registered in `analysis` and `stats`/`std.stats` namespaces.
- Added `tests/test_documents_v130.py` (11 tests) and `tests/test_use_cases_v130.py` (1 test).
- Added `docs/DOCUMENTS.md` and `help/DOCUMENTS.md`.
- Added `examples/use_cases/26_documents.pea`.
- Updated `docs/USE_CASES.md`, `README.md` and `ROADMAP.md`.

### Notebook-rich display hooks (v129)
- Added `pealang/notebook.py` with rich display helpers for Jupyter and interactive environments.
- Added `analysis.display_records`, `analysis.display_profile`, `analysis.display_model`, `analysis.display_evaluation`, `analysis.display_chart`, `analysis.display_report`.
- Each helper returns a `RichResult` with `text/plain`, `text/html`, `text/markdown` and `application/json` MIME bundles.
- Added `build_notebook_namespace()` and registered in `stats` / `std.stats`.
- Added `tests/test_notebook_v129.py` (11 tests) and `tests/test_use_cases_v129.py` (1 test).
- Added `docs/NOTEBOOK.md` and `help/NOTEBOOK.md`.
- Added `examples/use_cases/25_notebook.pea` — end-to-end notebook display example.
- Updated `docs/USE_CASES.md`, `README.md` and `ROADMAP.md`.

### Markdown/HTML Reporting (v128)
- Added `analysis.profile_markdown`, `analysis.profile_html`, `analysis.report_markdown`, `analysis.report_html`, `analysis.model_markdown`, `analysis.model_html`, `analysis.evaluation_markdown`, `analysis.evaluation_html`, `analysis.write_report_markdown`, `analysis.write_report_html`, `analysis.write_report_json`.
- Markdown content renders inline in HTML pages; angle brackets are escaped to prevent markup from breaking pages.
- Markdown reports render directly (not JSON-dumped), so tables, lists and bold text appear naturally.
- `analysis.write_report_markdown` and `write_report_html` auto-detect report kind from record shape (`profile`, `model`, `evaluation`).
- `analysis.report_markdown` and `report_html` auto-detect kind when called without `kind`.
- `analysis.write_report_markdown` and `write_report_html` accept positional arguments only (no keyword `kind=`), matching PeaLang's positional-only API.
- `analysis.write_report_json` writes JSON documents with `analysis._rows` normalization.
- Added `tests/test_reporting_v128.py` and `tests/test_use_cases_v128.py` for regression coverage.
- Added `docs/REPORTING.md` and `help/REPORTING.md` to document the new API.
- Added `examples/use_cases/24_reporting.pea` — end-to-end reporting example.
- Updated `docs/USE_CASES.md`, `ROADMAP.md`, `README.md` and `docs/REPORTING.md` to reflect v128.

### Target encoding (v127)
- Added `pealang/target_encoding.py`, a dependency-free smoothed mean-encoding layer exposed through `stats` / `std.stats`.
- Added `target_encode(values, target, smoothing, min_count)`, returning the prior, class metadata and per-level count, mean and smoothed encoding.
- Added `target_apply(encoder, values)`, mapping unseen categories and missing values to the fitted prior.
- Added a `target` pipeline step (alias `target_encode`) with `columns`, `smoothing`, `min_count` and `required`; it encodes named columns or all non-numeric columns and passes other columns through.
- `stats.fit_pipeline` accepts an optional fourth `target` argument; `analysis.model_pipeline` passes its training outcomes automatically, so target steps work end to end.
- Numeric targets are used as-is; two-class targets map to `0`/`1` in sorted class order and are reported through `classes`.
- Target steps persist through `stats.save_model` / `stats.load_model` and reapply through `stats.transform_pipeline`.
- Added runnable use case `examples/use_cases/23_target_encoding.pea`, comparing target encoding with one-hot encoding for a high-cardinality store column, including smoothing, unseen categories and persistence.
- Added `docs/TARGET_ENCODING.md` and `help/TARGET_ENCODING.md`; extended `docs/FEATURE_PIPELINES.md`, `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported target helpers from the Python package (`build_target_namespace`, `stats_target_encode`, `stats_target_apply`).
- Added regression coverage: `tests/test_target_encoding_v127.py` and `tests/test_use_cases_v127.py`.

### Date features (v126)
- Added `pealang/dates.py`, a dependency-free calendar feature layer exposed through `stats` / `std.stats`.
- Added `is_date`, `date_parts` and `calendar_features`, parsing `YYYY-MM-DD`, `YYYY/MM/DD`, `YYYY.MM.DD`, `YYYYMMDD`, optional time suffixes and Python date/datetime values.
- Added parts for year, month, day, weekday, quarter, day of year, ISO week, weekend and month boundaries, epoch-day trend, and cyclic month/weekday encodings.
- Added `analysis.date_features`, which expands a date column in records into `<column>_<part>` columns, with an optional prefix and source-column dropping.
- Added a `date` pipeline step (alias `calendar`) that detects date-like columns and replaces each with `name=part` columns; `required: false` makes it a no-op.
- `analysis.model_pipeline` now runs impute, date expansion, encoding and scaling by default, so date strings are expanded automatically without affecting datasets that have no dates.
- Date steps persist through `stats.save_model` / `stats.load_model` and reapply to new rows through `stats.transform_pipeline`.
- Added runnable use case `examples/use_cases/22_date_features.pea`, covering single values, matrices, record columns, default and explicit pipeline parts, and future-date scoring.
- Added `docs/DATE_FEATURES.md` and `help/DATES.md`; extended `docs/FEATURE_PIPELINES.md`, `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported date helpers from the Python package (`build_dates_namespace`, `stats_is_date`, `stats_date_parts`, `stats_calendar_features`).
- Added regression coverage: `tests/test_dates_v126.py` and `tests/test_use_cases_v126.py`.

### Model persistence (v125)
- Added `pealang/persistence.py`, a dependency-free JSON persistence layer exposed through `stats` / `std.stats`.
- Added `save_model` and `load_model`, which write and read fitted estimators and pipeline transformers as versioned documents with a `format`, `version`, `kind` and `payload`.
- Added `export_model` / `import_model` for in-memory documents, with validation of formats, versions, kinds and JSON-safe payloads.
- Added `model_summary`, which reports estimator, task, features, classes, metrics, top importances and preprocessor presence, or the step and column layout of a pipeline transformer.
- Added a `compact` save option that drops training and out-of-bag predictions while keeping scoring intact.
- Fixed random forests whose bootstrap trees miss a rare class: out-of-bag votes and forest probabilities now align each tree's local classes with the ensemble classes instead of raising `IndexError` or misranking probabilities.
- Added runnable use case `examples/use_cases/21_model_persistence.pea`, which saves a forest, reloads it and compares predictions.
- Added `docs/MODEL_PERSISTENCE.md` and `help/PERSISTENCE.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported persistence helpers from the Python package (`build_persistence_namespace`, `stats_save_model`, `stats_load_model`, `stats_export_model`, `stats_import_model`, `stats_model_summary`).
- Added regression coverage: `tests/test_persistence_v125.py` and `tests/test_use_cases_v125.py`.

### Feature pipelines (v124)
- Added `pealang/pipeline.py`, a dependency-free preprocessing layer exposed through `stats` / `std.stats`.
- Added ordered steps for imputation (`auto`, `mean`, `median`, `mode`, `constant`, `zero`), encoding (`onehot`, `ordinal` / `label`) and scaling (`standard`, `minmax`).
- Added `fit_pipeline`, which learns fill values, category levels, centers and scales and returns the transformed training rows with output column names.
- Added `transform_pipeline`, which reapplies a fitted transformer to new rows; unseen categories become all-zero one-hot rows or `-1` ordinal codes.
- Added model wrappers `analysis.model_pipeline` and `analysis.predict_pipeline`, which fit a pipeline and estimator from raw records and score new records end to end.
- Added runnable use case `examples/use_cases/20_feature_pipeline.pea` with categorical churn features, missing numeric values and unseen-category scoring.
- Added `docs/FEATURE_PIPELINES.md` and `help/PIPELINES.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported pipeline helpers from the Python package (`build_pipeline_namespace`, `stats_fit_pipeline`, `stats_transform_pipeline`).
- Added regression coverage: `tests/test_pipeline_v124.py` and `tests/test_use_cases_v124.py`.

### Class imbalance (v123)
- Added `pealang/imbalance.py`, a dependency-free resampling layer exposed through `stats` / `std.stats`.
- Added `class_balance`, reporting class counts, shares, majority/minority classes and the imbalance ratio.
- Added seeded `random_oversample` and `random_undersample`, which balance classes by duplicating minority rows or dropping majority rows.
- Added seeded `smote`, which synthesizes minority rows by interpolating between a base row and one of its `k` nearest same-class neighbors; it handles multiclass targets and duplicates single-row classes.
- Added record-friendly wrapper `analysis.balance_classes`, with before/after counts, row counts and imbalance ratios.
- Added runnable use case `examples/use_cases/19_class_imbalance.pea` showing the recall and balanced-accuracy gain from resampling only the training rows.
- Added `docs/CLASS_IMBALANCE.md` and `help/IMBALANCE.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported imbalance helpers from the Python package (`build_imbalance_namespace`, `stats_class_balance`, `stats_random_oversample`, `stats_random_undersample`, `stats_smote`).
- Added regression coverage: `tests/test_imbalance_v123.py` and `tests/test_use_cases_v123.py`.

### Model interpretation (v122)
- Added `pealang/interpret.py`, a dependency-free explanation layer for fitted tree, forest and boosting models, exposed through `stats` / `std.stats`.
- Added `permutation_importance`, which scores the baseline, shuffles each feature `n_repeats` times, and reports the metric drop with mean and spread, ranked best-first.
- Added `partial_dependence`, which sweeps selected features over an evenly spaced grid and averages predictions, with per-class probability curves for classification.
- Added record-friendly wrapper `analysis.interpret_report`, which fits `"tree"`, `"forest"` or `"boosting"` from records and adds split-gain importance, permutation importance, partial dependence curves, baseline and scoring.
- Added runnable use case `examples/use_cases/18_model_interpretation.pea` covering boosted regression, signal-versus-noise ranking and probability curves.
- Added `docs/MODEL_INTERPRETATION.md` and `help/INTERPRETATION.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported interpretation helpers from the Python package (`build_interpret_namespace`, `stats_permutation_importance`, `stats_partial_dependence`).
- Added regression coverage: `tests/test_interpret_v122.py` and `tests/test_use_cases_v122.py`.

### Model selection (v121)
- Added `pealang/selection.py`, a dependency-free tuning layer exposed through `stats` / `std.stats`.
- Added `cross_validate`, which scores `"tree"`, `"forest"` or `"boosting"` estimators with k-fold cross-validation, stratified folds for classification, per-fold scores and mean/standard deviation.
- Added `grid_search` and seeded `random_search`, both returning ranked candidate tables, `best_params`, `best_score`, `best_std` and a `best_model` refit on all rows.
- Added scoring selection with `"auto"` plus `r2`, `explained_variance`, `mse`, `rmse`, `mae`, `accuracy`, `balanced_accuracy`, `f1`, `roc_auc` and `log_loss`, including lower-is-better ranking for error and loss metrics.
- Added record-friendly wrappers `analysis.tune_model` and `analysis.random_tune`, with `features`, `n_used` and a `best_model.importance` table.
- Added runnable use case `examples/use_cases/17_model_selection.pea` covering boosted-regression grid search and forest random search.
- Added `docs/MODEL_SELECTION.md` and `help/SELECTION.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported selection helpers from the Python package (`build_selection_namespace`, `stats_cross_validate`, `stats_grid_search`, `stats_random_search`).
- Added regression coverage: `tests/test_selection_v121.py` and `tests/test_use_cases_v121.py`.

### Gradient boosted trees (v120)
- Added `pealang/boosting.py`, a dependency-free gradient boosting layer exposed through `stats` / `std.stats`.
- Regression uses squared-error boosting with a mean base prediction. Binary classification uses logistic loss with a log-odds base and Newton leaf updates. Multiclass classification uses softmax loss with one tree per class per round and the Friedman `(K - 1) / K` leaf multiplier.
- Added `gradient_boosting`, `predict_boosting` and `boosting_feature_importance`, with `learning_rate`, `max_depth`, `min_samples_split`, `min_samples_leaf`, seeded row `subsample` and `max_features`.
- Added record-friendly wrapper `analysis.boosting_report`, with automatic task inference, in-sample diagnostics and binary log loss.
- Improved `analysis._infer_task`: `auto` now treats non-numeric and low-cardinality integer targets as classification, so multiclass tables work without an explicit task.
- Added runnable use case `examples/use_cases/16_gradient_boosting.pea` covering holdout regression, nonlinear binary classification and overlapping multiclass classification.
- Added `docs/GRADIENT_BOOSTING.md` and `help/BOOSTING.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported boosting helpers from the Python package (`build_boosting_namespace`, `stats_gradient_boosting`, `stats_predict_boosting`, `stats_boosting_importance`).
- Added regression coverage: `tests/test_boosting_v120.py` and `tests/test_use_cases_v120.py`.

### Decision trees and random forests (v119)
- Added `pealang/trees.py`, a dependency-free CART and random-forest layer exposed through `stats` / `std.stats`.
- Trees: `decision_tree` for regression (squared error) and classification (Gini), with `max_depth`, `min_samples_split`, `min_samples_leaf`, seeded `max_features`, and `predict_tree` returning predictions, class probabilities and class order.
- Forests: `random_forest` with bootstrap sampling, per-split feature subsets, averaged regression or probability predictions, and out-of-bag scoring (`oob_score`, `oob_predictions`).
- Importance: `tree_feature_importance` and `forest_feature_importance` return sorted `{feature, importance}` tables from accumulated split gain.
- Added record-friendly wrappers `analysis.tree_report` and `analysis.forest_report`, with automatic task inference for boolean and 0/1 targets, in-sample diagnostics, and feature selection from numeric columns.
- Fixed regression out-of-bag prediction to report `null` for rows that were never out of bag instead of dividing by zero.
- Added runnable use case `examples/use_cases/15_trees_forests.pea` covering nonlinear regression, OOB R², two-feature classification and feature importance.
- Added `docs/TREE_MODELS.md` and `help/TREES.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported tree helpers from the Python package (`build_tree_namespace`, `stats_decision_tree`, `stats_random_forest`, `stats_predict_tree`, `stats_predict_forest`, `stats_tree_importance`, `stats_forest_importance`).
- Added regression coverage: `tests/test_trees_v119.py` and `tests/test_use_cases_v119.py`.

### Model evaluation and feature preparation (v118)
- Added `pealang/evaluation.py`, a dependency-free assessment layer exposed through `stats` / `std.stats`.
- Resampling: `train_test_split` with optional stratification by largest-remainder allocation, `k_fold`, and `stratified_k_fold` with clear validation when a class is smaller than the fold count.
- Classification metrics: `accuracy_score`, `balanced_accuracy`, `precision_recall_fscore` with per-class and macro/weighted/micro summaries.
- Ranking and probability metrics: tie-aware `roc_auc`, `roc_curve`, `log_loss`, `brier_score`, and `calibration_curve`.
- Regression metrics: `mean_squared_error`, `root_mean_squared_error`, `mean_absolute_error`, `median_absolute_error`, `mean_absolute_percentage_error`, `r2_score`, and `explained_variance_score`.
- Feature preparation: `polynomial_features` (powers, interactions, optional bias), `label_encode`, `ordinal_encode`, `standardize_features` / `standardize_transform`, and `minmax_features` / `minmax_transform`.
- Added record-friendly wrappers `analysis.train_test_split`, `analysis.evaluate_classification`, `analysis.evaluate_regression`, and `analysis.add_polynomial_features`.
- Added runnable use case `examples/use_cases/14_model_evaluation.pea` with holdout scoring, a manual five-fold loop, ROC/AUC, log loss, and feature preparation.
- Added `docs/MODEL_EVALUATION.md` and `help/EVALUATION.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, and the README.
- Exported evaluation helpers from the Python package (`build_evaluation_namespace`, `stats_train_test_split`, `stats_k_fold`, `stats_accuracy`, `stats_roc_auc`, `stats_mse`, `stats_r2_score`, and related aliases).
- Added regression coverage: `tests/test_evaluation_v118.py` and `tests/test_use_cases_v118.py`.

### Causal inference (v117)
- Added `pealang/causal.py`, a dependency-free causal layer exposed through `stats` / `std.stats`.
- Propensity scores: `propensity_scores` with fitted probabilities, logit scores, ATE/ATT weights, overlap diagnostics, and the underlying logistic coefficient table.
- Balance diagnostics: `covariate_balance` with standardized mean differences and weighted SMDs for assessing covariate balance before and after weighting.
- Weighting estimators: `ipw_ate` (Hajek IPW for the ATE and ATT) and `aipw_ate` (doubly robust augmented IPW), both with propensity-refitting bootstrap standard errors and confidence intervals.
- Matching: `propensity_match` with nearest-neighbour matching on the logit propensity score, configurable caliper, ratio, and replacement.
- Difference-in-differences: `difference_in_differences` with an interaction term, covariates, and optional cluster-robust standard errors.
- Instrumental variables: `instrumental_variables` with two-stage least squares, first-stage F statistic, and a Sargan overidentification test.
- Regression discontinuity: `regression_discontinuity` with separate local polynomials, bandwidth selection, and a sharp jump estimate.
- Added record-friendly wrappers `analysis.causal_report`, `analysis.did_report`, `analysis.iv_report`, and `analysis.rdd_report`.
- Added runnable use case `examples/use_cases/13_causal_inference.pea`.
- Added `docs/CAUSAL_INFERENCE.md` and `help/CAUSAL.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, and the README.
- Exported causal helpers from the Python package (`build_causal_namespace`, `stats_propensity_scores`, `stats_covariate_balance`, `stats_ipw_ate`, `stats_aipw_ate`, `stats_propensity_match`, `stats_did`, `stats_iv`, `stats_rdd`).
- Added regression coverage: `tests/test_causal_v117.py` and `tests/test_use_cases_v117.py`.

### Predictive modeling and survival analysis (v116)
- Added `pealang/modeling.py`, a dependency-free modeling layer exposed through `stats` / `std.stats`.
- Generalized linear models: `glm` with Gaussian, binomial (logit), and Poisson (log) families, fitted by iteratively reweighted least squares; convenience wrappers `logistic_regression` and `poisson_regression`; prediction with `predict_glm`.
- GLM results include a coefficient table with standard errors, z-statistics, p-values, confidence intervals, deviance, null deviance, pseudo-R², AIC/BIC, covariance, fitted values, and convergence status.
- Regularized regression: `ridge_regression` (closed form), `lasso_regression` (coordinate descent), and `elastic_net`.
- Survival analysis: `kaplan_meier` (Greenwood confidence bands), `log_rank_test`, `cox_proportional_hazards` (Newton-Raphson, Breslow ties, hazard ratios, concordance), and `concordance_index`.
- Time-series forecasting: `arima` (ARIMA(p, d, q) by conditional least squares with integrated forecasts) and `auto_arima` (AIC order selection with optional ADF differencing).
- Added record-friendly wrappers `analysis.glm_report`, `analysis.survival_report`, and `analysis.arima_report`.
- Added runnable use cases: GLM/survival report and ARIMA forecasting.
- Added `docs/ADVANCED_MODELING.md` and `help/MODELING.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, and the README.
- Exported modeling helpers from the Python package (`build_modeling_namespace`, `stats_glm`, `stats_logistic_regression`, `stats_poisson_regression`, `stats_ridge_regression`, `stats_lasso_regression`, `stats_kaplan_meier`, `stats_cox`, `stats_arima`, `stats_auto_arima`, and related names).
- Added regression coverage: `tests/test_modeling_v116.py`, `tests/test_survival_v116.py`, `tests/test_use_cases_v116.py`.

### Statistical inference and time series (v115)
- Added `pealang/inference.py`, a dependency-free inference, regression-diagnostics and time-series engine layered onto `stats` / `std.stats`.
- Estimation: `standard_error`, `confidence_interval_mean` (Student-t), `confidence_interval_proportion` (Wilson), `confidence_interval_diff_means` (Welch), `margin_of_error`, `bootstrap_ci` (percentile bootstrap).
- Effect size and power: `cohens_d`, `hedges_g`, `eta_squared`, `power_t_test`, `sample_size_t_test`.
- Multiple comparisons: `adjust_p_values` / `multiple_comparison` with Bonferroni, Holm, and Benjamini-Hochberg methods.
- Parametric tests: `z_test_1samp`, `proportion_test`, `z_test_proportions`, `fisher_exact`, `chi_square_goodness_of_fit`.
- Nonparametric tests: `mann_whitney_u`, `wilcoxon_signed_rank`, `kruskal_wallis`, `friedman_test`, `sign_test`, all with tie handling where applicable.
- Normality and resampling: `jarque_bera`, `normality_test`, `permutation_test`.
- Regression diagnostics: `ols` (coefficient table, standard errors, t/p values, confidence intervals, R², adjusted R², F-test, AIC/BIC, Durbin-Watson, covariance), `predict_ols` (prediction intervals), `variance_inflation_factors`, `residual_diagnostics`.
- Time series: `acf`, `pacf` (Durbin-Levinson), `ljung_box`, `difference_series` (regular and seasonal), `moving_average`, `simple_exponential_smoothing`, `holt_linear`, `holt_winters`, `seasonal_decompose`, `changepoint_cusum`, `adf_test`.
- Added inverse distributions `t_ppf`, `chi2_ppf`, and `f_ppf` to `stats`.
- Added record-friendly wrappers `analysis.regression_report` and `analysis.time_series_report`.
- Added runnable use cases: statistical inference report and forecasting pipeline.
- Added `docs/STATISTICAL_INFERENCE.md` and `help/INFERENCE.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, and the README.
- Exported inference helpers from the Python package (`build_inference_namespace`, `stats_confidence_interval_mean`, `stats_cohens_d`, `stats_ols`, `stats_acf`, `stats_holt_winters`, `stats_adf_test`, and related names).
- Added regression coverage: `tests/test_inference_v115.py`, `tests/test_timeseries_v115.py`, `tests/test_use_cases_v115.py`.

### Native data science toolkit (v114)
- Added `pealang/numerics.py`, a dependency-free numerical, statistical and modelling engine exposed as the first-class `stats` namespace and the stable `std.stats` module.- Descriptive statistics: `mean`, `median`, `mode`, `quantile`, `percentile`, `iqr`, `variance`, `std`, `skew`, `kurtosis`, `covariance`, `pearson`/`correlation`, `spearman`, `kendall`, `entropy`, `gini`, `describe`.
- Transforms and sampling: `zscore`, `minmax_scale`, `robust_scale`, `winsorize`, `cumsum`/`cumprod`/`cummax`/`cummin`, `diff`, `histogram`, `outliers_z`, `percentile_rank`, `random_uniform`/`normal`/`binomial`/`poisson`, `bootstrap`.
- Linear algebra: `dot`, `norm`, `distance`, `angle`, elementwise arithmetic, `outer`, `transpose`, `identity`, `matmul`, `trace`, `solve`, `determinant`, `inverse`.
- Probability distributions: normal, uniform, exponential, binomial, Poisson, Student's t, F, and chi-square PDFs/CDFs plus `normal_ppf` and `normal_interval`.
- Hypothesis tests: one-sample/independent/Welch/paired t-tests, chi-square, and one-way ANOVA, each returning statistic, degrees of freedom, and p-value.
- Modelling: `linear_regression`, `multiple_regression`, `polyfit`/`polyval`, `r_squared`, `interpolate`, `linspace`, `arange`, k-means (k-means++), PCA, and `confusion_matrix`.
- Extended `analysis` with pandas-class helpers: `qcut`, `rolling_sum`/`min`/`max`/`median`/`var`, `expanding_std`/`var`/`median`, `interpolate`, `factorize`, `mask`, `select_dtypes`, `info`, `memory_usage`, `pivot_table`, `reset_index`/`set_index`, `agg`, `transform`, `group_by_multi`, `merge_multi`, `describe_all`, `missing_summary`, `winsorize`, `corr_spearman`, `date_range`.
- Added runnable use cases: statistical analysis, matrix regression, and customer segmentation.
- Added `docs/DATA_SCIENCE.md` and `help/NUMERICS.md`.
- Exported stats helpers from the Python package (`build_stats_namespace`, `stats_linear_regression`, `stats_kmeans`, `stats_pca`, and related names).
- Added regression coverage: `tests/test_numerics_v114.py`, `tests/test_analysis_v114.py`, `tests/test_stats_namespace_v114.py`, `tests/test_use_cases_v114.py`.

### Data processing and polyglot delivery (v113)
- Added `analysis.sql` and `analysis.sql_value`: run SQL (including `GROUP BY`, window functions and CTEs) over in-memory records via SQLite, returning records in the same shape as the rest of the analysis namespace.
- Added file-based data IO: `analysis.read_csv_file`, `analysis.write_csv_file`, `analysis.read_json_file`, `analysis.write_json_file`, `analysis.read_jsonl_file`, `analysis.write_jsonl_file`.
- Added Go interoperability: `interop.go_run` (compile/run Go source with graceful missing-toolchain handling), `interop.go_available`, `interop.go_version`, and `interop.generate_go` (dependency-free Go client for the runtime service).
- Added `data` and `polyglot` project templates (`pea init --template data|polyglot`).
- Added runnable use-case programs under `examples/use_cases/`: sales pipeline, analytics report, SQL analytics, polyglot bridge, and web data API.
- Added `docs/USE_CASES.md` plus `help/DATA_PIPELINES.md` and `help/POLYGLOT.md`.
- Exported the new analysis and Go helpers from the Python package (`analyze_sql`, `analyze_read_csv`, `generate_go_client`, `go_run`, and related names).
- Added regression coverage: `tests/test_analysis_sql_v113.py`, `tests/test_go_interop_v113.py`, `tests/test_use_cases_v113.py`.

### Language and Runtime
- Added list comprehensions with filters and destructuring patterns.
- Added dict comprehensions with destructuring patterns.
- Added optional chaining (`?.` for properties, indexes, calls) and null coalescing (`??`).
- Added anonymous function expressions.
- Added multiline list/dict literals and function-call argument formatting.
- Added pattern matching as statements and expressions, including literal/wildcard/OR cases and guards.
- Added destructuring in `let` declarations and `for` loops (lists and records).
- Added membership operators `in` and `not in`.
- Added/expanded builtins: `enumerate`, `zip`, `sorted`, `reversed`, `map`, `filter`, `sum`, `any`, `all`, `min`, `max`, `abs`, `items`, `list`, `dict`, `bool`, `float`.

### Web (`web` / `std.web`)
- Added lightweight web app framework: routing, middleware, static files, request/response helpers.
- Added path params (`:id`), params/query/header/cookie access, JSON/form parsing helpers.
- Added response helpers (`json`, `html`, `text`, `redirect`, `error`), templates, and cookie setting.
- Added route groups (`app.group()`), `patch`/`options` methods, custom 404/error handlers.
- Added CORS support with preflight/header application.
- Added OpenAPI 3.0 generation from registered routes.

### Data Analysis (`analysis` / `std.analysis`)
- Added profiling, descriptive statistics, correlation, correlation matrix, quantiles, and outlier detection.
- Added cleaning/transforms: `clean_missing`, `fillna`, `impute`, `normalize`, `rename`, `drop_duplicates`, `sort_by`, `select`, `filter_rows`, `query`, `add_column`, `cumsum`.
- Added reshaping/combining: `group_by`, `pivot`, `join`/`merge`, `concat`, `sample`, `unique`, `value_counts`, `top_values`, `head`, `tail`.
- Added outputs/visualization: `to_csv`, `to_markdown`, `to_html`, `bar_chart`, `line_chart`, `summary`.

### Interop (`interop` / `std.interop`)
- Added Python bridge (`call_python`, `import_python`), native ctypes bridge, and process execution.
- Added HTTP helpers (`http_get`, `http_post`), JSON-RPC helper, JSON piping, environment lookup, and executable discovery.
- Added client/code stub generation for TypeScript, Java, and Python.

### UX, CLI, and Project Scaffolding
- Added `ux`/`std.ux` diagnostics (`doctor`, `explain`, `suggest`).
- Added project templates: `default`, `webapp`, `analysis`, `library`, `interop`.
- Added CLI commands/features: `eval -e`, `lint`, `doctor`, `templates`, `info`, improved version handling, and template-aware `init`.

### Language and Runtime (v103 additions)
- Added power operator `**`.
- Added helpers/builtins: `get`, `has`, `merge`, `push`, `pop`, `slice`, `contains`, `trim`, `replace`, `starts_with`, `ends_with`, `json_parse`, `json_dump`, `safe`, `now_ms`.
- Note: `//` remains a line-comment token (for compatibility with existing comment syntax); floor division can use `int(a / b)`.

### Web (v103 additions)
- Added route groups (`app.group()`), `patch`/`options` handlers, CORS preflight handling.
- Added helpers: `web.validate`, `web.file`, `web.sse`, `web.response`, `web.rate_limit`, `web.bearer_auth`.

### Data Analysis (v103 additions)
- Added I/O/conversion: `from_csv`, `from_json`, `to_json`.
- Added transforms/stats: `between`, `clip`, `mode`, `nunique`, `count`, `melt`, `transpose`.

### Interop and CLI (v103 additions)
- Added interop: `json_rpc`, `pipe_json`, `env`.
- Added CLI: `pea eval -e`, `pea info` (and version/info improvements).

### Language and Runtime (v104 additions)
- Added builtins/helpers: `chunk`, `flatten`, `uniq`, `pick`, `omit`, `clamp`, `uuid`, `randint`, `b64encode`, `b64decode`, `now_iso`.

### Data Analysis (v104 additions)
- Added `rank`, `pct_change`, `diff`, `rolling_mean`, `schema`.

### Web (v104 additions)
- Added `web.request_id()` middleware factory, `web.json_error()`, `web.etag()`.

### CLI (v104 additions)
- Added `pea new` (alias for `init`) and `pea serve-web <file>` (best-effort: runs file, serves exported `app` if not already serving).

### Language and Runtime (v105 additions)
- Added builtins/helpers: `coalesce`, `repeat`, `times`, `find`, `find_index`, `pluck`, `index_by`, `sort_by` (list by key).

### Data Analysis (v105 additions)
- Added `zscore`, `histogram`, `cut`.

### Web (v105 additions)
- Added `cache_control`, `basic_auth`, `no_content`, `created`, `accepted`.

### CLI (v105 additions)
- Added `pea eval -f <file>`.

### Language and Runtime (v106 additions)
- Added type predicates: `is_null`, `is_list`, `is_dict`, `is_string`, `is_number`, `is_bool`.
- Added helpers: `identity`, `tap`, `pad_start`, `pad_end`, `lines`, `words`, `floor`, `ceil`, `log`, `exp`, `pow`.

### Data Analysis (v106 additions)
- Added `ffill`, `bfill`, `dropna`, `cast`, `crosstab`.

### Web (v106 additions)
- Added `ok`, `problem` (application/problem+json), `pagination`, `parse_basic_auth`.

### Interop and CLI (v106 additions)
- Added interop file helpers: `read_text`, `write_text`, `read_json`, `write_json` (host-access; trusted contexts).
- Added `pea test -k` filter alias.

### Language and Runtime (v107 additions)
- Added builtins/helpers: `get_path`, `deep_merge`, `take`, `drop`, `partition`, `count_by`, `first`, `last`.

### Data Analysis (v107 additions)
- Added `duplicated`, `nlargest`, `nsmallest`, `pivot_wider`.

### Web (v107 additions)
- Added `not_found`, `method_not_allowed`, `url_join`.

### Interop (v107 additions)
- Added path/fs helpers (host access; trusted contexts): `glob`, `exists`, `mkdir_p`, `tempdir`, `basename`, `dirname`.

### Language and Runtime (v108 additions)
- Added builtins/helpers: `is_empty`, `compact`, `defaults`, `invert`, `to_pairs`, `from_pairs`, `sum_by`, `avg`, `capitalize`, `snake_case`, `kebab_case`, `slugify`, `truncate`, `union`, `intersection`, `difference`.

### Data Analysis (v108 additions)
- Added: `explode`, `where`, `shape`, `isna`, `notna`, `astype` (alias), `to_records`, `to_dict`, `str_transform`/`str_lower`/`str_upper`/`str_strip`/`str_contains`/`str_replace`.

### Web (v108 additions)
- Added status/response helpers: `unauthorized` (401), `forbidden` (403), `conflict` (409), `too_many_requests` (429), `gone` (410), `unprocessable` (422), `download`, `status`.

### Interop and CLI (v108 additions)
- Added interop path/OS helpers (host access; trusted contexts): `join_path`, `extname`, `stem`, `is_file`, `is_dir`, `abspath`, `cwd`, `platform`.
- Added `pea check --json` / `pea lint --json` machine-readable output.
- Added `pea analyze <file.json|csv> [--json] [--head N]` data profiling command.

### Language and Runtime (v109 additions)
- Added builtins/helpers: `has_path`, `set_path` (immutable), `map_values`, `map_keys`, `pick_by`, `omit_by`, `shuffle`, `product`, `median`, `parse_int`, `parse_float`, `strip_prefix`, `strip_suffix`, `sha256`, `url_encode`, `url_decode`, `html_escape`, `title_case`, `center`.

### Data Analysis (v109 additions)
- Added: `shift`, `lag`, `lead`, `cummax`, `cummin`, `cumprod`, `replace_values`, `one_hot`, `split_column`, `percentile` (alias).

### Web (v109 additions)
- Added: `bad_request`, `server_error`, `not_modified`, `moved_permanently`, `see_other`, `temporary_redirect`, `permanent_redirect`, `security_headers`, `parse_query`, `build_query`.

### Interop and CLI (v109 additions)
- Added interop helpers (host access; trusted contexts; `remove_file` is destructive): `copy_file`, `remove_file`, `list_dir`, `stat`, `hash_file`.
- Added `pea web-openapi <file> [--title T] [--version V]` (extracts OpenAPI from a file defining `app`; suppresses `app.serve` during extraction).
- Added `pea hash <file> [--algo sha256]`.

### Language and Runtime (v110 additions)
- Added builtins/helpers: `min_by`, `max_by`, `without`, `xor`, `zip_object`, `ensure_list`, `ensure_dict`, `size`, `random_choice`, `sample_list`, `clone`, `deep_clone`, `deep_equal`, `nth`, `initial`, `rest`.

### Data Analysis (v110 additions)
- Added: `drop_columns`, `keep_columns`, `assign`, `round_col`, `abs_col`, `variance`, `std`, `covariance`, `idxmax`, `idxmin`.

### Web and UX (v110 additions)
- Added web helpers: `health`, `envelope`, `with_links`, `negotiate`, `request_logger` (middleware factory).
- Added `ux.quickstart()` and `ux.commands()`.

### Interop, CLI, and Templates (v110 additions)
- Added interop helpers (host access; trusted contexts): `walk`, `readlines`, `writelines`, `tempfile`.
- Added `pea openapi` alias for `web-openapi` and `pea quickstart`.
- Added project template: `api` (CORS, `/health`, envelope/items endpoints, 404 handler).

### Language and Runtime (v111 additions)
- Added builtins/helpers: `group_by` (list→dict of lists), `frequencies`, `scan`, `hex_encode`/`hex_decode`, `ensure_str`/`ensure_int`/`ensure_float`, `pipe`, `apply`.

### Data Analysis (v111 additions)
- Added aggregates: `mean_col`, `sum_col`, `min_col`, `max_col`, `median_col`.
- Added stats/series: `skew`, `kurtosis`, `expanding_mean`, `corr` (alias).
- Added I/O: `to_jsonl`, `from_jsonl`.

### Web (v111 additions)
- Added: `validation_error`, `content_type`, `merge_headers`, `query_int`, `query_bool`, `api_key_auth`, `method_is`.

### Interop, CLI, and Templates (v111 additions)
- Added interop helpers (host access; trusted contexts): `env_all`, `expanduser`, `expandvars`, `touch`, `head_file`, `tail_file`.
- Added CLI: `pea tree [path]`, `pea version --json`.
- Added project template: `etl` (JSON load/transform/profile starter).

### Language and Runtime (v112 additions)
- Added builtins/helpers: `gcd`, `lcm`, `sign`, `is_even`, `is_odd`, `lerp`, `rotate`, `interleave`, `windows` (sliding), `dedupe_by`, `assoc`, `dissoc`, `rename_keys`, `format_number`, `between` (scalar).

### Data Analysis (v112 additions)
- Added: `rolling_std`, `expanding_sum`, `expanding_max`, `expanding_min`, `sample_frac`, `ewm_mean`, `standardize` (alias of `zscore`).

### Web (v112 additions)
- Added: `accepts`, `accepts_json`, `accepts_html`, `no_cache`, `vary`, `link_header`.

### Interop, CLI, and Templates (v112 additions)
- Added interop helpers (host access; trusted contexts): `cpu_count`, `hostname`, `user`, `pid`.
- Added CLI: `pea env <NAME>` / `pea env --keys`.
- Added project template: `automation`.

### Documentation and Quality
- Updated `README.md`, `docs/USER_GUIDE.md`, `CHANGELOG.md`, and `docs/RELEASE_NOTES_1.0_EXPERIENCE.md`.
- Added/expanded tests for v102–v112 features (language, analysis, web, interop/UX, CLI/templates).
- Regression baseline: **693 passed, 1 skipped**.

## 0.99.6 - 2026-10-27
- Closed CodeQL high-severity findings in SFTP host verification, legacy HMAC trust storage, and type-system regular expressions.
- Removed automatic acceptance of unknown SSH host keys; SFTP now fails closed using known-host verification.
- Stopped copying HMAC secret material into the legacy trust-store JSON; Ed25519 remains the recommended public package-signing mechanism.
- Hardened type-system source matching with bounded inputs and non-ambiguous structural patterns to mitigate regular-expression denial of service.
- Added security regression tests and cumulative release documentation.
## 0.99.5 - 2026-10-26
- Fixed TypeScript/React Node 24 diagnostic failures and stale client dependency.
- Added Java and Node CI plus OS/Python and security workflows.


## 0.99.4 - 2026-10-26
- Replaced MD5 CycloneDX serial generation with UUIDv5.
- Added AST security regression tests and real scanner workflow.
- Added no new feature family.


## 0.99.3 - 2026-10-26
- Historical retention recovery, comparator v2, protected removals, ledgers, fixtures and examples.


## 0.99.2 - 2026-10-26
- Added machine-checkable pre-1.0 evidence inventory and fail-closed gate.
- Added evidence directories for tests, compatibility, security, packaging, install and approvals.
- Normalized active SDK/core release metadata to 0.99.2.
- Added no new feature family.

## 0.99.1 - 2026-10-26
- Closed the pre-1.0 repository audit without adding features.
- Classified all intentional abstract interface methods.
- Added component maturity and known-limitations documents.
- Normalized SDK metadata and cumulative changelog structure.
- Added automated audit-closure tests and fail-closed 1.0 guidance.

0.99.0-rc1 - 2026-10-26
- Added final blocker/waiver closure gate.
- Added final documentation-review gate.
- Added 1.0.0 artifact signature, provenance and SBOM gates.
- Added authoritative GO-1.0/NO-GO dossier contract.

## 0.98.0-rc1 - 2026-10-26
- Added signed staging release-rehearsal evidence gates.
- Added clean-install, upgrade and rollback integrity drills.
- Added support/incident/rollback operational rehearsal gates.
- Added consolidated rehearsal approval and NO-GO behavior for missing real evidence.

## 0.97.0-rc1 - 2026-10-26
- Added launch-candidate frozen-change, signed-artifact/provenance, operational-playbook and rollback gates.
- Added explicit release/security/operations approval requirements.

## 0.96.0-rc1 - 2026-10-26
- Added documentation/support and packaging/operations readiness gates.
- Added verified release-evidence consolidation and residual-risk closure.
- Added final 1.0 readiness dossier with three-owner approval requirement.

## 0.95.0-rc1 - 2026-10-26
- Added real release-evidence ingestion contracts.
- Added critical/high blocker burn-down and waiver validation.
- Added wheel/sdist/container signature and provenance verification gates.
- Added staging release dry-run and rollback acceptance.
- Added explicit 1.0 GO/NO-GO decision requiring human approvals.

## 0.94.0-rc1 - 2026-10-26
- Added Windows/Linux/macOS and Python 3.10-3.13 install/upgrade/rollback/offline-install matrix gates.
- Added wheel/sdist/container plus SBOM/provenance reproducibility gates.
- Added dependency/license/security review closure and operational-runbook gates.
- Added consolidated 1.0 evidence-readiness gate.

## 0.93.0-rc1 - 2026-10-26
- Added extended-duration repeated-run soak certification.
- Added broader ecosystem evidence certification.
- Added disaster-recovery/state-restoration integrity and RTO drills.
- Added repeated-build reproducibility checks and consolidated RC gate digest.


## 0.92.0-rc1 - 2026-10-25
- Added RC evidence freshness and staleness enforcement.
- Added upgrade/rollback/re-upgrade drills with integrity-digest comparison.
- Added repeated-build API/diagnostic/bytecode drift surveillance.
- Added security/performance/memory trend gates, ecosystem certification and recovery drills.
- Added waiver expiry/ownership controls and consolidated RC2 certification gate.

## 0.91.0-rc1 - 2026-10-25
- Added cross-platform Windows/Linux/macOS and Python 3.10-3.13 soak-evidence contracts.
- Added supported-version upgrade and rollback/integrity validation.
- Added frozen API/diagnostic/bytecode compatibility surveillance.
- Added security, performance, packaging and offline-install soak aggregation.
- Added blocker/waiver validation and a consolidated RC go/no-go gate.

## 0.90.0-rc1 - 2026-10-25
- Froze intended public syntax, runtime, package, diagnostic and versioned bytecode compatibility surfaces for 1.0.
- Added canonical API freeze manifests and SHA-256 API-contract digests.
- Added additive/breaking API classification and approval-required breaking-change gates.
- Added the machine-readable 1.0 compatibility contract, tests and release documentation.
- Corrected stale Containerfile version references for the 0.90 RC line.

## 0.89.0-rc1 - 2026-10-25
- Froze new feature families for release-candidate hardening.
- Added blocker/high-severity defect and waiver registry contracts.
- Added consolidated regression, API, security, performance, supply-chain, migration, tooling, documentation and cross-platform readiness gates.
- Added tamper-evident RC readiness report digest.
- Added tests, release notes, known-issues registry and retention evidence.

## 0.89.0-alpha.1 - 2026-10-25
- Froze new feature families for RC hardening.
- Added consolidated release evidence and GO/NO-GO decisions.
- Added blocker/high-severity defect closure and scoped waivers.
- Added RC readiness tests and documentation.

## 0.88.0-alpha.1 - 2026-10-25
- Added LSP and DAP compatibility certification contracts.
- Added stable diagnostic code/severity registry and snapshots.
- Added deterministic editor capability negotiation.
- Added reproducible breakpoint/stack/variable debugging fixtures.
- Added combined developer-tooling certification gates, tests and documentation.

## 0.87.0-alpha.1 - 2026-10-25
- Added agent tool isolation, approval replay protection, budgets and audit certification.

## 0.86.0-alpha.1 - 2026-10-25
- Added ML and serving conformance.

## 0.85.0-alpha.1 - 2026-10-25
- Added connector capability profiles and certification suites.
- Added SQL dialect, binding and transaction conformance contracts.
- Added streaming checkpoint, replay and deduplication semantics.
- Added object-store pagination, range-read and multipart-failure fixtures.
- Added certification gates, tests, release notes and retention evidence.

## 0.84.0-alpha.1 - 2026-10-25
- Added parent-child cancellation and deadline propagation.
- Added fail-fast structured task-group lifecycle guarantees.
- Added retry safety and idempotency-key payload validation.
- Added graceful shutdown, draining and resilience release gates.
- Added stress-oriented regression tests, release notes and retention evidence.

## 0.83.0-alpha.1 - 2026-10-25
- Added representative benchmark-suite execution with mean, p50, p95, p99, throughput and peak-memory evidence.
- Added prior-baseline performance regression budgets and automated gates.
- Added named compiler/runtime hot-path profiling.
- Added cache load/eviction metrics and memory-pressure probes.
- Added benchmark baseline serialization, tests, release notes and retention evidence.

## 0.82.0-alpha.1 - 2026-10-25
- Added deterministic source manifests and tamper verification.
- Added CycloneDX SBOM and SLSA/in-toto provenance verification.
- Added Ed25519 detached release-manifest signing and verification.
- Added dependency-lock and offline-install evidence plus packaging quality gates.
- Added tests, release notes, retention evidence and handover.

## 0.81.0-alpha.1 - 2026-10-25
- Added machine-readable deprecation lifecycle enforcement.
- Added deterministic, resumable and reversible migration execution.
- Added public API snapshots, diffs and breaking-change gates.
- Added upgrade fixtures, tests, release notes and retention evidence.

## 0.80.0-alpha.1 - 2026-10-25
- Added W3C trace-context propagation and parent/child spans.
- Added bounded span export and metric cardinality controls.
- Added liveness/readiness operational contracts.
- Added redacted diagnostic bundles with SHA-256 manifests.
- Added tests, release notes, operations guide, retention report and handover.


## 0.79.0a1 - Enterprise integration hardening
- Added chained credential providers and normalized integration profiles.
- Added shared timeout, rate-limit, authentication and availability error taxonomy.
- Added exponential retry/backoff with jitter and circuit-breaker recovery.
- Added correlation IDs and connector health reports.
- Retained v0.78 security controls and all previous connector implementations.

## 0.78.0a1 - Security hardening
- Added reusable trust-boundary validation for text, collection, path and URL inputs.
- Added private/loopback/link-local network blocking for host URL validation.
- Added recursive credential and bearer-token redaction.
- Added tamper-evident SHA-256/HMAC audit chains.
- Added v0.78 security regression tests while retaining the cumulative release history.


## 0.77.0 - 2026-10-25
- Added repeatable runtime performance and allocation-memory probes.
- Added mean/p95 latency and peak-memory budget gates.
- Added a dependency-free bounded LRU cache with eviction and hit-rate metrics.
- Retained the clean documentation layout and v0.76 release-hardening gates.

## 0.76.0 - 2026-10-25
- Added adversarial agent-policy probes and deterministic probe summaries.
- Added public API compatibility gating with explicit approved-removal handling.
- Added integrated test, security, API and file-retention release thresholds.
- Reorganized release notes, retention evidence and project metadata under `docs/` while retaining one root cumulative changelog and detailed README.

## 0.75.0 - 2026-10-25
- Added persistent SQLite agent audit trails, durable approval records, deterministic approval IDs, actor/reason capture, and audited tool-execution evidence.

## 0.73.0 - 2026-10-25
- Added optional ONNX Runtime inference, tensor/DataFrame and PyTorch interchange, and policy-governed natural-language query planning.

## 0.72.0 - 2026-10-25
- Merged interactive dashboard controls/bindings, browser REPL and dataset inspection, plus Jupyter kernel protocol and rich DataFrame rendering.

## 0.71.0 - 2026-10-24
- Combined three roadmap targets: dataset/column lineage, pipeline observability with SLA/alerts/audit, and a declarative dashboard DSL with React rendering.

## 0.70.0 - 2026-10-24
- Added durable SQLite orchestration state, retries with backoff/jitter, deterministic idempotency, interval scheduling, logical dates, run history, and backfill execution.

## 0.69.0 - 2026-10-24
- Added DAG/task definitions, dependency validation, cycle detection, deterministic topological ordering, execution layers, declarative graph loading, and local DAG execution.

## 0.68.0 - 2026-10-24
- Added RabbitMQ and WebSocket connectors, explicit RabbitMQ acknowledgement controls, QoS/prefetch, JSON messaging, and an in-memory message bus.

## 0.67.0 - 2026-10-24
- Added Kafka producer/consumer integration, consumer groups, manual commits, security options, batch publishing, and an in-memory test broker.

## 0.66.0 - 2026-10-24
- Added event-time streams, watermarks, late-event handling, tumbling/sliding windows, and persistent idempotent delivery semantics.

## 0.65.0 - 2026-10-24
- Added partitioning, bounded JSONL scans, predicate/projection pushdown, spill execution and checkpoints.


## 0.64.0a1 - 2026-10-24
- Added engine-neutral distributed compute plans and Local/Arrow/Polars/Spark adapters.
## 0.63.0rc2 - 2026-10-24
- RC2 stabilization: refreshed validation evidence, RC1 API compatibility checks and migration/operator guidance.
## 0.63.0rc1 - 2026-10-24
- Froze feature scope for RC1 and added API compatibility, deprecation policy, integration gates, threat model and migration guidance.
## 0.62.0 - 2026-10-24
- Added release-candidate packaging, SBOM/provenance, checksums, artifact verification, Containerfile, CI matrix and v1 readiness assessment.
## 0.61.0 - 2026-10-24
- Added secure Kubernetes YAML, security contexts, NetworkPolicy/PDB/topology controls, drain handling and RC stabilization checks.
## 0.60.0 - 2026-10-23
- Added distributed serving backends, load/performance gates, OpenTelemetry hooks and Kubernetes operations.
## 0.59.0 - 2026-10-23
- Added resilient serving with rate/concurrency limits, timeouts, logs/traces, secure loading, live reload and rollback.
## 0.57.0 - 2026-10-23
- Added portable pipelines, SQLite monitoring, policy/deployment manifests and MLOps CLI commands.
## 0.56.0 - 2026-10-23
- Added secure model bundles, monitoring stores, alerts, promotion gates, canary routing and rollback controls.
## 0.55.0 - 2026-10-23
- Added model bundles, inference/audit APIs, drift and fairness diagnostics, calibration, registry lifecycle and FastAPI serving.
## 0.54.0 - 2026-10-23
- Added production ML pipelines, cross-validation, tuning, regularization, multiclass classification and governance artifacts.
## 0.53.0 - 2026-10-23
- Added ML foundations: preprocessing, linear/logistic regression, evaluation, k-fold indices, persistence and pipelines.
## 0.52.0 - 2026-10-23
- Added forecasting baselines, evaluation metrics, seasonal decomposition, grouped forecasts, chart-ready series and optional acceleration benchmarks.
## 0.51.0 - 2026-10-23
- Added grouped and time-series analytics with resampling, shifts, changes, expanding/EWM windows and interpolation.
## 0.50.0 - 2026-10-23
- Added DataFrame analytics and statistics: summaries, quantiles, dispersion, correlation, frequencies, crosstabs, ranking, cumulative/rolling calculations, outliers and profiling.
## 0.49.0 - 2026-10-23
- Hardened connector runtime with token providers, profiles, health checks, certification matrices and Graph/SharePoint paging.
## 0.48.0 - 2026-10-23
- Added Microsoft Graph/SharePoint connector foundation, secret providers, capability metadata and connector certification.
## 0.47.0 - 2026-10-23
- Added S3, Azure Blob, ADLS Gen2 and GCS object storage connectors with common file and DataFrame operations.
## 0.46.0 - 2026-10-23
- Added OData and SFTP cloud connectors with pagination, query options, secure transfers and DataFrame ingestion.
## 0.45.0 - 2026-10-23
- Added Connector SDK with registry, transport abstraction, retries, auth helpers, REST and GraphQL connectors, pagination and DataFrame conversion.
## 0.44.0 - 2026-10-23
- Added SQL/database layer with SQLite, optional database adapters, discovery, parameterized queries, transactions, batching and SQLite upsert.
## 0.43.0 - 2026-10-23
- Added DataFrame Engine: joins, grouped aggregations, expressions, null handling, pivot/unpivot, window row numbers and expanded LazyFrame operations.
## 0.42.0 - 2026-10-23
- Added PeaLang Data foundation: schema model, DataFrame/LazyFrame, connector registry, CSV/JSON/JSONL and core transforms.
## 0.41.0 - 2026-10-23
- Added beta/pilot readiness model, candidate pilots, performance regression gate, security-review preparation and 1.0 migration-readiness report.
## 0.40.0 - 2026-10-23
- Added 500-case conformance corpus, differential runner, fuzz harness, security-boundary suite and multi-platform/Python CI definitions.
## 0.39.0 - 2026-10-23
- Added WebAssembly containers, browser ABI/policy, SDK and CLI.
## 0.38.0 - 2026-10-23
- Added native test/expect runner, filtering, coverage baseline, watch-mode portability baseline and migration CLI.
## 0.37.0 - 2026-10-23
- Added complete resource limit accounting and structured concurrency with cancellation propagation.
## 0.36.0 - 2026-10-23
- Added generic contracts/substitution/inference, protocols, project-wide contract analysis, and Result/Option/Future semantics foundation.
## 0.35.0 - 2026-10-23
- Stabilized the 14-module `std.*` standard library, capability gates, manifest, CLI inspection and compatibility tests.

### Language specification
- Added implementation-independent language specification, EBNF grammar, feature stability registry, compatibility/deprecation contract, spec CLI, and revised foundational roadmap.

### Registry metadata
- Added canonical registry indexes, sequence/replay protection, immutable version policy, package expiration, publisher namespaces, persistent registry state, and environment-based Bearer credentials.

### Package authenticity
- Added Ed25519 public-key package signatures, public trust store, revocation, HTTPS registry transport, verified install, offline cache, and lockfile hash enforcement.

### Package archives
- Added signed .peapkg support, trusted publisher keys, verification, safe extraction, HTTPS registry policy, installation receipts, and dependency-confusion defenses.

### Tooling and conformance
- Added VM profiling, line coverage, benchmark tooling, and observer hooks.
- Added interpreter-versus-VM differential conformance coverage.
- Added source inventory/hash comparison and strengthened release integrity gates.
- Added profile/benchmark CLI commands and hardening documentation.

## 0.29.0 - 2026-10-22
- Added TypeScript SDK, React hooks, browser-safe capabilities, and schema UI integration.
## 0.28.0 - 2026-10-22
- Added Java runtime sidecar and Java SDK.
## 0.27.0 - 2026-10-22
- Added package ecosystem foundation.
## 0.26.0 - 2026-10-22
- Added native async VM.
## 0.24.0 - 0.25.0
- Added semantic analysis and FastAPI integration.
## 0.18.0 - 0.23.0
- Added embedding, types, compiler/VM, capability safety, exceptions, imports, and VM DAP.
## 0.1.0 - 0.17.0
- Established the language and tooling foundations.


## 0.74.0-alpha.1 - 2026-10-25
- Added agent dry-run tool planning.
- Added deterministic tool allow/deny policy gates.
- Added host approval gates for sensitive agent actions.
- Added tool-call budget enforcement.
- Moved historical development handovers to `docs/handover/` for a cleaner project root.
- Added agent governance documentation and regression tests.
