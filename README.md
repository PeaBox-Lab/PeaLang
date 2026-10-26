# PeaLang

**A modern, embeddable programming language and runtime for application scripting, data engineering, orchestration, streaming, machine learning, and distributed workloads.**

> Current release: **v0.99.5**  
> Status: **Pre-1.0 / Release Candidate Stabilization**

PeaLang is a general-purpose programming language and runtime designed to work both as a standalone language and as an embeddable extension layer for existing applications.

The project has evolved from a lightweight interpreter into a broader language platform with compilation, bytecode execution, type checking, debugging, packaging, data processing, connectors, orchestration, streaming, machine learning, distributed execution, security, and release-integrity tooling.

PeaLang is currently in the final stabilization and certification phase leading to **v1.0.0**.

---

## Highlights

PeaLang includes:

- Interpreter and parser
- Compiler and bytecode VM
- Static and runtime type-system capabilities
- Modules and package management
- Standard library
- Async and structured concurrency
- Debug Adapter Protocol support
- Application embedding
- Python integration
- FastAPI integration
- Java SDK
- TypeScript SDK
- React SDK
- Browser/WASM integration
- SQL and database connectivity
- DataFrame processing
- Cloud and object-storage connectors
- Analytics and time-series processing
- Forecasting
- Machine-learning foundations
- MLOps and model serving
- Distributed execution
- Streaming processing
- Kafka integration
- RabbitMQ and WebSocket messaging
- DAG orchestration
- Agent and tool-governance capabilities
- Observability and profiling
- Package signing and verification
- SBOM and provenance tooling
- Release-integrity and compatibility gates

---

# Why PeaLang?

PeaLang is designed around a simple idea:

> **Extend existing systems instead of replacing them.**

It can be used as an application scripting and orchestration layer while existing services continue to use technologies such as Python, Java, FastAPI, JavaScript, TypeScript, React, SQL, Kafka, and other established platforms.

Typical use cases include:

### Embedded application logic

Use PeaLang as an extension or scripting language inside another application.

### Automation and orchestration

Define workflows, tasks, pipelines, DAGs, and distributed operations.

### Data engineering

Work with structured data, databases, DataFrames, connectors, streams, and analytical workloads.

### Streaming

Build event-processing workflows with streaming, windowing, Kafka, messaging systems, and WebSockets.

### Machine learning

Develop data-processing, forecasting, ML, MLOps, serving, and production inference workflows.

### Enterprise integration

Connect PeaLang workloads to existing applications and infrastructure instead of requiring complete rewrites.

---

# Quick Start

## Requirements

PeaLang's current pre-1.0 compatibility work targets modern Python environments.

For development, create an isolated environment.

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Upgrade the packaging tools:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Install PeaLang from the project directory:

```bash
pip install -e .
```

---

# Your First PeaLang Program

Create:

```text
hello.pea
```

Example:

```pea
let name = "PeaLang"
print("Hello from " + name)
```

Run it using the PeaLang CLI:

```bash
pea run hello.pea
```

Use the CLI help for the commands supported by your installed version:

```bash
pea --help
```

---

# PeaLang Architecture

PeaLang has evolved into a layered runtime:

```text
                    PeaLang Application
                           |
              +------------+------------+
              |                         |
          Interpreter               Compiler
              |                         |
              |                      Bytecode
              |                         |
              +------------+------------+
                           |
                           VM
                           |
             +-------------+-------------+
             |             |             |
        Standard       Connectors     Tooling
        Library
             |             |             |
       +-----+-----+       |       +-----+-----+
       |           |       |       |           |
      Data       ML/AI   Cloud    Debugging   Profiling
       |           |       |
       |        Serving  Messaging
       |           |       |
       +-----------+-------+
                   |
            Orchestration
                   |
        Distributed Execution
```

---

# Language and Runtime

The PeaLang runtime contains implementations for core language processing and execution, including:

```text
Parser
Interpreter
Compiler
Bytecode
Virtual Machine
Type System
Module System
Package System
Standard Library
Async Runtime
Structured Concurrency
```

The project also maintains compatibility and public-API snapshots as part of the stabilization process.

---

# Data Engineering

PeaLang includes functionality targeting data-oriented workloads.

Areas include:

```text
DataFrames
SQL
Database connectivity
Object storage
Cloud connectors
Analytics
Time series
Forecasting
Streaming
Windowing
```

