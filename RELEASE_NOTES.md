# PeaLang 0.18.0 Release Notes

PeaLang 0.18 begins the transition from a standalone automation language to an embeddable extension language.

## Added

- Public `PeaRuntime`, `PeaModule`, `RuntimeOptions`, and `ExecutionResult` APIs.
- Explicit module exports and exported-function invocation from Python.
- Safe conversion for primitive values, collections, dataclasses, and Pydantic v2 models.
- Capability-protected host functions and host modules.
- Execution time, instruction, and call-depth budgets.
- Process access disabled by default for embedded runtimes.
- Structured runtime, permission, and resource-limit errors.
- Python-host and FastAPI examples.
- Embedding, FastAPI, Java, React, security, and architecture documentation.

## Compatibility

Existing PeaLang scripts and CLI workflows remain compatible with the 0.15 baseline. The embedding API is introduced as preview and may receive additive refinements before 1.0.
