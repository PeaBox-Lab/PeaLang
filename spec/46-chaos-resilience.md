# Chaos engineering and resilience validation

Phase 103 continues Wave 6 with a deterministic chaos engineering and
resilience validation sector pack at version 5.3.0. It is additive to the SLO,
observability pack, runtime profiler, performance-gate, and certified-package
surfaces, and it does not change the frozen 3.0 language surface.

`chaos_pack_capabilities()` returns the versioned capability set with the
default profile, supported options, the `*.chaos.json` source filter, the
sorted chaos kinds, stable ordering, and a recomputed gate.
`CHAOS_PACK_VERSION` records the current release and `CHAOS_PACK_FORMAT`
identifies the sector-pack format.

`ChaosProfileV2` is a frozen, validated profile with a positive `max_entries`
limit, an `include_preview` switch, a `check_steady` switch, a `check_hypothesis`
switch, a `check_blast` switch, a `check_abort` switch, a `check_rollback`
switch, a `check_game_day` switch, a `check_report` switch, a
`fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `CHAOS_PACK_VERSION`. Invalid profiles raise
`ChaosPackError` before any planning occurs.
`DEFAULT_CHAOS_PROFILE` is stable and serializable.

`plan_chaos_pack()` discovers resilience manifests under a root while skipping
build and cache directories. Preview, canary, and experimental directories are
skipped unless `include_preview` is enabled. Each manifest must declare a
lowercase `name`, a string `version`, a `kind` drawn from `CHAOS_KINDS`, a
non-empty sorted set of `evidence` artifacts, string lists for `requires`, and
string lists for `bindings`; invalid manifests produce a `C204` issue. Every
declared evidence path must resolve to a file under the root, or a `C205` issue
is produced. Each `ChaosAppV2` carries a relative path, a manifest content
digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces a `C201` issue; a dependency cycle
produces a `C202` issue; and exceeding the entry limit produces a `C203` issue.
When `check_steady` is enabled, a `resilience-demo` with no resolved
`steady-state` dependency produces a `C206` issue. When `check_hypothesis` is
enabled, a `resilience-demo` with no resolved `hypothesis` dependency produces a
`C207` issue. When `check_blast` is enabled, a `resilience-demo` with no resolved
`blast-radius` dependency produces a `C208` issue. When `check_abort` is
enabled, a `resilience-demo` with no resolved `abort-condition` dependency
produces a `C209` issue. When `check_rollback` is enabled, a `resilience-demo`
with no resolved `rollback-plan` dependency produces a `C210` issue. When
`check_game_day` is enabled, a `resilience-demo` with no resolved `game-day`
dependency produces a `C211` issue. When `check_report` is enabled, a
`resilience-demo` with no resolved `resilience-report` dependency produces a
`C212` issue. All issues are sorted by code, path, and message. Incomplete state
starts from paths whose digest is new or changed relative to supplied state,
with `new` or `changed` reasons, and propagates a `dependency` reason to
dependents through a stable queue. Entries are emitted in a deterministic
topological order.

`load_chaos_state_v2()` reads versioned digest state, returning empty state for
an absent file and rejecting invalid version, JSON, or shape.
`write_chaos_state_v2()` persists a deterministic digest map keyed by relative
path, with no absolute host paths.

`chaos_pack_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest.
`chaos_pack_gate()` verifies the version, format, gate shape, report and plan
digests, entry and issue fingerprints, count consistency, and profile, then
recomputes PASS/FAIL from the reported error count, incomplete count, and
incomplete-failure policy. Extra fields such as CLI decisions are ignored by
digest recomputation.

The `pea chaos-pack ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-steady]
[--no-check-hypothesis] [--no-check-blast] [--no-check-abort]
[--no-check-rollback] [--no-check-game-day] [--no-check-report]
[--fail-on-incomplete] [--current-version V]` command reports resilience
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea chaos-pack --capabilities` prints the versioned capability
set. The `sector.chaos_pack` feature flag records availability.
