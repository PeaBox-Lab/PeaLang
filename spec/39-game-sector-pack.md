# Game Development sector pack

Wave 4 continues with a deterministic sector-pack evidence gate for the Game
Development row of the sector table. It is additive to `host_bindings.py`,
`vm_embedding.py`, and the Java client sidecar, and it does not change the frozen
3.0 language surface.

`game_pack_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.game.json` source filter, the sorted game
kinds, stable ordering, and a recomputed gate. `GAME_PACK_VERSION` records the
current release and `GAME_PACK_FORMAT` identifies the sector-pack format.

`GameProfileV2` is a frozen, validated profile with a positive `max_games`
limit, an `include_preview` switch, a `check_runtime` switch, a `check_ecs`
switch, a `check_engine` switch, a `check_hot_reload` switch, a `check_input`
switch, a `check_render` switch, a `fail_on_incomplete` policy, and a
`current_version` string. An empty `current_version` resolves to
`GAME_PACK_VERSION`. Invalid profiles raise `GamePackError` before any planning
occurs. `DEFAULT_GAME_PROFILE` is stable and serializable.

`plan_game_pack()` discovers games under a root while skipping build and cache
directories. Preview, canary, and experimental directories are skipped unless
`include_preview` is enabled. Each manifest must declare a lowercase `name`, a
string `version`, a `kind` drawn from `GAME_KINDS`, a non-empty sorted set of
`evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce a `G204` issue. Every declared evidence
path must resolve to a file under the root, or a `G205` issue is produced. Each
`GameAppV2` carries a relative path, a manifest content digest, the name,
version, kind, sorted evidence paths, sorted platform bindings, sorted required
names, sorted resolved dependencies, a clean/stale state, and reasons. A
dependency is resolved through the provider set of a required game name.
Wall-clock values and absolute host paths never enter the plan.

A required game with no provider produces a `G201` issue; a dependency cycle
produces a `G202` issue; and exceeding the game limit produces a `G203` issue.
When `check_runtime` is enabled, a `sample-game` with no resolved `runtime`
dependency produces a `G206` issue. When `check_ecs` is enabled, a `sample-game`
with no resolved `ecs` dependency produces a `G207` issue. When `check_engine`
is enabled, a `sample-game` with no resolved `unity-bridge` or `unreal-bridge`
dependency produces a `G208` issue. When `check_hot_reload` is enabled, a
`sample-game` with no resolved `hot-reload` dependency produces a `G209` issue.
When `check_input` is enabled, a `sample-game` with no resolved `input-api`
dependency produces a `G210` issue. When `check_render` is enabled, a
`sample-game` with no resolved `render-api` dependency produces a `G211` issue.
All issues are sorted by code, path, and message. Incomplete state starts from
paths whose digest is new or changed relative to supplied state, with `new` or
`changed` reasons, and propagates a `dependency` reason to dependents through a
stable queue. Games are emitted in a deterministic topological order.

`load_game_state_v2()` reads versioned digest state, returning empty state for
an absent file and rejecting invalid version, JSON, or shape.
`write_game_state_v2()` persists a deterministic digest map keyed by relative
path, with no absolute host paths.

`game_pack_report()` summarizes plan count, game and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `game_pack_gate()` verifies
the version, format, gate shape, report and plan digests, game and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea game-pack ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-games N] [--include-preview] [--no-check-runtime]
[--no-check-ecs] [--no-check-engine] [--no-check-hot-reload] [--no-check-input]
[--no-check-render] [--fail-on-incomplete] [--current-version V]` command
reports game evidence without creating or modifying project files. `--check`
requires a passing gate, `--emit` writes the JSON report, and `--write-state`
persists the digest state. `pea game-pack --capabilities` prints the versioned
capability set. The `sector.game_pack` feature flag records availability.
