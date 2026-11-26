# Repository and metadata integrity

Phase 121 at version 5.21.0 is a Wave 9 maintenance release.
It is additive in metadata and documentation only, and it does not change the
frozen 3.0 language surface, the public API snapshot, or the stable feature
registry.

Phase 121 repairs repository metadata without changing the language
surface. The `PUBLIC_API_SNAPSHOT.sha256` sidecar must match the SHA-256 digest
of `PUBLIC_API_SNAPSHOT.json`. `RELEASE_MANIFEST.json` keeps its fixed metric
contract while its note describes the current maintenance release. Java and
browser SDK metadata must agree with the active PeaLang version. The dangling
Phase 34 heading is removed from `ROADMAP.md`, and the tracked `pytest_output.txt`
is refreshed so it no longer advertises an obsolete test count.

The release keeps `SECTIONS` at 13, preserves every pinned component version,
and leaves the core freeze digest unchanged.
