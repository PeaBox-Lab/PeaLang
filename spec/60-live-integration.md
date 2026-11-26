# Live service integration evidence

Phase 117 continues Wave 8 with a deterministic live service integration evidence sector pack
at version 5.17.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`live_integration_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.integration.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `LIVE_INTEGRATION_VERSION` records the
current release and `LIVE_INTEGRATION_FORMAT` identifies the sector-pack format.

`LiveIntegrationProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_database`, `check_cloud`, `check_sharepoint`, `check_sftp`, `check_redis`, `check_redaction`, `check_fixture`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `LIVE_INTEGRATION_VERSION`. Invalid profiles raise
`LiveIntegrationPackError` before any planning occurs.
`DEFAULT_LIVE_INTEGRATION_PROFILE` is stable and serializable.

`plan_live_integration()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `database-connection`, `cloud-store`, `sharepoint-binding`, `sftp-binding`, `redis-binding`, `redacted-endpoint`, `fixture-result`, `resource`, `integration-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `LI204` issue. Every declared
evidence path must resolve to a file under the root, or an `LI205`
issue is produced. Each `LiveIntegrationAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `LI201` issue; a dependency
cycle produces an `LI202` issue; and exceeding the entry limit produces
an `LI203` issue. When `check_database` is enabled, a `integration-demo` with no resolved `database-connection` dependency produces an `LI206` issue.
When `check_cloud` is enabled, a `integration-demo` with no resolved `cloud-store` dependency produces an `LI207` issue.
When `check_sharepoint` is enabled, a `integration-demo` with no resolved `sharepoint-binding` dependency produces an `LI208` issue.
When `check_sftp` is enabled, a `integration-demo` with no resolved `sftp-binding` dependency produces an `LI209` issue.
When `check_redis` is enabled, a `integration-demo` with no resolved `redis-binding` dependency produces an `LI210` issue.
When `check_redaction` is enabled, a `integration-demo` with no resolved `redacted-endpoint` dependency produces an `LI211` issue.
When `check_fixture` is enabled, a `integration-demo` with no resolved `fixture-result` dependency produces an `LI212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_live_integration_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_live_integration_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`live_integration_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `live_integration_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea live-integration ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-database] [--no-check-cloud] [--no-check-sharepoint] [--no-check-sftp] [--no-check-redis] [--no-check-redaction] [--no-check-fixture]
[--fail-on-incomplete] [--current-version V]` command reports live integration
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea live-integration --capabilities` prints the versioned capability
set. The `sector.live_integration` feature flag records availability. Stable issue codes are
`LI206`, `LI207`, `LI208`, `LI209`, `LI210`, `LI211`, `LI212` for the required evidence checks, alongside the structural codes
`LI201`–`LI205`.
