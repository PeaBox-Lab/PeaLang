
# PeaLang AI Development Handover 0.18

## Product direction

PeaLang is an embeddable extension language for rules, workflows, integrations, automation, and controlled application customization. It complements Python, FastAPI, Java, and React rather than replacing them.

## Implemented in 0.18

- `pealang.embedding.PeaRuntime`
- `PeaModule` exported-function API
- `RuntimeOptions` capability and resource configuration
- host function and host module registration
- dataclass and Pydantic conversion
- execution budgets and process-off default
- Python and FastAPI examples
- embedding and interoperability documentation

## Next build

Version 0.19 should add semantic types while preserving untyped compatibility. Implement type AST nodes, annotated declarations and parameters, record aliases, union and optional types, a semantic symbol table, import/export validation, diagnostics, `pea typecheck`, and at least 50 conformance tests.

## Non-negotiable release contents

Every release must include cumulative changelog, release notes, README, roadmap, version history, foundations, full user and embedding guides, help pages, tests, examples, security notes, architecture notes, and an updated AI handover.

