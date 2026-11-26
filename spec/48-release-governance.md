# Release governance and change safety

Phase 105 continues Wave 6 with a deterministic release governance and change
safety sector pack at version 5.5.0. It is additive to the capacity, chaos, SLO,
observability pack, runtime profiler, performance-gate, and certified-package
surfaces, and it does not change the frozen 3.0 language surface.

`release_governance_capabilities()` returns the versioned capability set with
the default profile, supported options, the `*.release.json` source filter, the
sorted release kinds, stable ordering, and a recomputed gate.
`RELEASE_GOVERNANCE_VERSION` records the current release and
`RELEASE_GOVERNANCE_FORMAT` identifies the sector-pack format.

`ReleaseGovernanceProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, a `check_change` switch, a
`check_approval` switch, a `check_canary` switch, a `check_rollback` switch, a
`check_flag` switch, a `check_audit` switch, a `check_checklist` switch, a
`fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `RELEASE_GOVERNANCE_VERSION`. Invalid profiles
raise `ReleaseGovernancePackError` before any planning occurs.
`DEFAULT_RELEASE_GOVERNANCE_PROFILE` is stable and serializable.

`plan_release_governance()` discovers release manifests under a root while
skipping build and cache directories. Preview, canary, and experimental
directories are skipped unless `include_preview` is enabled. Each manifest must
declare a lowercase `name`, a string `version`, a `kind` drawn from
`RELEASE_GOVERNANCE_KINDS`, a non-empty sorted set of `evidence` artifacts,
string lists for `requires`, and string lists for `bindings`; invalid manifests
produce an `R204` issue. Every declared evidence path must resolve to a file
under the root, or an `R205` issue is produced. Each
`ReleaseGovernanceAppV2` carries a relative path, a manifest content digest, the
name, version, kind, sorted evidence paths, sorted platform bindings, sorted
required names, sorted resolved dependencies, a clean/stale state, and reasons.
A dependency is resolved through the provider set of a required name.
Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `R201` issue; a dependency cycle
produces an `R202` issue; and exceeding the entry limit produces an `R203`
issue. When `check_change` is enabled, a `release-demo` with no resolved
`change-record` dependency produces an `R206` issue. When `check_approval` is
enabled, a `release-demo` with no resolved `approval` dependency produces an
`R207` issue. When `check_canary` is enabled, a `release-demo` with no resolved
`canary-plan` dependency produces an `R208` issue. When `check_rollback` is
enabled, a `release-demo` with no resolved `rollback-plan` dependency produces
an `R209` issue. When `check_flag` is enabled, a `release-demo` with no resolved
`feature-flag` dependency produces an `R210` issue. When `check_audit` is
enabled, a `release-demo` with no resolved `audit-trail` dependency produces an
`R211` issue. When `check_checklist` is enabled, a `release-demo` with no
resolved `release-checklist` dependency produces an `R212` issue. All issues are
sorted by code, path, and message. Incomplete state starts from paths whose
digest is new or changed relative to supplied state, with `new` or `changed`
reasons, and propagates a `dependency` reason to dependents through a stable
queue. Entries are emitted in a deterministic topological order.

`load_release_governance_state_v2()` reads versioned digest state, returning
empty state for an absent file and rejecting invalid version, JSON, or shape.
`write_release_governance_state_v2()` persists a deterministic digest map keyed
by relative path, with no absolute host paths.

`release_governance_report()` summarizes plan count, entry and incomplete
counts, error count, per-plan evidence, and a recomputable digest.
`release_governance_gate()` verifies the version, format, gate shape, report and
plan digests, entry and issue fingerprints, count consistency, and profile,
then recomputes PASS/FAIL from the reported error count, incomplete count, and
incomplete-failure policy. Extra fields such as CLI decisions are ignored by
digest recomputation.

The `pea release-governance ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-change]
[--no-check-approval] [--no-check-canary] [--no-check-rollback]
[--no-check-flag] [--no-check-audit] [--no-check-checklist]
[--fail-on-incomplete] [--current-version V]` command reports release evidence
without creating or modifying project files. `--check` requires a passing gate,
`--emit` writes the JSON report, and `--write-state` persists the digest state.
`pea release-governance --capabilities` prints the versioned capability set.
The `sector.release_governance` feature flag records availability.
