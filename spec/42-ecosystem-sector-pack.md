# Ecosystem registry and migration guides

Wave 5 opens with a deterministic ecosystem registry and migration-guide
evidence gate. It is additive to the registry resolution, signing, publishing,
and migration-assistant surfaces, and it does not change the frozen 3.0 language
surface.

`ecosystem_pack_capabilities()` returns the versioned capability set with the
default profile, supported options, the `*.ecosystem.json` source filter, the
sorted entry kinds, stable ordering, and a recomputed gate.
`ECOSYSTEM_PACK_VERSION` records the current release and `ECOSYSTEM_PACK_FORMAT`
identifies the sector-pack format.

`EcosystemProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, a `check_python` switch, a
`check_javascript` switch, a `check_java` switch, a `check_go` switch, a
`check_rust` switch, a `check_sql` switch, a `check_registry` switch, a
`check_metadata` switch, a `check_signature` switch, a `check_lockfile` switch,
a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `ECOSYSTEM_PACK_VERSION`. Invalid profiles raise
`EcosystemPackError` before any planning occurs. `DEFAULT_ECOSYSTEM_PROFILE` is
stable and serializable.

`plan_ecosystem_pack()` discovers ecosystem manifests under a root while
skipping build and cache directories. Preview, canary, and experimental
directories are skipped unless `include_preview` is enabled. Each manifest must
declare a lowercase `name`, a string `version`, a `kind` drawn from
`ECOSYSTEM_KINDS`, a non-empty sorted set of `evidence` artifacts, string lists
for `requires`, and string lists for `bindings`; invalid manifests produce an
`E204` issue. Every declared evidence path must resolve to a file under the
root, or an `E205` issue is produced. Each `EcosystemAppV2` carries a relative
path, a manifest content digest, the name, version, kind, sorted evidence paths,
sorted platform bindings, sorted required names, sorted resolved dependencies, a
clean/stale state, and reasons. A dependency is resolved through the provider
set of a required name. Wall-clock values and absolute host paths never enter
the plan.

A required entry with no provider produces an `E201` issue; a dependency cycle
produces an `E202` issue; and exceeding the entry limit produces an `E203`
issue. When `check_python` is enabled, an `ecosystem-demo` with no resolved
`python-guide` dependency produces an `E206` issue. When `check_javascript` is
enabled, an `ecosystem-demo` with no resolved `javascript-guide` dependency
produces an `E207` issue. When `check_java` is enabled, an `ecosystem-demo` with
no resolved `java-guide` dependency produces an `E208` issue. When `check_go`
is enabled, an `ecosystem-demo` with no resolved `go-guide` dependency produces
an `E209` issue. When `check_rust` is enabled, an `ecosystem-demo` with no
resolved `rust-guide` dependency produces an `E210` issue. When `check_sql` is
enabled, an `ecosystem-demo` with no resolved `sql-guide` dependency produces
an `E211` issue. When `check_registry` is enabled, an `ecosystem-demo` with no
resolved `registry-package` dependency produces an `E212` issue. When
`check_metadata` is enabled, an `ecosystem-demo` with no resolved
`registry-metadata` dependency produces an `E213` issue. When `check_signature`
is enabled, an `ecosystem-demo` with no resolved `signature` dependency produces
an `E214` issue. When `check_lockfile` is enabled, an `ecosystem-demo` with no
resolved `lockfile` dependency produces an `E215` issue. All issues are sorted
by code, path, and message. Incomplete state starts from paths whose digest is
new or changed relative to supplied state, with `new` or `changed` reasons, and
propagates a `dependency` reason to dependents through a stable queue. Entries
are emitted in a deterministic topological order.

`load_ecosystem_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_ecosystem_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`ecosystem_pack_report()` summarizes plan count, entry and incomplete counts,
error count, per-plan evidence, and a recomputable digest.
`ecosystem_pack_gate()` verifies the version, format, gate shape, report and
plan digests, entry and issue fingerprints, count consistency, and profile, then
recomputes PASS/FAIL from the reported error count, incomplete count, and
incomplete-failure policy. Extra fields such as CLI decisions are ignored by
digest recomputation.

The `pea ecosystem-pack ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-python]
[--no-check-javascript] [--no-check-java] [--no-check-go] [--no-check-rust]
[--no-check-sql] [--no-check-registry] [--no-check-metadata]
[--no-check-signature] [--no-check-lockfile] [--fail-on-incomplete]
[--current-version V]` command reports ecosystem evidence without creating or
modifying project files. `--check` requires a passing gate, `--emit` writes the
JSON report, and `--write-state` persists the digest state.
`pea ecosystem-pack --capabilities` prints the versioned capability set. The
`sector.ecosystem_pack` feature flag records availability.
