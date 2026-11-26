# SLO enforcement and incident-response governance

Phase 102 continues Wave 6 with a deterministic SLO enforcement and
incident-response governance sector pack at version 5.2.0. It is additive to the
observability pack, runtime profiler, performance-gate, and certified-package
surfaces, and it does not change the frozen 3.0 language surface.

`slo_pack_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.slo.json` source filter, the sorted SLO
kinds, stable ordering, and a recomputed gate.
`SLO_PACK_VERSION` records the current release and `SLO_PACK_FORMAT` identifies
the sector-pack format.

`SloProfileV2` is a frozen, validated profile with a positive `max_entries`
limit, an `include_preview` switch, a `check_budget` switch, a `check_drill`
switch, a `check_escalation` switch, a `check_postmortem` switch, a
`check_route` switch, a `check_runbook` switch, a `check_slo` switch, a
`fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `SLO_PACK_VERSION`. Invalid profiles raise
`SloPackError` before any planning occurs.
`DEFAULT_SLO_PROFILE` is stable and serializable.

`plan_slo_pack()` discovers governance manifests under a root while skipping
build and cache directories. Preview, canary, and experimental directories are
skipped unless `include_preview` is enabled. Each manifest must declare a
lowercase `name`, a string `version`, a `kind` drawn from `SLO_KINDS`, a non-empty
sorted set of `evidence` artifacts, string lists for `requires`, and string
lists for `bindings`; invalid manifests produce an `S204` issue. Every declared
evidence path must resolve to a file under the root, or an `S205` issue is
produced. Each `SloAppV2` carries a relative path, a manifest content digest,
the name, version, kind, sorted evidence paths, sorted platform bindings, sorted
required names, sorted resolved dependencies, a clean/stale state, and reasons.
A dependency is resolved through the provider set of a required name. Wall-clock
values and absolute host paths never enter the plan.

A required entry with no provider produces an `S201` issue; a dependency cycle
produces an `S202` issue; and exceeding the entry limit produces an `S203` issue.
When `check_budget` is enabled, an `incident-demo` with no resolved
`error-budget` dependency produces an `S206` issue. When `check_drill` is
enabled, an `incident-demo` with no resolved `incident-drill` dependency produces
an `S207` issue. When `check_escalation` is enabled, an `incident-demo` with no
resolved `escalation-policy` dependency produces an `S208` issue. When
`check_postmortem` is enabled, an `incident-demo` with no resolved `postmortem`
dependency produces an `S209` issue. When `check_route` is enabled, an
`incident-demo` with no resolved `alert-route` dependency produces an `S210`
issue. When `check_runbook` is enabled, an `incident-demo` with no resolved
`runbook` dependency produces an `S211` issue. When `check_slo` is enabled, an
`incident-demo` with no resolved `slo` dependency produces an `S212` issue. All
issues are sorted by code, path, and message. Incomplete state starts from paths
whose digest is new or changed relative to supplied state, with `new` or
`changed` reasons, and propagates a `dependency` reason to dependents through a
stable queue. Entries are emitted in a deterministic topological order.

`load_slo_state_v2()` reads versioned digest state, returning empty state for an
absent file and rejecting invalid version, JSON, or shape.
`write_slo_state_v2()` persists a deterministic digest map keyed by relative
path, with no absolute host paths.

`slo_pack_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest.
`slo_pack_gate()` verifies the version, format, gate shape, report and plan
digests, entry and issue fingerprints, count consistency, and profile, then
recomputes PASS/FAIL from the reported error count, incomplete count, and
incomplete-failure policy. Extra fields such as CLI decisions are ignored by
digest recomputation.

The `pea slo-pack ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-budget]
[--no-check-drill] [--no-check-escalation] [--no-check-postmortem]
[--no-check-route] [--no-check-runbook] [--no-check-slo] [--fail-on-incomplete]
[--current-version V]` command reports SLO governance evidence without creating
or modifying project files. `--check` requires a passing gate, `--emit` writes
the JSON report, and `--write-state` persists the digest state.
`pea slo-pack --capabilities` prints the versioned capability set. The
`sector.slo_pack` feature flag records availability.
