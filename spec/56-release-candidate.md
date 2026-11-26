# Release candidate and stable 1.0 evidence gate

Phase 113 continues Wave 7 with a deterministic release candidate and stable 1.0 evidence sector pack
at version 5.13.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`release_candidate_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.candidate.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `RELEASE_CANDIDATE_VERSION` records the
current release and `RELEASE_CANDIDATE_FORMAT` identifies the sector-pack format.

`ReleaseCandidateProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_candidate`, `check_dossier`, `check_signatures`, `check_matrix`, `check_upgrade`, `check_rollback`, `check_approval`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `RELEASE_CANDIDATE_VERSION`. Invalid profiles raise
`ReleaseCandidatePackError` before any planning occurs.
`DEFAULT_RELEASE_CANDIDATE_PROFILE` is stable and serializable.

`plan_release_candidate()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `candidate-build`, `evidence-dossier`, `signed-artifact`, `rc-platform-matrix`, `upgrade-test`, `rollback-test`, `go-decision`, `resource`, `candidate-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `H204` issue. Every declared
evidence path must resolve to a file under the root, or an `H205`
issue is produced. Each `ReleaseCandidateAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `H201` issue; a dependency
cycle produces an `H202` issue; and exceeding the entry limit produces
an `H203` issue. When `check_candidate` is enabled, a `candidate-demo` with no resolved `candidate-build` dependency produces an `H206` issue.
When `check_dossier` is enabled, a `candidate-demo` with no resolved `evidence-dossier` dependency produces an `H207` issue.
When `check_signatures` is enabled, a `candidate-demo` with no resolved `signed-artifact` dependency produces an `H208` issue.
When `check_matrix` is enabled, a `candidate-demo` with no resolved `rc-platform-matrix` dependency produces an `H209` issue.
When `check_upgrade` is enabled, a `candidate-demo` with no resolved `upgrade-test` dependency produces an `H210` issue.
When `check_rollback` is enabled, a `candidate-demo` with no resolved `rollback-test` dependency produces an `H211` issue.
When `check_approval` is enabled, a `candidate-demo` with no resolved `go-decision` dependency produces an `H212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_release_candidate_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_release_candidate_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`release_candidate_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `release_candidate_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea release-candidate ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-candidate] [--no-check-dossier] [--no-check-signatures] [--no-check-matrix] [--no-check-upgrade] [--no-check-rollback] [--no-check-approval]
[--fail-on-incomplete] [--current-version V]` command reports release candidate
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea release-candidate --capabilities` prints the versioned capability
set. The `sector.release_candidate` feature flag records availability. Stable issue codes are
`H206`, `H207`, `H208`, `H209`, `H210`, `H211`, `H212` for the required evidence checks, alongside the structural codes
`H201`–`H205`.
