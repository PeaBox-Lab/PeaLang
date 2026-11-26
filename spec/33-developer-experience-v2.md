# Developer experience v2

Wave 3 closes with a deterministic developer-experience evidence gate. It is
additive to all existing editor, debug, format, lint, test, build, docs,
migration, and template tooling, and it does not change the frozen 3.0 language
surface.

`devex_v2_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.devx.json` source filter, stable ordering,
and a recomputed gate. `DEVEX_V2_VERSION` records the current release and
`DEVEX_V2_FORMAT` identifies the evidence format.

`DevExProfileV2` is a frozen, validated profile with a positive `max_tools`
limit, an `include_experimental` switch, a `check_evidence` switch, a
`fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `DEVEX_V2_VERSION`. Invalid profiles raise
`DevExV2Error` before any planning occurs. `DEFAULT_DEVEX_PROFILE` is stable and
serializable.

`plan_devex_v2()` discovers developer-tool manifests under a root while
skipping build and cache directories. Experimental, preview, and incubator
directories are skipped unless `include_experimental` is enabled. Each manifest
must declare a lowercase `name`, a string `version`, a string `format`, a
non-empty sorted set of `evidence` artifacts, and string lists for `requires`
and `checks`; invalid manifests produce a `D204` issue. When `check_evidence` is
enabled, every declared evidence path must resolve to a file under the root, or
a `D205` issue is produced. Each `DevExToolV2` carries a relative path, a
manifest content digest, the name, version, format, sorted evidence paths,
sorted required names, sorted checks, sorted resolved dependencies, a
clean/stale state, and reasons. A dependency is resolved through the provider
set of a required tool name. Wall-clock values and absolute host paths never
enter the plan.

A required tool with no provider produces a `D201` issue when `check_evidence`
is enabled; a dependency cycle produces a `D202` issue; and exceeding the tool
limit produces a `D203` issue. All issues are sorted by code, path, and message.
Incomplete state starts from paths whose digest is new or changed relative to
supplied state, with `new` or `changed` reasons, and propagates a `dependency`
reason to dependents through a stable queue. Tools are emitted in a
deterministic topological order.

`load_devex_state_v2()` reads versioned digest state, returning empty state for
an absent file and rejecting invalid version, JSON, or shape.
`write_devex_state_v2()` persists a deterministic digest map keyed by relative
path, with no absolute host paths.

`devex_v2_report()` summarizes plan count, tool and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `devex_v2_gate()` verifies
the version, format, gate shape, report and plan digests, tool and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea devex-v2 ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-tools N] [--include-experimental] [--no-check-evidence]
[--fail-on-incomplete] [--current-version V]` command reports developer-tool
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea devex-v2 --capabilities` prints the versioned capability set.
The `devx.devex_v2` feature flag records availability.
