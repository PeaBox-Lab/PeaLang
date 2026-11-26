# Data Science / AI / ML sector pack

Wave 4 continues with a deterministic sector-pack evidence gate for the data,
analytics, and ML row of the sector table. It is additive to `analysis.py`,
`timeseries.py`, `forecasting.py`, `ai_ml.py`, `jupyter_kernel.py`,
`serving_runtime.py`, `std.analysis`, and `std.stats`, and it does not change the
frozen 3.0 language surface.

`data_pack_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.ds.json` source filter, the sorted workflow
kinds, stable ordering, and a recomputed gate. `DATA_PACK_VERSION` records the
current release and `DATA_PACK_FORMAT` identifies the sector-pack format.

`DataProfileV2` is a frozen, validated profile with a positive `max_workflows`
limit, an `include_preview` switch, a `check_parity` switch, a
`check_benchmarks` switch, a `fail_on_incomplete` policy, and a
`current_version` string. An empty `current_version` resolves to
`DATA_PACK_VERSION`. Invalid profiles raise `DataPackError` before any planning
occurs. `DEFAULT_DATA_PROFILE` is stable and serializable.

`plan_data_pack()` discovers workflows under a root while skipping build and
cache directories. Preview, experimental, and incubator directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `DATA_KINDS`, a non-empty sorted
set of `evidence` artifacts, and string lists for `requires` and `metrics`;
invalid manifests produce an `S204` issue. Every declared evidence path must
resolve to a file under the root, or an `S205` issue is produced. Each
`DataWorkflowV2` carries a relative path, a manifest content digest, the name,
version, kind, sorted evidence paths, sorted required names, sorted published
metrics, sorted resolved dependencies, a clean/stale state, and reasons. A
dependency is resolved through the provider set of a required workflow name.
Wall-clock values and absolute host paths never enter the plan.

A required workflow with no provider produces an `S201` issue; a dependency
cycle produces an `S202` issue; and exceeding the workflow limit produces an
`S203` issue. When `check_parity` is enabled, a `pipeline` workflow with no
resolved `parity-suite` dependency produces an `S206` issue. When
`check_benchmarks` is enabled, a `model` workflow with no resolved `benchmark`
dependency produces an `S207` issue. All issues are sorted by code, path, and
message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Workflows are emitted
in a deterministic topological order.

`load_data_state_v2()` reads versioned digest state, returning empty state for
an absent file and rejecting invalid version, JSON, or shape.
`write_data_state_v2()` persists a deterministic digest map keyed by relative
path, with no absolute host paths.

`data_pack_report()` summarizes plan count, workflow and incomplete counts,
error count, per-plan evidence, and a recomputable digest. `data_pack_gate()`
verifies the version, format, gate shape, report and plan digests, workflow and
issue fingerprints, count consistency, and profile, then recomputes PASS/FAIL
from the reported error count, incomplete count, and incomplete-failure policy.
Extra fields such as CLI decisions are ignored by digest recomputation.

The `pea data-pack ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-workflows N] [--include-preview] [--no-check-parity]
[--no-check-benchmarks] [--fail-on-incomplete] [--current-version V]` command
reports workflow evidence without creating or modifying project files.
`--check` requires a passing gate, `--emit` writes the JSON report, and
`--write-state` persists the digest state. `pea data-pack --capabilities` prints
the versioned capability set. The `sector.data_science_pack` feature flag
records availability.
