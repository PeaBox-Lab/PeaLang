# Mobile (iOS) sector pack

Wave 4 continues with a deterministic sector-pack evidence gate for the iOS row
of the sector table. It is additive to `host_bindings.py`, `vm_embedding.py`,
and the Java client sidecar, and it does not change the frozen 3.0 language
surface.

`ios_pack_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.ios.json` source filter, the sorted app
kinds, stable ordering, and a recomputed gate. `IOS_PACK_VERSION` records the
current release and `IOS_PACK_FORMAT` identifies the sector-pack format.

`IOSProfileV2` is a frozen, validated profile with a positive `max_apps` limit,
an `include_preview` switch, a `check_swift` switch, a `check_objc` switch, a
`check_xcframework` switch, a `check_templates` switch, a `fail_on_incomplete`
policy, and a `current_version` string. An empty `current_version` resolves to
`IOS_PACK_VERSION`. Invalid profiles raise `IOSPackError` before any planning
occurs. `DEFAULT_IOS_PROFILE` is stable and serializable.

`plan_ios_pack()` discovers apps under a root while skipping build and cache
directories. Preview, canary, and experimental directories are skipped unless
`include_preview` is enabled. Each manifest must declare a lowercase `name`, a
string `version`, a `kind` drawn from `IOS_KINDS`, a non-empty sorted set of
`evidence` artifacts, string lists for `requires`, and string lists for
`bindings`; invalid manifests produce an `I204` issue. Every declared evidence
path must resolve to a file under the root, or an `I205` issue is produced. Each
`IOSAppV2` carries a relative path, a manifest content digest, the name,
version, kind, sorted evidence paths, sorted platform bindings, sorted required
names, sorted resolved dependencies, a clean/stale state, and reasons. A
dependency is resolved through the provider set of a required app name.
Wall-clock values and absolute host paths never enter the plan.

A required app with no provider produces an `I201` issue; a dependency cycle
produces an `I202` issue; and exceeding the app limit produces an `I203` issue.
When `check_swift` is enabled, a `sample-app` with no resolved `swift-bridge`
dependency produces an `I206` issue. When `check_objc` is enabled, a
`sample-app` with no resolved `objc-compat` dependency produces an `I207`
issue. When `check_xcframework` is enabled, a `sample-app` with no resolved
`xcframework` dependency produces an `I208` issue. When `check_templates` is
enabled, a `sample-app` with no resolved `xcode-template` dependency produces
an `I209` issue. All issues are sorted by code, path, and message. Incomplete
state starts from paths whose digest is new or changed relative to supplied
state, with `new` or `changed` reasons, and propagates a `dependency` reason to
dependents through a stable queue. Apps are emitted in a deterministic
topological order.

`load_ios_state_v2()` reads versioned digest state, returning empty state for an
absent file and rejecting invalid version, JSON, or shape.
`write_ios_state_v2()` persists a deterministic digest map keyed by relative
path, with no absolute host paths.

`ios_pack_report()` summarizes plan count, app and incomplete counts, error
count, per-plan evidence, and a recomputable digest. `ios_pack_gate()` verifies
the version, format, gate shape, report and plan digests, app and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, incomplete count, and incomplete-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea ios-pack ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-apps N] [--include-preview] [--no-check-swift]
[--no-check-objc] [--no-check-xcframework] [--no-check-templates]
[--fail-on-incomplete] [--current-version V]` command reports app evidence
without creating or modifying project files. `--check` requires a passing gate,
`--emit` writes the JSON report, and `--write-state` persists the digest state.
`pea ios-pack --capabilities` prints the versioned capability set. The
`sector.ios_pack` feature flag records availability.
