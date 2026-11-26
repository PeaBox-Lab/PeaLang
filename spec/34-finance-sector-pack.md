# Enterprise/Finance/Banking sector pack

Wave 4 opens with a deterministic sector-pack evidence gate for the enterprise,
finance, and banking row of the sector table. It is additive to `std.sql`, the
connector modules, capability controls, and the lock/audit/quality CLI, and it
does not change the frozen 3.0 language surface.

`finance_pack_capabilities()` returns the versioned capability set with the
default profile, supported options, the `*.finance.json` source filter, the
sorted artifact kinds, stable ordering, and a recomputed gate.
`FINANCE_PACK_VERSION` records the current release and `FINANCE_PACK_FORMAT`
identifies the sector-pack format.

`FinanceProfileV2` is a frozen, validated profile with a positive
`max_artifacts` limit, an `include_sandbox` switch, a `check_interop` switch, a
`check_audit` switch, a `fail_on_incomplete` policy, and a `current_version`
string. An empty `current_version` resolves to `FINANCE_PACK_VERSION`. Invalid
profiles raise `FinancePackError` before any planning occurs.
`DEFAULT_FINANCE_PROFILE` is stable and serializable.

`plan_finance_pack()` discovers sector artifacts under a root while skipping
build and cache directories. Sandbox, pilot, and experimental directories are
skipped unless `include_sandbox` is enabled. Each manifest must declare a
lowercase `name`, a string `version`, a `kind` drawn from `FINANCE_KINDS`, a
non-empty sorted set of `evidence` artifacts, and string lists for `requires`
and `contracts`; invalid manifests produce an `F204` issue. Every declared
evidence path must resolve to a file under the root, or an `F205` issue is
produced. Each `FinanceArtifactV2` carries a relative path, a manifest content
digest, the name, version, kind, sorted evidence paths, sorted required names,
sorted contracts, sorted resolved dependencies, a clean/stale state, and
reasons. A dependency is resolved through the provider set of a required tool
name. Wall-clock values and absolute host paths never enter the plan.

A required artifact with no provider produces an `F201` issue; a dependency
cycle produces an `F202` issue; and exceeding the artifact limit produces an
`F203` issue. When `check_interop` is enabled, an `interop-binding` artifact
with no contracts produces an `F206` issue. When `check_audit` is enabled, a
`reference-app` artifact with no resolved `audit-rule` dependency produces an
`F207` issue. All issues are sorted by code, path, and message. Incomplete state
starts from paths whose digest is new or changed relative to supplied state,
with `new` or `changed` reasons, and propagates a `dependency` reason to
dependents through a stable queue. Artifacts are emitted in a deterministic
topological order.

`load_finance_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_finance_state_v2()` persists a deterministic digest map keyed by relative
path, with no absolute host paths.

`finance_pack_report()` summarizes plan count, artifact and incomplete counts,
error count, per-plan evidence, and a recomputable digest. `finance_pack_gate()`
verifies the version, format, gate shape, report and plan digests, artifact and
issue fingerprints, count consistency, and profile, then recomputes PASS/FAIL
from the reported error count, incomplete count, and incomplete-failure policy.
Extra fields such as CLI decisions are ignored by digest recomputation.

The `pea finance-pack ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-artifacts N] [--include-sandbox] [--no-check-interop]
[--no-check-audit] [--fail-on-incomplete] [--current-version V]` command reports
sector-pack evidence without creating or modifying project files. `--check`
requires a passing gate, `--emit` writes the JSON report, and `--write-state`
persists the digest state. `pea finance-pack --capabilities` prints the versioned
capability set. The `sector.finance_pack` feature flag records availability.
