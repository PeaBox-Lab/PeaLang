# PeaLang 0.34.0

PeaLang is an embeddable extension language. Version 0.34 begins the formal foundation-completion phase with an implementation-independent specification and compatibility contract.

## Specification
```bash
pea spec
pea features
```

The `spec/` directory now defines the language contract separately from the Python implementation. See `FOUNDATIONAL_ROADMAP.md` for the revised path to 1.0.

## Existing platform
PeaLang retains the PEAC compiler/VM, optional typing and semantic analysis, sync/async embedding, FastAPI, Java sidecar, TypeScript/React clients, DAP, package ecosystem, signed registry controls, profiling and observability.
