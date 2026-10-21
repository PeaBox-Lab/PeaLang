# Packages and Dependency Integrity

PeaLang 0.12 keeps dependencies local and explicit. Add one with `pea add NAME PATH`, generate `pea.lock` with `pea lock`, and validate it with `pea verify`. The lockfile stores a SHA-256 digest of each dependency entry file. Commit both `pea.json` and `pea.lock`. Regenerate the lock only after reviewing intended dependency changes.