This allows PeaLang programs to move beyond simple scripting and participate in larger data pipelines.

---

# Streaming and Messaging

PeaLang includes capabilities for event-driven and streaming applications.

These include:

- Streaming execution
- Windowing
- Kafka
- RabbitMQ
- WebSockets
- Messaging connectors
- Stateful processing
- DAG orchestration

These capabilities are intended to allow PeaLang programs to coordinate batch, event-driven, and streaming workflows.

---

# Machine Learning and MLOps

PeaLang's ML-oriented capabilities include areas such as:

```text
ML foundations
Forecasting
Production ML
Secure MLOps
Model serving
Resilient serving
Distributed serving
```

The goal is not to replace established ML ecosystems, but to provide a language and orchestration layer capable of integrating them into PeaLang workflows.

---

# Distributed Execution

PeaLang includes infrastructure for scalable workloads, including:

- DAG orchestration
- Distributed compute
- Scalable execution
- Streaming
- Distributed serving
- State management
- Recovery and resilience mechanisms

---

# SDKs and Integration

## Python

PeaLang's primary runtime integrates closely with Python and can be embedded into Python-based systems.

## FastAPI

PeaLang contains FastAPI integration for applications that want PeaLang execution behind HTTP APIs and services.

## Java

A Java SDK is provided under:

```text
java-sdk/
```

The pre-1.0 compatibility program includes validation against modern Java environments.

## TypeScript

The TypeScript SDK is located under:

```text
typescript-sdk/
```

It supports modern TypeScript compilation and Node module resolution.

## React

A React integration is available under:

```text
react-sdk/
```

It provides the foundation for integrating PeaLang-backed functionality into React applications.

## Browser / WASM

Browser integration is available under:

```text
browser-sdk/
```

PeaLang also contains WebAssembly-related runtime functionality for browser-oriented use cases.

---

# Developer Tooling

PeaLang provides tooling for language development and application debugging.

This includes:

- Debug Adapter Protocol support
- VM debugging
- Profiling
- Coverage support
- Semantic analysis
- Runtime diagnostics
- Conformance testing
- Performance regression infrastructure

---

# Testing

Run the Python test suite with:

```bash
pytest
```

Specific tests can be executed with:

```bash
pytest tests/
```

PeaLang maintains regression tests across multiple generations of the language to reduce the risk of accidentally removing historical capabilities.

The project also contains dedicated compatibility, conformance, retention, security, packaging, and release-integrity tests.

---

# Historical Retention

Backward capability retention is an explicit PeaLang development principle.

The repository maintains historical information including:

```text
Historical capability ledger
Historical release index
Retention reports
Public API snapshots
Version history
Compatibility reports
Approved-removal records
```

A capability should not disappear silently during development.

Intentional removals should be explicitly documented and approved.

---

# Security

PeaLang contains security functionality covering areas such as:

- Package verification
- Signed packages
- Ed25519 signatures
- Registry integrity
- Security boundaries
- Supply-chain validation
- Dependency auditing
- Security regression testing
- Provenance
- SBOM generation

Security validation remains part of the final v1.0 release process.

---

# Supply-Chain Integrity

PeaLang's release architecture includes support for:

```text
SHA-256 artifact verification
SBOM generation
Provenance
 package signatures
Release manifests
Public API snapshots
Compatibility evidence
Retention evidence
```

For v1.0, these mechanisms are intended to be applied to the exact final release artifacts.

---

# Repository Structure

A simplified project layout:

```text
PeaLang/
|
+-- pealang/                    # Main language/runtime
+-- tests/                      # Regression and validation tests
+-- docs/                       # Documentation
+-- examples/                   # PeaLang examples
|
+-- java-sdk/                   # Java integration
+-- typescript-sdk/             # TypeScript SDK
+-- react-sdk/                  # React integration
+-- browser-sdk/                # Browser integration
|
+-- release/                    # Release policy/configuration
+-- release-evidence/           # Release certification evidence
+-- tools/                      # Development/release tooling
|
+-- .github/
|   +-- workflows/              # CI and validation
|
+-- pyproject.toml
+-- README.md
+-- CHANGELOG.md
+-- ROADMAP.md
```

---

# Documentation

Project documentation is maintained under:

```text
docs/
```

Key starting points include:

