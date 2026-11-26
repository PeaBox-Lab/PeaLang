# Incremental build system v2

Wave 3 continues with an additive incremental build system v2 layer. It does not
change the frozen 3.0 language surface, and it does not replace the existing
`pea build` command or library packaging; both remain available.

`build_system_v2_capabilities()` returns the versioned capability set with the
default profile, supported options, the `*.pea` source filter, import-declared
dependencies, stable ordering, and a recomputed gate.
`BUILD_SYSTEM_V2_VERSION` records the current release and
`BUILD_SYSTEM_V2_FORMAT` identifies the evidence format.

`BuildProfileV2` is a frozen, validated profile with a positive `max_files`
limit, an `include_tests` switch, a `check_imports` switch, and a `fail_on_dirty`
policy. Invalid profiles raise `BuildSystemV2Error` before any planning occurs.
`DEFAULT_BUILD_PROFILE` is stable and serializable.

`plan_build_v2()` discovers `.pea` sources under a root while skipping build,
cache, and test directories according to the profile. It hashes raw file bytes,
parses `import "module"` declarations, and resolves them to canonical module
paths. Each `BuildNodeV2` carries a relative path, a content digest, import
names, resolved dependencies, a clean/stale state, and reasons. Missing imports
produce `B201` issues, dependency cycles produce canonicalized `B202` issues, and
exceeding the file limit produces a `B203` issue; all issues are sorted by code,
path, and message. Wall-clock values and absolute host paths never enter the
plan.

Build order is a stable topological order: dependencies precede dependents, and
ready nodes are popped in lexicographic order. Dirty state starts from paths
whose digest is new or changed relative to supplied state, then propagates along
reverse dependency edges with a `dependency` reason.

`load_build_state_v2()` reads versioned digest state, returning empty state for
an absent file and rejecting invalid version, JSON, or shape.
`write_build_state_v2()` persists a deterministic digest map keyed by relative
path, with no absolute host paths.

`build_v2_report()` summarizes plan count, node and dirty counts, error count,
per-plan evidence, and a recomputable digest. `build_v2_gate()` verifies the
version, format, gate shape, report and plan digests, node and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, dirty count, and dirty-failure policy. Extra fields such
as CLI decisions are ignored by digest recomputation.

The `pea build-v2 ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-files N] [--include-tests] [--fail-on-dirty]` command
reports a build plan without packaging or changing source. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea build-v2 --capabilities` prints the versioned capability set.
The `devx.incremental_build_v2` feature flag records availability.
