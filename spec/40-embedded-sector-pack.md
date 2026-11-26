# Embedded / IoT / OS sector pack

Wave 4 continues with a deterministic sector-pack evidence gate for the Embedded
/ IoT / OS row of the sector table. It is additive to `host_bindings.py`,
`vm_embedding.py`, and the Java client sidecar, and it does not change the frozen
3.0 language surface.

`embedded_pack_capabilities()` returns the versioned capability set with the
default profile, supported options, the `*.embedded.json` source filter, the
sorted firmware kinds, stable ordering, and a recomputed gate.
`EMBEDDED_PACK_VERSION` records the current release and `EMBEDDED_PACK_FORMAT`
identifies the sector-pack format.

`EmbeddedProfileV2` is a frozen, validated profile with a positive
`max_firmware` limit, an `include_preview` switch, a `check_native` switch, a
`check_c_abi` switch, a `check_rtos` switch, a `check_static` switch, a
`check_bus` switch, a `check_safety` switch, a `check_memory` switch, a
`check_signed` switch, a `fail_on_incomplete` policy, and a `current_version`
string. An empty `current_version` resolves to `EMBEDDED_PACK_VERSION`. Invalid
profiles raise `EmbeddedPackError` before any planning occurs.
`DEFAULT_EMBEDDED_PROFILE` is stable and serializable.

`plan_embedded_pack()` discovers firmware manifests under a root while skipping
build and cache directories. Preview, canary, and experimental directories are
skipped unless `include_preview` is enabled. Each manifest must declare a
lowercase `name`, a string `version`, a `kind` drawn from `EMBEDDED_KINDS`, a
non-empty sorted set of `evidence` artifacts, string lists for `requires`, and
string lists for `bindings`; invalid manifests produce an `E204` issue. Every
declared evidence path must resolve to a file under the root, or an `E205` issue
is produced. Each `EmbeddedAppV2` carries a relative path, a manifest content
digest, the name, version, kind, sorted evidence paths, sorted platform bindings,
sorted required names, sorted resolved dependencies, a clean/stale state, and
reasons. A dependency is resolved through the provider set of a required game
name. Wall-clock values and absolute host paths never enter the plan.

A required firmware app with no provider produces an `E201` issue; a dependency
cycle produces an `E202` issue; and exceeding the firmware limit produces an
`E203` issue. When `check_native` is enabled, a `firmware-demo` with no resolved
`native-profile` dependency produces an `E206` issue. When `check_c_abi` is
enabled, a `firmware-demo` with no resolved `c-abi` dependency produces an `E207`
issue. When `check_rtos` is enabled, a `firmware-demo` with no resolved
`rtos-binding` dependency produces an `E208` issue. When `check_static` is
enabled, a `firmware-demo` with no resolved `static-binary` dependency produces
an `E209` issue. When `check_bus` is enabled, a `firmware-demo` with no resolved
`gpio-api`, `i2c-api`, `spi-api`, or `can-api` dependency produces an `E210`
issue. When `check_safety` is enabled, a `firmware-demo` with no resolved
`safety-audit` dependency produces an `E211` issue. When `check_memory` is
enabled, a `firmware-demo` without a `bounded-memory` binding produces an `E212`
issue. When `check_signed` is enabled, a `firmware-demo` without a
`signed-update` binding produces an `E213` issue. All issues are sorted by code,
path, and message. Incomplete state starts from paths whose digest is new or
changed relative to supplied state, with `new` or `changed` reasons, and
propagates a `dependency` reason to dependents through a stable queue. Firmware
is emitted in a deterministic topological order.

`load_embedded_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_embedded_state_v2()` persists a deterministic digest map keyed by relative
path, with no absolute host paths.

`embedded_pack_report()` summarizes plan count, firmware and incomplete counts,
error count, per-plan evidence, and a recomputable digest. `embedded_pack_gate()`
verifies the version, format, gate shape, report and plan digests, firmware and
issue fingerprints, count consistency, and profile, then recomputes PASS/FAIL
from the reported error count, incomplete count, and incomplete-failure policy.
Extra fields such as CLI decisions are ignored by digest recomputation.

The `pea embedded-pack ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-firmware N] [--include-preview] [--no-check-native]
[--no-check-c-abi] [--no-check-rtos] [--no-check-static] [--no-check-bus]
[--no-check-safety] [--no-check-memory] [--no-check-signed]
[--fail-on-incomplete] [--current-version V]` command reports firmware evidence
without creating or modifying project files. `--check` requires a passing gate,
`--emit` writes the JSON report, and `--write-state` persists the digest state.
`pea embedded-pack --capabilities` prints the versioned capability set. The
`sector.embedded_pack` feature flag records availability.
