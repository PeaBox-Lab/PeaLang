# ML and serving conformance

Phase 107 continues Wave 7 with a deterministic ML and serving conformance sector pack
at version 5.7.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`serving_conformance_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.serving.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `SERVING_CONFORMANCE_VERSION` records the
current release and `SERVING_CONFORMANCE_FORMAT` identifies the sector-pack format.

`ServingConformanceProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_model`, `check_fixture`, `check_profile`, `check_overload`, `check_reload`, `check_rollback`, `check_report`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `SERVING_CONFORMANCE_VERSION`. Invalid profiles raise
`ServingConformancePackError` before any planning occurs.
`DEFAULT_SERVING_CONFORMANCE_PROFILE` is stable and serializable.

`plan_serving_conformance()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `model-contract`, `inference-fixture`, `serving-profile`, `overload-test`, `reload-test`, `rollback-test`, `benchmark-report`, `resource`, `serving-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `L204` issue. Every declared
evidence path must resolve to a file under the root, or an `L205`
issue is produced. Each `ServingConformanceAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `L201` issue; a dependency
cycle produces an `L202` issue; and exceeding the entry limit produces
an `L203` issue. When `check_model` is enabled, a `serving-demo` with no resolved `model-contract` dependency produces an `L206` issue.
When `check_fixture` is enabled, a `serving-demo` with no resolved `inference-fixture` dependency produces an `L207` issue.
When `check_profile` is enabled, a `serving-demo` with no resolved `serving-profile` dependency produces an `L208` issue.
When `check_overload` is enabled, a `serving-demo` with no resolved `overload-test` dependency produces an `L209` issue.
When `check_reload` is enabled, a `serving-demo` with no resolved `reload-test` dependency produces an `L210` issue.
When `check_rollback` is enabled, a `serving-demo` with no resolved `rollback-test` dependency produces an `L211` issue.
When `check_report` is enabled, a `serving-demo` with no resolved `benchmark-report` dependency produces an `L212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_serving_conformance_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_serving_conformance_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`serving_conformance_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `serving_conformance_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea serving-conformance ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-model] [--no-check-fixture] [--no-check-profile] [--no-check-overload] [--no-check-reload] [--no-check-rollback] [--no-check-report]
[--fail-on-incomplete] [--current-version V]` command reports serving conformance
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea serving-conformance --capabilities` prints the versioned capability
set. The `sector.serving_conformance` feature flag records availability. Stable issue codes are
`L206`, `L207`, `L208`, `L209`, `L210`, `L211`, `L212` for the required evidence checks, alongside the structural codes
`L201`–`L205`.
