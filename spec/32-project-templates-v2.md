# Project templates v2

Wave 3 concludes with an additive project template catalog layer. It does not
change the frozen 3.0 language surface, and it does not replace the existing
`pea scaffold` or `pea templates` commands; those commands remain available.

`project_templates_v2_capabilities()` returns the versioned capability set with
the default profile, supported options, the `*.template.json` source filter,
stable ordering, and a recomputed gate. `PROJECT_TEMPLATES_V2_VERSION` records
the current release and `PROJECT_TEMPLATES_V2_FORMAT` identifies the evidence
format.

`TemplateProfileV2` is a frozen, validated profile with a positive
`max_templates` limit, an `include_community` switch, a `check_dependencies`
switch, a `fail_on_drift` policy, and a `current_version` string. An empty
`current_version` resolves to `PROJECT_TEMPLATES_V2_VERSION`. Invalid profiles
raise `ProjectTemplatesV2Error` before any planning occurs.
`DEFAULT_TEMPLATE_PROFILE` is stable and serializable.

`plan_project_templates_v2()` discovers template manifests under a root while
skipping build and cache directories. Community, contrib, and third-party
directories are skipped unless `include_community` is enabled. Each manifest
must declare a lowercase `name`, a string `version`, a non-empty sorted set of
`files`, and string lists for `requires` and `entrypoints`; invalid manifests
produce a `T204` issue. An entrypoint that is not declared in `files` produces a
`T205` issue. Each `TemplateNodeV2` carries a relative path, a manifest content
digest, the name, version, sorted file set, sorted required names, sorted
entrypoints, sorted resolved dependencies, a clean/stale state, and reasons. A
dependency is resolved through the provider set of a required template name.
Wall-clock values and absolute host paths never enter the plan.

A required template with no provider produces a `T201` issue when
`check_dependencies` is enabled; a dependency cycle produces a `T202` issue;
and exceeding the template limit produces a `T203` issue. All issues are sorted
by code, path, and message. Drift state starts from paths whose digest is new or
changed relative to supplied state, with `new` or `changed` reasons, and
propagates a `dependency` reason to dependents through a stable queue. Nodes are
emitted in a deterministic topological order.

`load_template_state_v2()` reads versioned digest state, returning empty state
for an absent file and rejecting invalid version, JSON, or shape.
`write_template_state_v2()` persists a deterministic digest map keyed by
relative path, with no absolute host paths.

`templates_v2_report()` summarizes plan count, template and drift counts, error
count, per-plan evidence, and a recomputable digest. `templates_v2_gate()`
verifies the version, format, gate shape, report and plan digests, node and
issue fingerprints, count consistency, and profile, then recomputes PASS/FAIL
from the reported error count, drift count, and drift-failure policy. Extra
fields such as CLI decisions are ignored by digest recomputation.

The `pea templates-v2 ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-templates N] [--include-community]
[--no-check-dependencies] [--fail-on-drift] [--current-version V]` command
reports a template inventory without creating or modifying project files.
`--check` requires a passing gate, `--emit` writes the JSON report, and
`--write-state` persists the digest state. `pea templates-v2 --capabilities`
prints the versioned capability set. The `devx.project_templates_v2` feature
flag records availability.
