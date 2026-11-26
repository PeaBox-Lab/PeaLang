# CI evidence ingest and matrix verification

Phase 114 continues Wave 8 with a deterministic CI evidence ingest and matrix verification sector pack
at version 5.14.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`ci_evidence_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.ci.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `CI_EVIDENCE_VERSION` records the
current release and `CI_EVIDENCE_FORMAT` identifies the sector-pack format.

`CIEvidenceProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_run`, `check_cells`, `check_commit`, `check_pytest`, `check_scanners`, `check_hashes`, `check_coverage`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `CI_EVIDENCE_VERSION`. Invalid profiles raise
`CIEvidencePackError` before any planning occurs.
`DEFAULT_CI_EVIDENCE_PROFILE` is stable and serializable.

`plan_ci_evidence()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `ci-run`, `platform-cell`, `commit-binding`, `pytest-report`, `scanner-report`, `artifact-hash`, `cell-coverage`, `resource`, `ci-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `CI204` issue. Every declared
evidence path must resolve to a file under the root, or an `CI205`
issue is produced. Each `CIEvidenceAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `CI201` issue; a dependency
cycle produces an `CI202` issue; and exceeding the entry limit produces
an `CI203` issue. When `check_run` is enabled, a `ci-demo` with no resolved `ci-run` dependency produces an `CI206` issue.
When `check_cells` is enabled, a `ci-demo` with no resolved `platform-cell` dependency produces an `CI207` issue.
When `check_commit` is enabled, a `ci-demo` with no resolved `commit-binding` dependency produces an `CI208` issue.
When `check_pytest` is enabled, a `ci-demo` with no resolved `pytest-report` dependency produces an `CI209` issue.
When `check_scanners` is enabled, a `ci-demo` with no resolved `scanner-report` dependency produces an `CI210` issue.
When `check_hashes` is enabled, a `ci-demo` with no resolved `artifact-hash` dependency produces an `CI211` issue.
When `check_coverage` is enabled, a `ci-demo` with no resolved `cell-coverage` dependency produces an `CI212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_ci_evidence_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_ci_evidence_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`ci_evidence_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `ci_evidence_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea ci-evidence ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-run] [--no-check-cells] [--no-check-commit] [--no-check-pytest] [--no-check-scanners] [--no-check-hashes] [--no-check-coverage]
[--fail-on-incomplete] [--current-version V]` command reports CI evidence
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea ci-evidence --capabilities` prints the versioned capability
set. The `sector.ci_evidence` feature flag records availability. Stable issue codes are
`CI206`, `CI207`, `CI208`, `CI209`, `CI210`, `CI211`, `CI212` for the required evidence checks, alongside the structural codes
`CI201`–`CI205`.
