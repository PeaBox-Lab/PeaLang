


# PeaLang AI Development Handover 0.27

## Delivered

- pea.toml manifest
- deterministic pea.lock
- semantic versions and constraints
- local package dependency resolver
- .pea_modules installation
- Git and registry source metadata model
- permission manifests and audit
- SHA-256 integrity checks
- reproducible .peapkg archives
- package CLI commands

## Security decision

0.27 intentionally does not perform remote downloads. Git and registry sources can be locked, but authenticated transport, signature verification, registry trust configuration, and safe extraction must be built before remote installation is enabled.

## Next release

0.28 should focus on Java interoperability: an HTTP/gRPC-style runtime sidecar contract, Java SDK models, Spring Boot integration example/starter scaffolding, typed portable values, timeout/cancellation propagation, capability declarations, script compilation cache, and health/readiness endpoints.

## Release requirement

Continue cumulative version history, changelog, README, release notes, roadmap, foundations, user/embedding/help docs, architecture/security notes, tests, examples, and updated AI handover.



