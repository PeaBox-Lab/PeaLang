# PeaLang v0.76 Release Hardening

v0.76 introduces machine-checkable release gates before the final v1 stabilization line.

## Capabilities
- Adversarial agent-policy probe suite.
- Public API snapshot comparison with explicit approved-removal support.
- Minimum regression-test thresholds.
- Retention-gate integration.
- Unified pass/fail hardening report.
- SHA-256 manifest helper for release evidence.

A release is expected to fail closed when an unexpected public API removal or file-retention regression is detected.
