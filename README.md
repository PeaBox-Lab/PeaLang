# PeaLang v0.99.6

Readable automation, data, integration, orchestration, and AI workflow language.

PeaLang is an embeddable extension language designed for rules, workflows, integrations, data processing, automation, and controlled application customization.

PeaLang is designed to complement existing ecosystems such as Python, FastAPI, Java, TypeScript, React, databases, messaging systems, and enterprise applications rather than replace them.

## Release Status

Current version: **0.99.6**

Release type: **Security Hardening / Pre-1.0**

PeaLang v0.99.6 is a security-focused release following the v0.99.5 compatibility and release-readiness work.

The release addresses security findings identified after enabling GitHub CodeQL analysis against the reconstructed PeaLang repository history.

No new major feature family is introduced in v0.99.6.

The objective is to improve security while preserving the existing PeaLang language, runtime, SDK, data, integration, orchestration, ML, tooling, and enterprise capabilities.

## What's New in v0.99.6

### SSH / SFTP Security Hardening

PeaLang SFTP connections now fail closed for unknown SSH host keys.

The previous option that could automatically trust an unknown SSH host has been removed.

SFTP now requires trusted host-key information through configured or system known-hosts data.

This reduces exposure to SSH machine-in-the-middle attacks.

### Package Signing Hardening

The legacy HMAC package-signing subsystem remains available for backwards-compatible controlled/internal workflows.

However, legacy trust-store metadata no longer copies the HMAC shared secret into the trust-store JSON.

For public package authenticity, PeaLang's existing Ed25519 signing infrastructure remains the recommended mechanism.

### Type-System ReDoS Hardening

The type-system source analyzer has been hardened against pathological source input and expensive regular-expression behavior.

v0.99.6 introduces:

- bounded type-expression input
- bounded type-check source input
- safer structural matching
- reduced use of ambiguous arbitrary-text regular expressions
- adversarial regression tests

Current safety limits:

- Maximum individual type expression: **65,536 characters**
- Maximum type-check source input: **2,000,000 characters**

These limits protect static analysis from unreasonable or deliberately pathological input.

### Security Regression Coverage

v0.99.6 adds dedicated regression coverage for:

- unknown SSH host-key handling
- signing trust-store secret exposure
- oversized type expressions
- oversized type-check source
- pathological type-system input

## Validation

The v0.99.6 local regression suite completed successfully:

    612 passed
    0 failed

Python package generation also completed successfully for:

    pealang-0.99.6-py3-none-any.whl
    pealang-0.99.6.tar.gz

GitHub CodeQL should be rerun against the v0.99.6 commit before the release is considered fully security-closed.

The target is:

    CodeQL High alerts: 0

## Installation

PeaLang requires Python 3.10 or newer.

### Install from source

Clone the repository:

    git clone https://github.com/PeaBox-Lab/PeaLang.git
    cd PeaLang

Create a virtual environment:

Windows:

    py -m venv .venv
    .venv\Scripts\activate

Linux/macOS:

    python3 -m venv .venv
    source .venv/bin/activate

Install PeaLang:

    python -m pip install --upgrade pip
    pip install -e .

Verify installation:

    pea --help

or:

    pealang --help

### Install the wheel

If you have the v0.99.6 wheel:

    pip install pealang-0.99.6-py3-none-any.whl

## Your First PeaLang Program

Create:

    hello.pea

Add:

    let name = "PeaLang"
    print "Hello " + name

Run:

    pea run hello.pea

## Basic Language Example

    let total = 0

    for x in [1, 2, 3, 4, 5] {
        total += x
    }

    print total

PeaLang supports core language constructs including:

- variables and constants
- functions
- control flow
- loops
- collections
- modules
- imports
- exceptions
- optional static typing
- asynchronous execution
- compiler and bytecode VM
- standard library
- embedding APIs

## Optional Static Typing

PeaLang supports optional type contracts while retaining compatibility with untyped programs.

Example:

    function add(a: Int, b: Int) -> Int {
        return a + b
    }

    let result: Int = add(10, 20)
    print result

Type-check a program:

    pea typecheck program.pea

PeaLang includes support for:

- primitive types
- records
- nullable types
- unions
- generics
- protocols
- generic substitution
- type inference foundations
- Result
- Option
- Future
- function contracts
- semantic analysis

## Compiler and Virtual Machine

PeaLang provides both a tree-walking interpreter and portable bytecode virtual machine.

Compile:

    pea compile program.pea

Run using the VM:

    pea vm program.pea

PeaLang's bytecode/VM architecture includes:

- portable PEAC bytecode
- compiler
- constant pool
- stack virtual machine
- function call frames
- closures
- exception handling
- module imports
- source mapping
- resource accounting
- async suspension and resume
- debugger integration

## Embedding PeaLang

