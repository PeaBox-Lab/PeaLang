# Certified packages and the 5.0 ecosystem release

Wave 5 closes with the 5.0 ecosystem release and a deterministic certified-package
evidence gate. It is additive to the registry resolution, signing, publishing,
and migration-assistant surfaces, and it does not change the frozen 3.0 language
surface.

`certified_pack_capabilities()` returns the versioned capability set with the
default profile, supported options, the `*.certified.json` source filter, the
sorted package kinds, stable ordering, and a recomputed gate.
`CERTIFIED_PACK_VERSION` records the current release and
`CERTIFIED_PACK_FORMAT` identifies the sector-pack format.

`CertifiedProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, a `check_signature` switch, a
`check_provenance` switch, a `check_conformance` switch, a `check_reproducible`
switch, a `check_lockfile` switch, a `check_registry` switch, a
`check_migration` switch, a `fail_on_incomplete` policy, and a
`current_version` string. An empty `current_version` resolves to
`CERTIFIED_PACK_VERSION`. Invalid profiles raise `CertifiedPackError` before any
planning occurs. `DEFAULT_CERTIFIED_PROFILE` is stable and serializable.

`plan_certified_pack()` discovers certification manifests under a root while
skipping build and cache directories. Preview, canary, and experimental
directories are skipped unless `include_preview` is enabled. Each manifest must
declare a lowercase `name`, a string `version`, a `kind` drawn from
`CERTIFIED_KINDS`, a non-empty sorted set of `evidence` artifacts, string lists
for `requires`, and string lists for `bindings`; invalid manifests produce a
`C204` issue. Every declared evidence path must resolve to a file under the
root, or a `C205` issue is produced. Each `CertifiedAppV2` carries a relative
path, a manifest content digest, the name, version, kind, sorted evidence paths,
sorted platform bindings, sorted required names, sorted resolved dependencies, a
clean/stale state, and reasons. A dependency is resolved through the provider
set of a required name. Wall-clock values and absolute host paths never enter
the plan.

A required package with no provider produces a `C201` issue; a dependency cycle
produces a `C202` issue; and exceeding the entry limit produces a `C203` issue.
When `check_signature` is enabled, a `certification-demo` with no resolved
`signature` dependency produces a `C206` issue. When `check_provenance` is
enabled, a `certification-demo` with no resolved `provenance` dependency produces
a `C207` issue. When `check_conformance` is enabled, a `certification-demo` with
no resolved `conformance-report` dependency produces a `C208` issue. When
`check_reproducible` is enabled, a `certification-demo` with no resolved
`reproducible-build` dependency produces a `C209` issue. When `check_lockfile` is
enabled, a `certification-demo` with no resolved `lockfile` dependency produces
a `C210` issue. When `check_registry` is enabled, a `certification-demo` with no
resolved `registry-package` dependency produces a `C211` issue. When
`check_migration` is enabled, a `certification-demo` with no resolved
`migration-guide` dependency produces a `C212` issue. All issues are sorted by
code, path, and message. Incomplete state starts from paths whose digest is new
or changed relative to supplied state, with `new` or `changed` reasons, and
propagates a `dependency` reason to dependents through a stable queue. Packages
are emitted in a deterministic topological order.

`load_certified_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_certified_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`certified_pack_report()` summarizes plan count, package and incomplete counts,
error count, per-plan evidence, and a recomputable digest.
`certified_pack_gate()` verifies the version, format, gate shape, report and
plan digests, package and issue fingerprints, count consistency, and profile,
then recomputes PASS/FAIL from the reported error count, incomplete count, and
incomplete-failure policy. Extra fields such as CLI decisions are ignored by
digest recomputation.

The `pea certified-pack ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-signature]
[--no-check-provenance] [--no-check-conformance] [--no-check-reproducible]
[--no-check-lockfile] [--no-check-registry] [--no-check-migration]
[--fail-on-incomplete] [--current-version V]` command reports certification
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea certified-pack --capabilities` prints the versioned
capability set. The `sector.certified_pack` feature flag records availability.
