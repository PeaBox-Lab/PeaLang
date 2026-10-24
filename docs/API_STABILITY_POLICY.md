
# PeaLang Public API Stability Policy

Starting with 0.63 RC1, public APIs are snapshotted and compatibility checked. During 0.x, incompatible changes require explicit migration notes. For 1.x, public APIs follow semantic versioning: removals and incompatible changes are reserved for major releases. Deprecations must identify a replacement, introduction version and earliest removal version, with at least one minor-release transition where practical. Internal names beginning with `_` are excluded.
