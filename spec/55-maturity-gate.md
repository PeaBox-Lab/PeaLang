# Wave 7 maturity and consolidation gate

Phase 112 continues Wave 7 with a deterministic Wave 7 maturity and consolidation sector pack
at version 5.12.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`maturity_gate_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.maturity.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `MATURITY_GATE_VERSION` records the
current release and `MATURITY_GATE_FORMAT` identifies the sector-pack format.

`MaturityGateProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_trust`, `check_safety`, `check_conformance`, `check_sector`, `check_pilot`, `check_security`, `check_freeze`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `MATURITY_GATE_VERSION`. Invalid profiles raise
`MaturityGatePackError` before any planning occurs.
`DEFAULT_MATURITY_GATE_PROFILE` is stable and serializable.

`plan_maturity_gate()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `trust-gate`, `safety-gate`, `conformance-gate`, `sector-gate`, `pilot-gate`, `security-review`, `version-freeze`, `resource`, `maturity-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `Z204` issue. Every declared
evidence path must resolve to a file under the root, or an `Z205`
issue is produced. Each `MaturityGateAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `Z201` issue; a dependency
cycle produces an `Z202` issue; and exceeding the entry limit produces
an `Z203` issue. When `check_trust` is enabled, a `maturity-demo` with no resolved `trust-gate` dependency produces an `Z206` issue.
When `check_safety` is enabled, a `maturity-demo` with no resolved `safety-gate` dependency produces an `Z207` issue.
When `check_conformance` is enabled, a `maturity-demo` with no resolved `conformance-gate` dependency produces an `Z208` issue.
When `check_sector` is enabled, a `maturity-demo` with no resolved `sector-gate` dependency produces an `Z209` issue.
When `check_pilot` is enabled, a `maturity-demo` with no resolved `pilot-gate` dependency produces an `Z210` issue.
When `check_security` is enabled, a `maturity-demo` with no resolved `security-review` dependency produces an `Z211` issue.
When `check_freeze` is enabled, a `maturity-demo` with no resolved `version-freeze` dependency produces an `Z212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_maturity_gate_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_maturity_gate_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`maturity_gate_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `maturity_gate_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea maturity-gate ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-trust] [--no-check-safety] [--no-check-conformance] [--no-check-sector] [--no-check-pilot] [--no-check-security] [--no-check-freeze]
[--fail-on-incomplete] [--current-version V]` command reports maturity gate
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea maturity-gate --capabilities` prints the versioned capability
set. The `sector.maturity_gate` feature flag records availability. Stable issue codes are
`Z206`, `Z207`, `Z208`, `Z209`, `Z210`, `Z211`, `Z212` for the required evidence checks, alongside the structural codes
`Z201`–`Z205`.
