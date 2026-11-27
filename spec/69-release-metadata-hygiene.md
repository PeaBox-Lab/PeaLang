# Verification stability and release metadata hygiene

Phase 126 at version 5.26.0 is a Wave 10 maintenance release.
It repairs evidence retention, SDK contracts, and verification metadata without
changing the frozen 3.0 language surface, the public API snapshot, or the
stable feature registry.

Phase 126 closes verification and metadata drift. `pea info` reports
the complete dispatch command inventory. A behavioral deadline test uses a
never-completing operation instead of textual assertions. Current release
metadata, user-guide version text, and tracked package metadata are refreshed
while the fixed release metrics and frozen 3.0 core remain unchanged.

The release keeps `SECTIONS` at 13, preserves every pinned component version,
and leaves the core freeze digest unchanged.
