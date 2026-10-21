# Feature Guide v0.3.0
## Language
Variables/constants, values, operators, conditions, loops, functions/closures/recursion, collections, property/index access and mutation, interpolation, local imports, CLI and REPL.
## Automation
UTF-8 files, paths, JSON, CSV, environment variables, ISO date/time, regular expressions, HTTP and opt-in process execution.
## Experimental boundaries
Import semantics, host-backed standard-library behavior and unsandboxed I/O.
## Not implemented
Exceptions, namespace imports, package manager, static types, concurrency, formatter, checker, LSP, database modules or AI provider APIs.

## v0.5 workflow and testing
Native assertions, expected-output PeaLang tests, structured workflow helpers, task helpers and bounded parallel expressions are implemented. Durable orchestration, cancellation and distributed execution are not.

## v0.6 AI workflow identity
Provider-neutral AI calls, deterministic mock testing, OpenAI-compatible endpoints, external credential lookup, structured output validation/extraction and portable prompt skills are implemented. Streaming, embeddings, multimodal input and agent tool calling are not.

## v0.7 projects
Project manifests, entry points, local modules, local path dependencies and project CLI commands are implemented. Registry packages, lockfiles and import namespaces are not.

## v0.8 agents/tools
Explicit tool registration, tool metadata, per-agent name allowlists, one-shot AI-backed agents and explicit tool calls are implemented. Autonomous loops, memory, automatic function calling and sandboxing are not.

## v0.9 language maturity
Language-level try/catch/finally, throw and trailing default function arguments are implemented. PeaLang remains interpreter-first.

## v0.10 modules/namespaces
Aliased namespace imports and explicit exports are implemented while legacy imports remain compatible.
