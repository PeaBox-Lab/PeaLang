# Versioned docs

Wave 3 continues with an additive versioned documentation layer. It does not
change the frozen 3.0 language surface, and it does not replace the existing
`pea docs` command; that command remains available.

`versioned_docs_capabilities()` returns the versioned capability set with the
default profile, supported options, the `*.md` source filter, the version
pattern, stable ordering, and a recomputed gate. `VERSIONED_DOCS_VERSION`
records the current release and `VERSIONED_DOCS_FORMAT` identifies the evidence
format.

`DocsProfileV2` is a frozen, validated profile with a positive `max_files`
limit, an `include_release_notes` switch, a `check_links` switch, a
`fail_on_drift` policy, and a `current_version` string. An empty
`current_version` resolves to `VERSIONED_DOCS_VERSION`. Invalid profiles raise
`VersionedDocsError` before any inventory occurs. `DEFAULT_DOCS_PROFILE` is
stable and serializable.

`plan_docs_v2()` discovers Markdown sources under a root while skipping build
and cache directories. Release-note, history, archive, and retention
directories are skipped unless `include_release_notes` is enabled. Each
`DocEntryV2` carries a relative path, a content digest, sorted version
references matched by `v?MAJOR.MINOR.PATCH`, sorted internal link targets, a
clean/stale state, and reasons. External links, bare anchors, and data URLs are
ignored. Wall-clock values and absolute host paths never enter the plan.

A doc that references versions but not the current version produces a `D201`
issue; a broken internal link produces a `D202` issue; and exceeding the file
limit produces a `D203` issue. All issues are sorted by code, path, and message.
Drift starts from paths whose digest is new or changed relative to supplied
state.

`load_docs_state_v2()` reads versioned digest state, returning empty state for an
absent file and rejecting invalid version, JSON, or shape.
`write_docs_state_v2()` persists a deterministic digest map keyed by relative
path, with no absolute host paths.

`docs_v2_report()` summarizes plan count, doc and drift counts, error count,
per-plan evidence, and a recomputable digest. `docs_v2_gate()` verifies the
version, format, gate shape, report and plan digests, entry and issue
fingerprints, count consistency, and profile, then recomputes PASS/FAIL from the
reported error count, drift count, and drift-failure policy. Extra fields such
as CLI decisions are ignored by digest recomputation.

The `pea docs-v2 ROOT [--check] [--emit FILE.json] [--state FILE]
[--write-state] [--max-files N] [--include-release-notes] [--no-links]
[--fail-on-drift] [--current-version V]` command reports a documentation
inventory without changing source. `--check` requires a passing gate, `--emit`
writes the JSON report, and `--write-state` persists the digest state.
`pea docs-v2 --capabilities` prints the versioned capability set. The
`devx.versioned_docs` feature flag records availability.
