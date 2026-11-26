# Observability and SRE sector pack

Wave 6 opens with a deterministic observability and production-reliability sector
pack at version 5.1.0. It is additive to the runtime profiler, performance-gate,
and certified-package surfaces, and it does not change the frozen 3.0 language
surface.

`observability_pack_capabilities()` returns the versioned capability set with the
default profile, supported options, the `*.observability.json` source filter, the
sorted reliability kinds, stable ordering, and a recomputed gate.
`OBSERVABILITY_PACK_VERSION` records the current release and
`OBSERVABILITY_PACK_FORMAT` identifies the sector-pack format.

`ObservabilityProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, a `check_trace` switch, a
`check_metric` switch, a `check_log` switch, a `check_slo` switch, a
`check_alert` switch, a `check_runbook` switch, a `check_dashboard` switch, a
`fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `OBSERVABILITY_PACK_VERSION`. Invalid profiles
raise `ObservabilityPackError` before any planning occurs.
`DEFAULT_OBSERVABILITY_PROFILE` is stable and serializable.

`plan_observability_pack()` discovers reliability manifests under a root while
skipping build and cache directories. Preview, canary, and experimental
directories are skipped unless `include_preview` is enabled. Each manifest must
declare a lowercase `name`, a string `version`, a `kind` drawn from
`OBSERVABILITY_KINDS`, a non-empty sorted set of `evidence` artifacts, string
lists for `requires`, and string lists for `bindings`; invalid manifests produce
an `O204` issue. Every declared evidence path must resolve to a file under the
root, or an `O205` issue is produced. Each `ObservabilityAppV2` carries a relative
path, a manifest content digest, the name, version, kind, sorted evidence paths,
sorted platform bindings, sorted required names, sorted resolved dependencies, a
clean/stale state, and reasons. A dependency is resolved through the provider set
of a required name. Wall-clock values and absolute host paths never enter the
plan.

A required entry with no provider produces an `O201` issue; a dependency cycle
produces an `O202` issue; and exceeding the entry limit produces an `O203` issue.
When `check_trace` is enabled, a `reliability-demo` with no resolved `trace`
dependency produces an `O206` issue. When `check_metric` is enabled, a
`reliability-demo` with no resolved `metric` dependency produces an `O207` issue.
When `check_log` is enabled, a `reliability-demo` with no resolved `log`
dependency produces an `O208` issue. When `check_slo` is enabled, a
`reliability-demo` with no resolved `slo` dependency produces an `O209` issue.
When `check_alert` is enabled, a `reliability-demo` with no resolved
`alert-policy` dependency produces an `O210` issue. When `check_runbook` is
enabled, a `reliability-demo` with no resolved `incident-runbook` dependency
produces an `O211` issue. When `check_dashboard` is enabled, a
`reliability-demo` with no resolved `dashboard` dependency produces an `O212`
issue. All issues are sorted by code, path, and message. Incomplete state starts
from paths whose digest is new or changed relative to supplied state, with `new`
or `changed` reasons, and propagates a `dependency` reason to dependents through
a stable queue. Entries are emitted in a deterministic topological order.

`load_observability_state_v2()` reads versioned digest state, returning empty
state for an absent file and rejecting invalid version, JSON, or shape.
`write_observability_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`observability_pack_report()` summarizes plan count, entry and incomplete counts,
error count, per-plan evidence, and a recomputable digest.
`observability_pack_gate()` verifies the version, format, gate shape, report and
plan digests, entry and issue fingerprints, count consistency, and profile, then
recomputes PASS/FAIL from the reported error count, incomplete count, and
incomplete-failure policy. Extra fields such as CLI decisions are ignored by
digest recomputation.

The `pea observability-pack ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-trace]
[--no-check-metric] [--no-check-log] [--no-check-slo] [--no-check-alert]
[--no-check-runbook] [--no-check-dashboard] [--fail-on-incomplete]
[--current-version V]` command reports reliability evidence without creating or
modifying project files. `--check` requires a passing gate, `--emit` writes the
JSON report, and `--write-state` persists the digest state.
`pea observability-pack --capabilities` prints the versioned capability set. The
`sector.observability_pack` feature flag records availability.
