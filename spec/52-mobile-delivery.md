# Mobile delivery evidence

Phase 109 continues Wave 7 with a deterministic mobile delivery evidence sector pack
at version 5.9.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`mobile_delivery_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.mobile.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `MOBILE_DELIVERY_VERSION` records the
current release and `MOBILE_DELIVERY_FORMAT` identifies the sector-pack format.

`MobileDeliveryProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_android`, `check_ios`, `check_lifecycle`, `check_sdk`, `check_sample`, `check_pipeline`, `check_devices`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `MOBILE_DELIVERY_VERSION`. Invalid profiles raise
`MobileDeliveryPackError` before any planning occurs.
`DEFAULT_MOBILE_DELIVERY_PROFILE` is stable and serializable.

`plan_mobile_delivery()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `android-bridge`, `ios-bridge`, `lifecycle-binding`, `sdk-bundle`, `sample-app`, `build-pipeline`, `device-matrix`, `resource`, `mobile-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `B204` issue. Every declared
evidence path must resolve to a file under the root, or an `B205`
issue is produced. Each `MobileDeliveryAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `B201` issue; a dependency
cycle produces an `B202` issue; and exceeding the entry limit produces
an `B203` issue. When `check_android` is enabled, a `mobile-demo` with no resolved `android-bridge` dependency produces an `B206` issue.
When `check_ios` is enabled, a `mobile-demo` with no resolved `ios-bridge` dependency produces an `B207` issue.
When `check_lifecycle` is enabled, a `mobile-demo` with no resolved `lifecycle-binding` dependency produces an `B208` issue.
When `check_sdk` is enabled, a `mobile-demo` with no resolved `sdk-bundle` dependency produces an `B209` issue.
When `check_sample` is enabled, a `mobile-demo` with no resolved `sample-app` dependency produces an `B210` issue.
When `check_pipeline` is enabled, a `mobile-demo` with no resolved `build-pipeline` dependency produces an `B211` issue.
When `check_devices` is enabled, a `mobile-demo` with no resolved `device-matrix` dependency produces an `B212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_mobile_delivery_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_mobile_delivery_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`mobile_delivery_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `mobile_delivery_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea mobile-delivery ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-android] [--no-check-ios] [--no-check-lifecycle] [--no-check-sdk] [--no-check-sample] [--no-check-pipeline] [--no-check-devices]
[--fail-on-incomplete] [--current-version V]` command reports mobile delivery
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea mobile-delivery --capabilities` prints the versioned capability
set. The `sector.mobile_delivery` feature flag records availability. Stable issue codes are
`B206`, `B207`, `B208`, `B209`, `B210`, `B211`, `B212` for the required evidence checks, alongside the structural codes
`B201`–`B205`.
