# Independent security review and soak evidence

Phase 118 continues Wave 8 with a deterministic independent security review and soak evidence sector pack
at version 5.18.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`security_soak_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.soak.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `SECURITY_SOAK_VERSION` records the
current release and `SECURITY_SOAK_FORMAT` identifies the sector-pack format.

`SecuritySoakProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_review`, `check_threat`, `check_fuzz`, `check_remediation`, `check_soak`, `check_load`, `check_slo`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `SECURITY_SOAK_VERSION`. Invalid profiles raise
`SecuritySoakPackError` before any planning occurs.
`DEFAULT_SECURITY_SOAK_PROFILE` is stable and serializable.

`plan_security_soak()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `security-review`, `threat-model`, `fuzz-corpus`, `remediation-log`, `soak-run`, `load-profile`, `slo-adherence`, `resource`, `soak-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `SS204` issue. Every declared
evidence path must resolve to a file under the root, or an `SS205`
issue is produced. Each `SecuritySoakAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `SS201` issue; a dependency
cycle produces an `SS202` issue; and exceeding the entry limit produces
an `SS203` issue. When `check_review` is enabled, a `soak-demo` with no resolved `security-review` dependency produces an `SS206` issue.
When `check_threat` is enabled, a `soak-demo` with no resolved `threat-model` dependency produces an `SS207` issue.
When `check_fuzz` is enabled, a `soak-demo` with no resolved `fuzz-corpus` dependency produces an `SS208` issue.
When `check_remediation` is enabled, a `soak-demo` with no resolved `remediation-log` dependency produces an `SS209` issue.
When `check_soak` is enabled, a `soak-demo` with no resolved `soak-run` dependency produces an `SS210` issue.
When `check_load` is enabled, a `soak-demo` with no resolved `load-profile` dependency produces an `SS211` issue.
When `check_slo` is enabled, a `soak-demo` with no resolved `slo-adherence` dependency produces an `SS212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_security_soak_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_security_soak_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`security_soak_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `security_soak_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea security-soak ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-review] [--no-check-threat] [--no-check-fuzz] [--no-check-remediation] [--no-check-soak] [--no-check-load] [--no-check-slo]
[--fail-on-incomplete] [--current-version V]` command reports security and soak
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea security-soak --capabilities` prints the versioned capability
set. The `sector.security_soak` feature flag records availability. Stable issue codes are
`SS206`, `SS207`, `SS208`, `SS209`, `SS210`, `SS211`, `SS212` for the required evidence checks, alongside the structural codes
`SS201`–`SS205`.
