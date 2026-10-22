# PeaLang Package Ecosystem

PeaLang 0.27 introduces `pea.toml`, deterministic `pea.lock`, semantic-version constraints, local/Git/registry source metadata, SHA-256 integrity checks, permission manifests, `.peapkg` archives, installation, auditing, and reproducible package builds.

## Create

```bash
pea pkg-init my-extension
```

## Manifest

```toml
[project]
name = "bonus-rules"
version = "1.0.0"
entry = "src/main.pea"
pealang = ">=0.30.0"

[dependencies]
validation = { path = "../validation", version = "^1.2.0" }
remote-rules = { git = "https://example.com/rules.git", version = "1.0.0", rev = "abc123" }

[permissions]
allow = ["employee.read"]
```

## Workflow

```bash
pea lock
pea install
pea audit
pea build
```

`pea.lock` stores resolved versions, source identity, dependency permission requests, and SHA-256 checksums for local manifests. `.peapkg` builds normalize timestamps and ownership metadata for reproducibility.

Git and registry entries are represented in the lock model in 0.27. Network fetching and cryptographic signature verification are deliberately deferred until authenticated transport and trust-store policy are implemented.
