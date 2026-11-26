# Cross-platform CI and production pilot evidence

Phase 108 continues Wave 7 with a deterministic cross-platform CI and production pilot evidence sector pack
at version 5.8.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`pilot_evidence_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.pilot.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `PILOT_EVIDENCE_VERSION` records the
current release and `PILOT_EVIDENCE_FORMAT` identifies the sector-pack format.

`PilotEvidenceProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_matrix`, `check_ci`, `check_coverage`, `check_security`, `check_pilot`, `check_host`, `check_baseline`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `PILOT_EVIDENCE_VERSION`. Invalid profiles raise
`PilotEvidencePackError` before any planning occurs.
`DEFAULT_PILOT_EVIDENCE_PROFILE` is stable and serializable.

`plan_pilot_evidence()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `platform-matrix`, `ci-run`, `coverage-report`, `security-review`, `pilot-app`, `host-integration`, `performance-baseline`, `resource`, `pilot-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `V204` issue. Every declared
evidence path must resolve to a file under the root, or an `V205`
issue is produced. Each `PilotEvidenceAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `V201` issue; a dependency
cycle produces an `V202` issue; and exceeding the entry limit produces
an `V203` issue. When `check_matrix` is enabled, a `pilot-demo` with no resolved `platform-matrix` dependency produces an `V206` issue.
When `check_ci` is enabled, a `pilot-demo` with no resolved `ci-run` dependency produces an `V207` issue.
When `check_coverage` is enabled, a `pilot-demo` with no resolved `coverage-report` dependency produces an `V208` issue.
When `check_security` is enabled, a `pilot-demo` with no resolved `security-review` dependency produces an `V209` issue.
When `check_pilot` is enabled, a `pilot-demo` with no resolved `pilot-app` dependency produces an `V210` issue.
When `check_host` is enabled, a `pilot-demo` with no resolved `host-integration` dependency produces an `V211` issue.
When `check_baseline` is enabled, a `pilot-demo` with no resolved `performance-baseline` dependency produces an `V212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_pilot_evidence_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_pilot_evidence_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`pilot_evidence_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `pilot_evidence_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea pilot-evidence ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-matrix] [--no-check-ci] [--no-check-coverage] [--no-check-security] [--no-check-pilot] [--no-check-host] [--no-check-baseline]
[--fail-on-incomplete] [--current-version V]` command reports pilot evidence
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea pilot-evidence --capabilities` prints the versioned capability
set. The `sector.pilot_evidence` feature flag records availability. Stable issue codes are
`V206`, `V207`, `V208`, `V209`, `V210`, `V211`, `V212` for the required evidence checks, alongside the structural codes
`V201`–`V205`.
