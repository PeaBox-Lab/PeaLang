# Stable 1.0 declaration and GA evidence bundle

Phase 120 continues Wave 8 with a deterministic stable 1.0 declaration and GA evidence bundle sector pack
at version 5.20.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`stable_declaration_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.declaration.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `STABLE_DECLARATION_VERSION` records the
current release and `STABLE_DECLARATION_FORMAT` identifies the sector-pack format.

`StableDeclarationProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_final`, `check_pre_v1`, `check_maturity`, `check_candidate`, `check_attestation`, `check_approval`, `check_declaration`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `STABLE_DECLARATION_VERSION`. Invalid profiles raise
`StableDeclarationPackError` before any planning occurs.
`DEFAULT_STABLE_DECLARATION_PROFILE` is stable and serializable.

`plan_stable_declaration()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `final-gate`, `pre-v1-evidence`, `maturity-report`, `candidate-report`, `attestation-report`, `approval-signature`, `ga-declaration`, `resource`, `ga-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `SD204` issue. Every declared
evidence path must resolve to a file under the root, or an `SD205`
issue is produced. Each `StableDeclarationAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `SD201` issue; a dependency
cycle produces an `SD202` issue; and exceeding the entry limit produces
an `SD203` issue. When `check_final` is enabled, a `ga-demo` with no resolved `final-gate` dependency produces an `SD206` issue.
When `check_pre_v1` is enabled, a `ga-demo` with no resolved `pre-v1-evidence` dependency produces an `SD207` issue.
When `check_maturity` is enabled, a `ga-demo` with no resolved `maturity-report` dependency produces an `SD208` issue.
When `check_candidate` is enabled, a `ga-demo` with no resolved `candidate-report` dependency produces an `SD209` issue.
When `check_attestation` is enabled, a `ga-demo` with no resolved `attestation-report` dependency produces an `SD210` issue.
When `check_approval` is enabled, a `ga-demo` with no resolved `approval-signature` dependency produces an `SD211` issue.
When `check_declaration` is enabled, a `ga-demo` with no resolved `ga-declaration` dependency produces an `SD212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_stable_declaration_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_stable_declaration_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`stable_declaration_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `stable_declaration_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea stable-declaration ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-final] [--no-check-pre-v1] [--no-check-maturity] [--no-check-candidate] [--no-check-attestation] [--no-check-approval] [--no-check-declaration]
[--fail-on-incomplete] [--current-version V]` command reports stable declaration
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea stable-declaration --capabilities` prints the versioned capability
set. The `sector.stable_declaration` feature flag records availability. Stable issue codes are
`SD206`, `SD207`, `SD208`, `SD209`, `SD210`, `SD211`, `SD212` for the required evidence checks, alongside the structural codes
`SD201`–`SD205`.