PeaLang is intended to operate as an extension language inside existing applications.

Supported integration directions include:

- Python
- FastAPI
- Java
- TypeScript
- React
- browser/WebAssembly environments

The goal is not to replace host languages.

Instead:

    Host Application
          |
          +-- Python
          +-- Java
          +-- FastAPI
          +-- React
          |
          +-- PeaLang
                |
                +-- Rules
                +-- Workflows
                +-- Automation
                +-- Integration
                +-- Data processing
                +-- Controlled user extensions

## Data Engineering

PeaLang includes a growing data-processing and data-engineering stack.

Capabilities include:

- DataFrame
- LazyFrame
- schema inference
- CSV
- JSON
- JSONL
- transformations
- joins
- group-by
- aggregations
- expressions
- null handling
- pivot/unpivot
- window operations
- analytics
- statistics
- time-series processing
- forecasting
- scalable execution
- partitioning
- spill processing

## Databases and Connectors

PeaLang includes database and connector foundations for environments including:

- SQLite
- DuckDB
- PostgreSQL
- MySQL/MariaDB
- SQL Server
- Oracle
- REST
- GraphQL
- OData
- SFTP
- S3
- Azure Blob Storage
- Azure Data Lake Storage
- Google Cloud Storage
- Microsoft Graph
- SharePoint

Optional third-party dependencies may be required for individual connectors.

## Streaming and Messaging

PeaLang includes streaming and messaging capabilities including:

- Kafka
- RabbitMQ
- WebSocket messaging
- event-time processing
- watermarks
- late-event handling
- tumbling windows
- sliding windows
- checkpointing
- replay
- idempotent delivery

## Workflow Orchestration

PeaLang includes DAG-based orchestration support.

Capabilities include:

- DAG definitions
- task dependencies
- cycle detection
- topological ordering
- execution layers
- retries
- backoff
- persistent state
- scheduling
- logical execution dates
- run history
- backfill
- idempotency

## Machine Learning

PeaLang includes dependency-light machine-learning and production-ML foundations.

Capabilities include:

- preprocessing
- linear regression
- logistic regression
- evaluation metrics
- cross-validation
- regularization
- multiclass classification
- model persistence
- pipelines
- model governance
- inference
- model monitoring
- drift diagnostics
- fairness diagnostics
- calibration
- model registry
- serving
- MLOps
- optional ONNX Runtime integration
- optional PyTorch interoperability

## Distributed Execution

PeaLang contains engine-neutral distributed execution foundations with optional adapters for:

- local execution
- Apache Arrow
- Polars
- Apache Spark

The architecture is intended to allow PeaLang execution plans to use different processing engines without forcing PeaLang programs to be rewritten around a specific backend.

## Serving and Operations

PeaLang includes operational foundations for:

- FastAPI serving
- distributed serving
- rate limits
- concurrency limits
- timeouts
- health checks
- readiness checks
- deployment state
- observability
- OpenTelemetry integration
- Kubernetes deployment
- Kubernetes security controls
- graceful shutdown
- rollback

## Security

Security is a core PeaLang design concern.

PeaLang includes capabilities covering:

- capability-controlled execution
- runtime resource limits
- secure package handling
- SHA-256 integrity verification
- Ed25519 package signatures
- signed registry metadata
- key rotation/revocation foundations
- HTTPS-only registry policies
- secret-provider abstractions
- dependency-confusion defenses
- safe package extraction
- security regression tests
- SBOM generation
- provenance
- release integrity
- supply-chain verification
- GitHub CodeQL scanning

### SFTP Security

Unknown SSH hosts are rejected by default in v0.99.6.

Do not disable host-key verification in production integrations.

### Package Security

For public package distribution, use PeaLang's Ed25519 public/private-key signing infrastructure.

Legacy HMAC support exists primarily for backwards-compatible controlled/internal environments.

### Secrets

Never commit:

- passwords
- API keys
- access tokens
- signing private keys
- SSH private keys
- database credentials
- `.env` files containing secrets

Supply credentials at runtime using an appropriate secret-management mechanism.

## Standard Library

PeaLang provides a stable `std.*` namespace covering common application functionality.

Inspect available modules using:

    pea stdlib

The standard-library architecture includes explicit capability gates for sensitive operations such as:

- filesystem access
- HTTP/network access
- logging
- concurrency

## Testing

Run the complete Python test suite:

    python -m pytest -q

The v0.99.6 release baseline passes:

    612 tests

PeaLang also maintains conformance, compatibility, security, retention, and release-readiness tests.

## CI Validation

The repository contains GitHub Actions workflows covering:

    Windows / Linux / macOS
    Python 3.10
    Python 3.11
    Python 3.12
    Python 3.13

Additional workflows cover:

    Java 17
    Java 21
    Node 20
    Node 22
    Node 24
 