```text
docs/BASICS.md
docs/STANDARD_LIBRARY.md
docs/PACKAGES.md
docs/BYTECODE_AND_VM.md
docs/ASYNC_VM.md
docs/EMBEDDING.md
docs/FASTAPI_INTEGRATION.md
docs/JAVA_REACT_INTEROP.md
docs/DEBUG_ADAPTER.md
docs/RELEASE_INTEGRITY.md
```

Additional documentation covers data engineering, connectors, streaming, machine learning, orchestration, distributed execution, security, migration, compatibility, and release engineering.

---

# Versioning

PeaLang follows incremental development with compatibility and retention checks between releases.

The project is currently in the:

```text
0.99.x -> 1.0.0
```

stabilization phase.

Feature development is effectively frozen while remaining release-certification work is completed.

See:

```text
CHANGELOG.md
ROADMAP.md
docs/project/VERSION_HISTORY.md
docs/releases/
```

for detailed release history.

---

# Current 1.0 Status

PeaLang v0.99.5 is a **pre-1.0 stabilization release**.

Core implementation is substantially complete, while final release certification remains in progress.

Current areas of final validation include:

- Full regression validation
- Windows/Linux/macOS compatibility
- Python version compatibility
- Java 17/21 SDK validation
- Node 20/22/24 SDK validation
- Security scanning
- Clean installation
- Offline installation
- Wheel validation
- Source distribution validation
- Container validation
- Reproducibility
- SBOM generation
- Provenance
- Artifact signing
- Final release approvals

A workflow or validation framework being present does **not** automatically mean that the corresponding v1.0 certification has passed.

Final v1.0 readiness requires retained evidence produced against the final release candidate.

---

# 1.0 Release Philosophy

PeaLang follows a fail-closed release policy.

A release should not be declared ready merely because the implementation builds successfully.

The final release gate considers:

```text
Regression
Historical retention
API stability
Compatibility
Security
Packaging
Installation
Supply-chain integrity
Documentation
Release evidence
Approvals
```

Missing required release evidence results in a **NO-GO** rather than an assumed PASS.

---

# Roadmap

The immediate objective is:

## PeaLang 1.0

The remaining work focuses on stabilization and release certification rather than adding major new feature families.

The intended sequence is:

```text
Pre-1.0 stabilization
        |
Regression certification
        |
Compatibility certification
        |
Security certification
        |
Packaging certification
        |
Supply-chain evidence
        |
Release approvals
        |
PeaLang 1.0.0
```

See `ROADMAP.md` for the detailed project roadmap.

---

# Contributing

Contributions should preserve PeaLang's historical compatibility and release-integrity principles.

Before submitting a change:

```bash
pytest
```

For changes affecting public APIs, packaging, SDKs, security, compatibility, or release behavior, also run the relevant specialized validation suites.

Changes should:

1. Preserve existing functionality unless removal is intentional.
2. Include regression tests for new behavior.
3. Document public-facing changes.
4. Update the changelog where appropriate.
5. Avoid committing generated build artifacts.
6. Avoid undocumented breaking changes.

---

# Generated Files

Generated build output should not be treated as canonical PeaLang source.

Examples include:

```text
build/
dist/
target/
*.egg-info/
__pycache__/
.pytest_cache/
node_modules/
coverage/
```

These artifacts should normally be generated during build, test, packaging, or release processes rather than maintained as source.

---

# Release Documentation

Each PeaLang release should maintain:

- Cumulative `CHANGELOG.md`
- Version-specific release notes
- Updated README
- Version history
- User documentation
- Basics/foundation documentation
- Upgrade and migration guidance
- Retention evidence
- Compatibility evidence
- Release-integrity evidence

This keeps both historical evolution and current usage discoverable.

---

# Stability Notice

PeaLang is currently a **pre-1.0 project**.

The project has entered API and feature stabilization, but users should still expect final packaging, compatibility, and release-certification changes before v1.0.0.

Production adoption should therefore evaluate the specific PeaLang release and its accompanying compatibility and release evidence.

---

# License

See the repository's `LICENSE` file for licensing terms.

---

# Project Status

```text
Current version       : 0.99.5
Development phase     : Pre-1.0 stabilization
Feature development   : Frozen for 1.0
Historical retention  : Enabled
Compatibility gates   : Enabled
Security gates        : Enabled
Release certification : In progress
Target milestone      : PeaLang 1.0.0
```

---

## PeaLang

**Build small scripts. Embed them anywhere. Scale them into real systems.**
