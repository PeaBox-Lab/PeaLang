# Capacity and cost reliability governance

Phase 104 continues Wave 6 with a deterministic capacity and cost reliability
governance sector pack at version 5.4.0. It is additive to the chaos, SLO,
observability pack, runtime profiler, performance-gate, and certified-package
surfaces, and it does not change the frozen 3.0 language surface.

`capacity_pack_capabilities()` returns the versioned capability set with the
default profile, supported options, the `*.capacity.json` source filter, the
sorted capacity kinds, stable ordering, and a recomputed gate.
`CAPACITY_PACK_VERSION` records the current release and `CAPACITY_PACK_FORMAT`
identifies the sector-pack format.

`CapacityProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, a `check_budget` switch, a
`check_quota` switch, a `check_headroom` switch, a `check_autoscale` switch, a
`check_limit` switch, a `check_forecast` switch, a `check_review` switch, a
`fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `CAPACITY_PACK_VERSION`. Invalid profiles raise
`CapacityPackError` before any planning occurs. `DEFAULT_CAPACITY_PROFILE` is
stable and serializable.

`plan_capacity_pack()` discovers capacity manifests under a root while skipping
build and cache directories. Preview, canary, and experimental directories are
skipped unless `include_preview` is enabled. Each manifest must declare a
lowercase `name`, a string `version`, a `kind` drawn from `CAPACITY_KINDS`, a
non-empty sorted set of `evidence` artifacts, string lists for `requires`, and
string lists for `bindings`; invalid manifests produce a `K204` issue. Every
declared evidence path must resolve to a file under the root, or a `K205` issue
is produced. Each `CapacityAppV2` carries a relative path, a manifest content
digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces a `K201` issue; a dependency cycle
produces a `K202` issue; and exceeding the entry limit produces a `K203` issue.
When `check_budget` is enabled, a `capacity-demo` with no resolved `cost-budget`
dependency produces a `K206` issue. When `check_quota` is enabled, a
`capacity-demo` with no resolved `quota` dependency produces a `K207` issue.
When `check_headroom` is enabled, a `capacity-demo` with no resolved `headroom`
dependency produces a `K208` issue. When `check_autoscale` is enabled, a
`capacity-demo` with no resolved `autoscale-policy` dependency produces a
`K209` issue. When `check_limit` is enabled, a `capacity-demo` with no resolved
`resource-limit` dependency produces a `K210` issue. When `check_forecast` is
enabled, a `capacity-demo` with no resolved `forecast` dependency produces a
`K211` issue. When `check_review` is enabled, a `capacity-demo` with no resolved
`review-gate` dependency produces a `K212` issue. All issues are sorted by code,
path, and message. Incomplete state starts from paths whose digest is new or
changed relative to supplied state, with `new` or `changed` reasons, and
propagates a `dependency` reason to dependents through a stable queue. Entries
are emitted in a deterministic topological order.

`load_capacity_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_capacity_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`capacity_pack_report()` summarizes plan count, entry and incomplete counts,
error count, per-plan evidence, and a recomputable digest.
`capacity_pack_gate()` verifies the version, format, gate shape, report and
plan digests, entry and issue fingerprints, count consistency, and profile,
then recomputes PASS/FAIL from the reported error count, incomplete count, and
incomplete-failure policy. Extra fields such as CLI decisions are ignored by
digest recomputation.

The `pea capacity-pack ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-budget]
[--no-check-quota] [--no-check-headroom] [--no-check-autoscale]
[--no-check-limit] [--no-check-forecast] [--no-check-review]
[--fail-on-incomplete] [--current-version V]` command reports capacity
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea capacity-pack --capabilities` prints the versioned
capability set. The `sector.capacity_pack` feature flag records availability.
