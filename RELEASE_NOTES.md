# PeaLang 0.12.0 Release Notes

0.12 introduces the first package-integrity layer. `pea lock` records deterministic SHA-256 hashes for local dependency entry files in `pea.lock`; `pea verify` compares installed dependencies against the lock and returns a failing exit code when integrity changes. Existing projects continue to run without a lockfile.
