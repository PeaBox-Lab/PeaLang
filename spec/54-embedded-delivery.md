# Embedded and IoT delivery evidence

Phase 111 continues Wave 7 with a deterministic embedded and IoT delivery evidence sector pack
at version 5.11.0. It is additive to the release governance, capacity,
chaos, SLO, observability, and certified-package surfaces, and it does not
change the frozen 3.0 language surface.

`embedded_delivery_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.embedded.json` source filter, the sorted
kinds, stable ordering, and a recomputed gate. `EMBEDDED_DELIVERY_VERSION` records the
current release and `EMBEDDED_DELIVERY_FORMAT` identifies the sector-pack format.

`EmbeddedDeliveryProfileV2` is a frozen, validated profile with a positive
`max_entries` limit, an `include_preview` switch, `check_nogc`, `check_abi`, `check_rtos`, `check_binary`, `check_gpio`, `check_update`, `check_safety`
switches, a `fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `EMBEDDED_DELIVERY_VERSION`. Invalid profiles raise
`EmbeddedDeliveryPackError` before any planning occurs.
`DEFAULT_EMBEDDED_DELIVERY_PROFILE` is stable and serializable.

`plan_embedded_delivery()` discovers manifests under a root while skipping build and
cache directories. Preview, canary, and experimental directories are skipped
unless `include_preview` is enabled. Each manifest must declare a lowercase
`name`, a string `version`, a `kind` drawn from `no-gc-profile`, `c-abi`, `rtos-binding`, `static-binary`, `gpio-api`, `signed-update`, `safety-audit`, `resource`, `firmware-demo`, a non-empty sorted set
of `evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `F204` issue. Every declared
evidence path must resolve to a file under the root, or an `F205`
issue is produced. Each `EmbeddedDeliveryAppV2` carries a relative path, a manifest
content digest, the name, version, kind, sorted evidence paths, sorted platform
bindings, sorted required names, sorted resolved dependencies, a clean/stale
state, and reasons. A dependency is resolved through the provider set of a
required name. Wall-clock values and absolute host paths never enter the plan.

A required entry with no provider produces an `F201` issue; a dependency
cycle produces an `F202` issue; and exceeding the entry limit produces
an `F203` issue. When `check_nogc` is enabled, a `firmware-demo` with no resolved `no-gc-profile` dependency produces an `F206` issue.
When `check_abi` is enabled, a `firmware-demo` with no resolved `c-abi` dependency produces an `F207` issue.
When `check_rtos` is enabled, a `firmware-demo` with no resolved `rtos-binding` dependency produces an `F208` issue.
When `check_binary` is enabled, a `firmware-demo` with no resolved `static-binary` dependency produces an `F209` issue.
When `check_gpio` is enabled, a `firmware-demo` with no resolved `gpio-api` dependency produces an `F210` issue.
When `check_update` is enabled, a `firmware-demo` with no resolved `signed-update` dependency produces an `F211` issue.
When `check_safety` is enabled, a `firmware-demo` with no resolved `safety-audit` dependency produces an `F212` issue. All issues are sorted by code, path,
and message. Incomplete state starts from paths whose digest is new or changed
relative to supplied state, with `new` or `changed` reasons, and propagates a
`dependency` reason to dependents through a stable queue. Entries are emitted in
a deterministic topological order.

`load_embedded_delivery_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_embedded_delivery_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`embedded_delivery_report()` summarizes plan count, entry and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `embedded_delivery_gate()` verifies
the version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea embedded-delivery ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-entries N] [--include-preview] [--no-check-nogc] [--no-check-abi] [--no-check-rtos] [--no-check-binary] [--no-check-gpio] [--no-check-update] [--no-check-safety]
[--fail-on-incomplete] [--current-version V]` command reports embedded delivery
evidence without creating or modifying project files. `--check` requires a
passing gate, `--emit` writes the JSON report, and `--write-state` persists the
digest state. `pea embedded-delivery --capabilities` prints the versioned capability
set. The `sector.embedded_delivery` feature flag records availability. Stable issue codes are
`F206`, `F207`, `F208`, `F209`, `F210`, `F211`, `F212` for the required evidence checks, alongside the structural codes
`F201`–`F205`.
