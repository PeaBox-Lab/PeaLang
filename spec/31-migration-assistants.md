# Migration assistants

Wave 3 continues with an additive migration assistant layer. It does not change
the frozen 3.0 language surface, and it does not replace the existing
`pea migrate` command; that command remains available.

`migration_assistants_capabilities()` returns the versioned capability set with
the default profile, supported options, the `*.migration` source filter, stable
ordering, and a recomputed gate. `MIGRATION_ASSISTANTS_VERSION` records the
current release and `MIGRATION_ASSISTANTS_FORMAT` identifies the evidence format.

`MigrationProfileV2` is a frozen, validated profile with a positive
`max_migrations` limit, an `include_test_migrations` switch, a `check_imports`
switch, a `fail_on_dirty` policy, and a `current_version` string. An empty
`current_version` resolves to `MIGRATION_ASSISTANTS_VERSION`. Invalid profiles
raise `MigrationAssistantError` before any planning occurs.
`DEFAULT_MIGRATION_PROFILE` is stable and serializable.

`plan_migration_v2()` discovers migration sources under a root while skipping
build and cache directories. Release-note, history, archive, and retention
directories are skipped unless `include_test_migrations` is enabled. Each
`MigrationNodeV2` carries a relative path, a content digest, sorted import
declarations matched by `import "name"`, sorted script definitions matched by
`def name(`, sorted resolved dependencies, a clean/stale state, and reasons.
A dependency is resolved when an imported name is defined by a migration script
or matches a stable candidate path. Wall-clock values and absolute host paths
never enter the plan.

An import with no provider produces an `M201` issue when `check_imports` is
enabled; a dependency cycle produces an `M202` issue; and exceeding the
migration limit produces an `M203` issue. All issues are sorted by code, path,
and message. Dirty state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to importers through a stable queue. Nodes are emitted in a
deterministic topological order.

`load_migration_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_migration_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`migration_v2_report()` summarizes plan count, node and dirty counts, error
count, per-plan evidence, and a recomputable digest. `migration_v2_gate()`
verifies the version, format, gate shape, report and plan digests, node and
issue fingerprints, count consistency, and profile, then recomputes PASS/FAIL
from the reported error count, dirty count, and dirty-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea migrate-v2 ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-migrations N] [--include-test-migrations]
[--no-check-imports] [--fail-on-dirty] [--current-version V]` command reports a
migration plan without changing source. `--check` requires a passing gate,
`--emit` writes the JSON report, and `--write-state` persists the digest state.
`pea migrate-v2 --capabilities` prints the versioned capability set. The
`devx.migration_assistants` feature flag records availability.
