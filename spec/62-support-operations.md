# Support and operations readiness evidence

Phase 119 continues Wave 8 with a deterministic support and operations readiness evidence sector pack
at version 5.19.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`support_operations_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.support.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `SUPPORT_OPERATIONS_VERSION` records the
current release and `SUPPORT_OPERATIONS_FORMAT` identifies the sector-pack format.

`SupportOperationsProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_policy`, `check_incident`, `check_rollback`, `check_owner`, `check_drill`, `check_sla`, `check_escalation`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `SUPPORT_OPERATIONS_VERSION`. Invalid profiles raise
`SupportOperationsPackError` before any planning occurs.
`DEFAULT_SUPPORT_OPERATIONS_PROFILE` is stable and serializable.

`plan_support_operations()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `support-policy`, `incident-runbook`, `rollback-playbook`, `owner-assignment`, `drill-evidence`, `sla-rto-target`, `escalation-policy`, `resource`, `support-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `SO204` issue. Every declared
evidence path must resolve to a file under the root, or an `SO205`
issue is produced. Each `SupportOperationsAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `SO201` issue; a dependency
cycle produces an `SO202` issue; and exceeding the entry limit produces
an `SO203` issue. When `check_policy` is enabled, a `support-demo` with no resolved `support-policy` dependency produces an `SO206` issue.
When `check_incident` is enabled, a `support-demo` with no resolved `incident-runbook` dependency produces an `SO207` issue.
When `check_rollback` is enabled, a `support-demo` with no resolved `rollback-playbook` dependency produces an `SO208` issue.
When `check_owner` is enabled, a `support-demo` with no resolved `owner-assignment` dependency produces an `SO209` issue.
When `check_drill` is enabled, a `support-demo` with no resolved `drill-evidence` dependency produces an `SO210` issue.
When `check_sla` is enabled, a `support-demo` with no resolved `sla-rto-target` dependency produces an `SO211` issue.
When `check_escalation` is enabled, a `support-demo` with no resolved `escalation-policy` dependency produces an `SO212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_support_operations_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_support_operations_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`support_operations_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `support_operations_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea support-operations ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-policy] [--no-check-incident] [--no-check-rollback] [--no-check-owner] [--no-check-drill] [--no-check-sla] [--no-check-escalation]
[--fail-on-incomplete] [--current-version V]` command reports support operations
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea support-operations --capabilities` prints the versioned capability
set. The `sector.support_operations` feature flag records availability. Stable issue codes are
`SO206`, `SO207`, `SO208`, `SO209`, `SO210`, `SO211`, `SO212` for the required evidence checks, alongside the structural codes
`SO201`–`SO205`.
