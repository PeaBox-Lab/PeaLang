# Release artifact attestation and provenance

Phase 115 continues Wave 8 with a deterministic release artifact attestation and provenance sector pack
at version 5.15.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`artifact_attestation_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.attestation.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `ARTIFACT_ATTESTATION_VERSION` records the
current release and `ARTIFACT_ATTESTATION_FORMAT` identifies the sector-pack format.

`ArtifactAttestationProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_wheel`, `check_sdist`, `check_container`, `check_sbom`, `check_provenance`, `check_signature`, `check_repro`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `ARTIFACT_ATTESTATION_VERSION`. Invalid profiles raise
`ArtifactAttestationPackError` before any planning occurs.
`DEFAULT_ARTIFACT_ATTESTATION_PROFILE` is stable and serializable.

`plan_artifact_attestation()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `wheel-digest`, `sdist-digest`, `container-manifest`, `sbom`, `provenance`, `signature`, `reproducibility`, `resource`, `artifact-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `AT204` issue. Every declared
evidence path must resolve to a file under the root, or an `AT205`
issue is produced. Each `ArtifactAttestationAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `AT201` issue; a dependency
cycle produces an `AT202` issue; and exceeding the entry limit produces
an `AT203` issue. When `check_wheel` is enabled, a `artifact-demo` with no resolved `wheel-digest` dependency produces an `AT206` issue.
When `check_sdist` is enabled, a `artifact-demo` with no resolved `sdist-digest` dependency produces an `AT207` issue.
When `check_container` is enabled, a `artifact-demo` with no resolved `container-manifest` dependency produces an `AT208` issue.
When `check_sbom` is enabled, a `artifact-demo` with no resolved `sbom` dependency produces an `AT209` issue.
When `check_provenance` is enabled, a `artifact-demo` with no resolved `provenance` dependency produces an `AT210` issue.
When `check_signature` is enabled, a `artifact-demo` with no resolved `signature` dependency produces an `AT211` issue.
When `check_repro` is enabled, a `artifact-demo` with no resolved `reproducibility` dependency produces an `AT212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_artifact_attestation_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_artifact_attestation_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`artifact_attestation_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `artifact_attestation_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea artifact-attestation ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-wheel] [--no-check-sdist] [--no-check-container] [--no-check-sbom] [--no-check-provenance] [--no-check-signature] [--no-check-repro]
[--fail-on-incomplete] [--current-version V]` command reports artifact attestation
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea artifact-attestation --capabilities` prints the versioned capability
set. The `sector.artifact_attestation` feature flag records availability. Stable issue codes are
`AT206`, `AT207`, `AT208`, `AT209`, `AT210`, `AT211`, `AT212` for the required evidence checks, alongside the structural codes
`AT201`–`AT205`.
