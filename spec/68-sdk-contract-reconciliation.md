# SDK contract and documentation reconciliation

Phase 125 at version 5.25.0 is a Wave 10 maintenance release.
It repairs evidence retention, SDK contracts, and verification metadata without
changing the frozen 3.0 language surface, the public API snapshot, or the
stable feature registry.

Phase 125 reconciles SDK contracts with shipped surfaces. Generated
Java clients use the `io.pealang.client` package, the current release version,
and JSON arrays for invocation arguments. React and browser documentation
describes the exports actually shipped by `@pealang/react` and
`@pealang/browser`. No new public API, command, or flag is introduced.

The release keeps `SECTIONS` at 13, preserves every pinned component version,
and leaves the core freeze digest unchanged.
