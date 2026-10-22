# PeaLang 0.35.0 Release Notes

0.35 stabilizes the standard-library architecture required by the foundational roadmap.

## Added
- Canonical `std` namespace and 14 named modules
- `StdModuleSpec`, `MODULES`, `stdlib_manifest()` and `pea stdlib`
- Permission gates for filesystem, HTTP, logging and concurrency modules
- Dedicated compatibility regression tests
- Standard-library docs/help

## Compatibility
Existing top-level `file`, `path`, `json`, `csv`, `datetime`, `regex`, `http`, and `task` aliases are retained during 0.x. New code should use `std.*`.
