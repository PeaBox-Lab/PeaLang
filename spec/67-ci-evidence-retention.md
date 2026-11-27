# CI evidence retention and performance gate repair

Phase 124 at version 5.24.0 is a Wave 10 maintenance release.
It repairs evidence retention, SDK contracts, and verification metadata without
changing the frozen 3.0 language surface, the public API snapshot, or the
stable feature registry.

Phase 124 repairs CI evidence retention without creating evidence.
The performance workflow invokes the real `pea benchmark` CLI path, saves a
baseline, writes the `perf_report.json` it uploads, and applies the existing
regression threshold. Python, Java, and Node matrices retain their reports;
security workflows retain Bandit, pip-audit, Semgrep, Trivy, and secret-scan
reports. The GA handoff remains NO-GO until genuine evidence is populated.

The release keeps `SECTIONS` at 13, preserves every pinned component version,
and leaves the core freeze digest unchanged.
