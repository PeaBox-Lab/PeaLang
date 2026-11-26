# Cloud Infrastructure / DevOps sector pack

Wave 4 completes with a deterministic sector-pack evidence gate for the Cloud
Infrastructure / DevOps row of the sector table. It is additive to the package
lifecycle CLI, `frameworks.py` k8s/cloudbuild/edge scaffolds,
`cloud_connectors.py`, `object_storage.py`, and `kafka_connector.py`, and it does
not change the frozen 3.0 language surface.

`cloud_pack_capabilities()` returns the versioned capability set with the default
profile, supported options, the `*.cloud.json` source filter, the sorted
deployment kinds, stable ordering, and a recomputed gate.
`CLOUD_PACK_VERSION` records the current release and `CLOUD_PACK_FORMAT`
identifies the sector-pack format.

`CloudProfileV2` is a frozen, validated profile with a positive
`max_deployments` limit, an `include_preview` switch, a `check_container` switch,
a `check_orchestration` switch, a `check_pipeline` switch, a
`check_observability` switch, a `check_iam` switch, a `check_source` switch, a
`check_lockfile` switch, a `check_signed` switch, a `check_drift` switch, a
`fail_on_incomplete` policy, and a `current_version` string. An empty
`current_version` resolves to `CLOUD_PACK_VERSION`. Invalid profiles raise
`CloudPackError` before any planning occurs. `DEFAULT_CLOUD_PROFILE` is stable and
serializable.

`plan_cloud_pack()` discovers deployment manifests under a root while skipping
build and cache directories. Preview, canary, and experimental directories are
skipped unless `include_preview` is enabled. Each manifest must declare a
lowercase `name`, a string `version`, a `kind` drawn from `CLOUD_KINDS`, a
non-empty sorted set of `evidence` artifacts, string lists for `requires`, and
string lists for `bindings`; invalid manifests produce an `E204` issue. Every
declared evidence path must resolve to a file under the root, or an `E205` issue
is produced. Each `CloudAppV2` carries a relative path, a manifest content digest,
the name, version, kind, sorted evidence paths, sorted platform bindings, sorted
required names, sorted resolved dependencies, a clean/stale state, and reasons. A
dependency is resolved through the provider set of a required name. Wall-clock
values and absolute host paths never enter the plan.

A required deployment with no provider produces an `E201` issue; a dependency
cycle produces an `E202` issue; and exceeding the deployment limit produces an
`E203` issue. When `check_container` is enabled, a `deployment-demo` with no
resolved `container-image` dependency produces an `E206` issue. When
`check_orchestration` is enabled, a `deployment-demo` with no resolved
`k8s-manifest` dependency produces an `E207` issue. When `check_pipeline` is
enabled, a `deployment-demo` with no resolved `ci-pipeline` dependency produces
an `E208` issue. When `check_observability` is enabled, a `deployment-demo` with
no resolved `observability` dependency produces an `E209` issue. When
`check_iam` is enabled, a `deployment-demo` with no resolved `iam-policy`
dependency produces an `E210` issue. When `check_source` is enabled, a
`deployment-demo` with no resolved `go-service`, `python-service`, `bash-script`,
`cdk-stack`, or `terraform-module` dependency produces an `E211` issue. When
`check_lockfile` is enabled, a `deployment-demo` without a `lockfile` binding
produces an `E212` issue. When `check_signed` is enabled, a `deployment-demo`
without a `signed-package` binding produces an `E213` issue. When `check_drift`
is enabled, a `deployment-demo` without a `drift-check` binding produces an
`E214` issue. All issues are sorted by code, path, and message. Incomplete state
starts from paths whose digest is new or changed relative to supplied state, with
`new` or `changed` reasons, and propagates a `dependency` reason to dependents
through a stable queue. Deployments are emitted in a deterministic topological
order.

`load_cloud_state_v2()` reads versioned digest state, returning empty state for
an absent file and rejecting invalid version, JSON, or shape.
`write_cloud_state_v2()` persists a deterministic digest map keyed by relative
path, with no absolute host paths.

`cloud_pack_report()` summarizes plan count, deployment and incomplete counts,
error count, per-plan evidence, and a recomputable digest. `cloud_pack_gate()`
verifies the version, format, gate shape, report and plan digests, deployment and
issue fingerprints, count consistency, and profile, then recomputes PASS/FAIL
from the reported error count, incomplete count, and incomplete-failure policy.
Extra fields such as CLI decisions are ignored by digest recomputation.

The `pea cloud-pack ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-deployments N] [--include-preview] [--no-check-container]
[--no-check-orchestration] [--no-check-pipeline] [--no-check-observability]
[--no-check-iam] [--no-check-source] [--no-check-lockfile] [--no-check-signed]
[--no-check-drift] [--fail-on-incomplete] [--current-version V]` command reports
deployment evidence without creating or modifying project files. `--check`
requires a passing gate, `--emit` writes the JSON report, and `--write-state`
persists the digest state. `pea cloud-pack --capabilities` prints the versioned
capability set. The `sector.cloud_pack` feature flag records availability.
