# Agent safety and tool-use conformance

Phase 106 continues Wave 7 with a deterministic agent safety and tool-use conformance sector pack
at version 5.6.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`agent_safety_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.agent.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `AGENT_SAFETY_VERSION` records the
current release and `AGENT_SAFETY_FORMAT` identifies the sector-pack format.

`AgentSafetyProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_tool`, `check_dry_run`, `check_approval`, `check_replay`, `check_budget`, `check_audit`, `check_isolation`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `AGENT_SAFETY_VERSION`. Invalid profiles raise
`AgentSafetyPackError` before any planning occurs.
`DEFAULT_AGENT_SAFETY_PROFILE` is stable and serializable.

`plan_agent_safety()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `tool-policy`, `dry-run`, `approval-gate`, `replay-guard`, `budget`, `audit-log`, `isolation-policy`, `resource`, `agent-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `G204` issue. Every declared
evidence path must resolve to a file under the root, or an `G205`
issue is produced. Each `AgentSafetyAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `G201` issue; a dependency
cycle produces an `G202` issue; and exceeding the entry limit produces
an `G203` issue. When `check_tool` is enabled, a `agent-demo` with no resolved `tool-policy` dependency produces an `G206` issue.
When `check_dry_run` is enabled, a `agent-demo` with no resolved `dry-run` dependency produces an `G207` issue.
When `check_approval` is enabled, a `agent-demo` with no resolved `approval-gate` dependency produces an `G208` issue.
When `check_replay` is enabled, a `agent-demo` with no resolved `replay-guard` dependency produces an `G209` issue.
When `check_budget` is enabled, a `agent-demo` with no resolved `budget` dependency produces an `G210` issue.
When `check_audit` is enabled, a `agent-demo` with no resolved `audit-log` dependency produces an `G211` issue.
When `check_isolation` is enabled, a `agent-demo` with no resolved `isolation-policy` dependency produces an `G212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_agent_safety_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_agent_safety_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`agent_safety_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `agent_safety_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea agent-safety ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-tool] [--no-check-dry-run] [--no-check-approval] [--no-check-replay] [--no-check-budget] [--no-check-audit] [--no-check-isolation]
[--fail-on-incomplete] [--current-version V]` command reports agent safety
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea agent-safety --capabilities` prints the versioned capability
set. The `sector.agent_safety` feature flag records availability. Stable issue codes are
`G206`, `G207`, `G208`, `G209`, `G210`, `G211`, `G212` for the required evidence checks, alongside the structural codes
`G201`–`G205`.
