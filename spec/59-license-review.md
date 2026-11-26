# Third-party license review closure

Phase 116 continues Wave 8 with a deterministic third-party license review closure sector pack
at version 5.16.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`license_review_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.license.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `LICENSE_REVIEW_VERSION` records the
current release and `LICENSE_REVIEW_FORMAT` identifies the sector-pack format.

`LicenseReviewProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_inventory`, `check_policy`, `check_reviewer`, `check_approved`, `check_unknown`, `check_exception`, `check_evidence`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `LICENSE_REVIEW_VERSION`. Invalid profiles raise
`LicenseReviewPackError` before any planning occurs.
`DEFAULT_LICENSE_REVIEW_PROFILE` is stable and serializable.

`plan_license_review()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `license-inventory`, `license-policy`, `reviewer-decision`, `approved-license`, `unknown-license`, `exception-record`, `review-evidence`, `resource`, `license-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `LC204` issue. Every declared
evidence path must resolve to a file under the root, or an `LC205`
issue is produced. Each `LicenseReviewAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `LC201` issue; a dependency
cycle produces an `LC202` issue; and exceeding the entry limit produces
an `LC203` issue. When `check_inventory` is enabled, a `license-demo` with no resolved `license-inventory` dependency produces an `LC206` issue.
When `check_policy` is enabled, a `license-demo` with no resolved `license-policy` dependency produces an `LC207` issue.
When `check_reviewer` is enabled, a `license-demo` with no resolved `reviewer-decision` dependency produces an `LC208` issue.
When `check_approved` is enabled, a `license-demo` with no resolved `approved-license` dependency produces an `LC209` issue.
When `check_unknown` is enabled, a `license-demo` with no resolved `unknown-license` dependency produces an `LC210` issue.
When `check_exception` is enabled, a `license-demo` with no resolved `exception-record` dependency produces an `LC211` issue.
When `check_evidence` is enabled, a `license-demo` with no resolved `review-evidence` dependency produces an `LC212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_license_review_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_license_review_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`license_review_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `license_review_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea license-review ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-inventory] [--no-check-policy] [--no-check-reviewer] [--no-check-approved] [--no-check-unknown] [--no-check-exception] [--no-check-evidence]
[--fail-on-incomplete] [--current-version V]` command reports license review
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea license-review --capabilities` prints the versioned capability
set. The `sector.license_review` feature flag records availability. Stable issue codes are
`LC206`, `LC207`, `LC208`, `LC209`, `LC210`, `LC211`, `LC212` for the required evidence checks, alongside the structural codes
`LC201`–`LC205`.
