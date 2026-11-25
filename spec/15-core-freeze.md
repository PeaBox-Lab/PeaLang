# Frozen 3.0 core

The frozen 3.0 core is the stable language surface delivered by Wave 1
(phases 61-70). Freezing is additive-only: new APIs may be introduced, but an
unapproved removal from the public API snapshot fails the gate.

The canonical manifest is `CORE_SURFACES`. It names the frozen surface, its
category, and the release line that introduced it. `CoreFreezeManifest` provides
a stable digest and a structural diff so releases can prove that no frozen
surface was renamed, removed, or downgraded.

`verify_core_freeze()` combines five checks:

- `public_api` — the current public API has no unexpected removals,
- `conformance` — the v2 curated suite passes,
- `specification` — all normative spec sections exist and report the release,
- `surfaces` — the complete canonical surface manifest is still frozen, and
- `version` — package version and freeze release agree.

`core_freeze_gate()` reduces any supplied inputs to a deterministic PASS/FAIL
report, while `core_freeze_report()` adds the manifest for CLI output.
`pea freeze` prints that report as JSON and exits zero only on `PASS`.
