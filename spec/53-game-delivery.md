# Game delivery evidence

Phase 110 continues Wave 7 with a deterministic game delivery evidence sector pack
at version 5.10.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`game_delivery_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.game.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `GAME_DELIVERY_VERSION` records the
current release and `GAME_DELIVERY_FORMAT` identifies the sector-pack format.

`GameDeliveryProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_runtime`, `check_ecs`, `check_engine`, `check_input`, `check_render`, `check_hot_reload`, `check_build`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `GAME_DELIVERY_VERSION`. Invalid profiles raise
`GameDeliveryPackError` before any planning occurs.
`DEFAULT_GAME_DELIVERY_PROFILE` is stable and serializable.

`plan_game_delivery()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `runtime-binding`, `ecs-binding`, `engine-bridge`, `input-api`, `render-api`, `hot-reload`, `playable-build`, `resource`, `game-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `D204` issue. Every declared
evidence path must resolve to a file under the root, or an `D205`
issue is produced. Each `GameDeliveryAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `D201` issue; a dependency
cycle produces an `D202` issue; and exceeding the entry limit produces
an `D203` issue. When `check_runtime` is enabled, a `game-demo` with no resolved `runtime-binding` dependency produces an `D206` issue.
When `check_ecs` is enabled, a `game-demo` with no resolved `ecs-binding` dependency produces an `D207` issue.
When `check_engine` is enabled, a `game-demo` with no resolved `engine-bridge` dependency produces an `D208` issue.
When `check_input` is enabled, a `game-demo` with no resolved `input-api` dependency produces an `D209` issue.
When `check_render` is enabled, a `game-demo` with no resolved `render-api` dependency produces an `D210` issue.
When `check_hot_reload` is enabled, a `game-demo` with no resolved `hot-reload` dependency produces an `D211` issue.
When `check_build` is enabled, a `game-demo` with no resolved `playable-build` dependency produces an `D212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_game_delivery_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_game_delivery_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`game_delivery_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `game_delivery_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea game-delivery ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-runtime] [--no-check-ecs] [--no-check-engine] [--no-check-input] [--no-check-render] [--no-check-hot-reload] [--no-check-build]
[--fail-on-incomplete] [--current-version V]` command reports game delivery
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea game-delivery --capabilities` prints the versioned capability
set. The `sector.game_delivery` feature flag records availability. Stable issue codes are
`D206`, `D207`, `D208`, `D209`, `D210`, `D211`, `D212` for the required evidence checks, alongside the structural codes
`D201`–`D205`.
