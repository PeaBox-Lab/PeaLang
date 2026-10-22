# PeaLang 0.27.0 Release Notes

PeaLang 0.27 establishes the package ecosystem foundation.

## Added

- `pea.toml` project/package manifest.
- Deterministic JSON `pea.lock` format version 1.
- Semantic version parsing and `^`, `~`, comparison, exact, and wildcard constraints.
- Local path dependency resolution and installation into `.pea_modules`.
- Git and registry dependency metadata in lock files.
- Dependency permission declarations and auditing.
- SHA-256 local-manifest integrity checks.
- Reproducible `.peapkg` tar.gz archives with normalized metadata.
- `pea pkg-init`, `pea lock`, `pea install`, `pea audit`, and `pea build` commands.
- Package-manager API and regression tests.

## Security scope

0.27 records Git and registry sources but does not download them. This avoids introducing unauthenticated network installation before package signatures, registry trust roots, transport verification, and policy controls are complete.
