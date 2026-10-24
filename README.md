# PeaLang 0.63.0 RC2

PeaLang is an embeddable extension language and local-first data platform for controlled rules, workflows, automation, host integration, data processing, analytics, machine learning, and model serving.

**0.63.0 RC2 is a stabilization release.** It preserves the RC1 feature freeze, validates public API compatibility against RC1, refreshes automated validation evidence, and adds focused migration and operator guidance. It does not intentionally introduce a breaking API or destructive schema migration.

> Release status: automated RC2 gates pass. PeaLang 1.0 GA remains blocked until the external license, live-integration, security, soak-testing, and signed-publication gates are completed.

## Release highlights

- RC1-to-RC2 public API compatibility check
- Zero removed public symbols
- Zero changed public signatures
- Public API snapshot and SHA-256 digest
- Upgrade compatibility mapping for 0.60, 0.61, 0.62, and 0.63 RC1
- RC1-to-RC2 migration guidance
- Threat model and release-candidate gate documentation
- Release manifest, retention audit, and integrity report
- 430 automated tests passed
- 500 conformance cases passed
- 250 fuzz iterations completed
- Zero automated test failures

## Core platform capabilities

### Language and runtime

- Interpreter, REPL, parser, evaluator, and command-line tooling
- Bytecode compiler and virtual machine
- Native async VM and structured concurrency foundations
- Type system, runtime validation, diagnostics, debugger, and DAP foundations
- Standard library and package ecosystem
- Signed package and registry foundations
- Embedding support for Python, Java, FastAPI, React, TypeScript, browser, and WebAssembly-oriented integrations

### Data platform

- DataFrame and LazyFrame APIs
- Expressions, joins, grouping, aggregation, null handling, pivot/unpivot, and windows
- CSV, JSON, JSONL, Parquet, and other structured-data foundations
- SQL and database adapters for SQLite, DuckDB, PostgreSQL, MySQL/MariaDB, SQL Server, and Oracle
- REST, GraphQL, OData, and SFTP connectors
- Amazon S3, Azure Blob Storage, Azure Data Lake Storage Gen2, and Google Cloud Storage connectors
- Microsoft Graph and SharePoint foundations
- Runtime secret providers and connector certification metadata

### Analytics and machine learning

- Descriptive statistics, correlation, frequency distributions, crosstabs, ranking, rolling calculations, and profiling
- Time-series resampling, lag/lead, percentage change, expanding windows, exponential moving averages, and interpolation
- Baseline forecasting and forecast evaluation
- Linear, ridge, lasso, binary logistic, and multiclass logistic regression foundations
- Scaling, imputation, categorical encoding, train/test splitting, cross-validation, and grid search
- Model cards, reproducibility manifests, schema validation, and coefficient reports

### MLOps and serving

- Versioned and integrity-checked model bundles
- Batch and audited inference
- Drift and fairness diagnostics
- Model registry lifecycle and promotion policies
- Portable production-pipeline serialization
- SQLite monitoring and prediction-audit stores
- FastAPI serving adapter and `pea-serve` CLI
- Authentication hooks, request limits, rate limiting, concurrency control, and timeouts
- Structured logging, correlation IDs, tracing hooks, live reload, canary routing, and rollback controls
- Redis-compatible distributed state and Kubernetes operational/security manifests
- SBOM, provenance, checksums, artifact verification, and release-candidate governance

## Requirements

- Python 3.10 or later
- Python 3.11 or 3.12 recommended for RC evaluation
- Windows, Linux, or macOS

Optional integrations require their provider libraries. Examples include `pyarrow`, `polars`, `pyspark`, `paramiko`, `boto3`, Azure SDK packages, Google Cloud Storage, Redis, FastAPI, Uvicorn, and `cryptography`.

## Installation

### Install from the wheel

Place `pealang-0.63.0rc2-py3-none-any.whl` in your working directory and run:

```bash
python -m pip install --upgrade pip
python -m pip install pealang-0.63.0rc2-py3-none-any.whl
```

Verify the installation:

```bash
pea --version
pea --help
```

### Install from the source ZIP

Extract `PeaLang_v0.63.0_RC2.zip`, open a terminal in the extracted project folder, and run:

```bash
python -m venv .venv
```

Activate the environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
.venv\Scripts\activate.bat
```

Linux or macOS:

```bash
source .venv/bin/activate
```

Install PeaLang:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

For development and testing:

```bash
python -m pip install pytest
python -m pytest -q
```

## Quick start

### Start the REPL

```bash
pea repl
```

Inside the REPL, use the PeaLang help command documented by the installed CLI. Do not enter shell commands such as `python -m pytest` inside the language REPL.

### Run a PeaLang program

```bash
pea run app.pea
```

### Inspect available CLI commands

```bash
pea --help
```

Additional installed commands may include:

```bash
pea-ml --help
pea-serve --help
```

## Python embedding example

```python
from pealang.data import DataFrame

employees = DataFrame([
    {"employee": "A", "department": "HR", "score": 82},
    {"employee": "B", "department": "Engineering", "score": 91},
])

print(employees.describe().to_dicts())
```

## SQL example

SQLite works through the Python standard library:

```python
from pealang.sql import connect

with connect("sqlite:///example.db") as database:
    database.execute(
        "create table if not exists employees(id integer primary key, name text)"
    )
    database.execute(
        "insert into employees(name) values (?)",
        ("Rajesh",),
    )
    database.commit()

    result = database.query("select * from employees")
    print(result.to_dicts())
```

Always use SQL parameters for values instead of building SQL strings through concatenation.

## Connector example

```python
from pealang.connectors import connector, bearer

api = connector(
    "rest",
    "https://api.example.com",
    headers=bearer("TOKEN_FROM_SECRET_PROVIDER"),
)

users = api.dataframe("/users", records_path="items")
print(users.to_dicts())
```

Credentials should be supplied at runtime through environment variables, Azure Key Vault, AWS Secrets Manager, or another secret provider. Do not commit tokens or passwords.

## Analytics example

```python
from pealang.data import DataFrame

sales = DataFrame([
    {"month": "2026-01", "amount": 100},
    {"month": "2026-02", "amount": 120},
    {"month": "2026-03", "amount": 135},
])

print(sales.describe().to_dicts())
print(sales.pct_change("amount").to_dicts())
print(sales.rolling("amount", window=2).to_dicts())
```

## Machine-learning example

```python
from pealang.data import DataFrame
from pealang.ml import LinearRegression

training = DataFrame([
    {"experience": 0, "salary": 30000},
    {"experience": 1, "salary": 35000},
    {"experience": 2, "salary": 40000},
])

model = LinearRegression().fit(
    training,
    features=["experience"],
    target="salary",
)

prediction = model.predict(DataFrame([{"experience": 3}]))
print(prediction.to_dicts())
```

The built-in ML implementations are suitable for baselines, education, embedded use, and small-scale workloads. Use mature specialist libraries and independent validation for high-scale or consequential production models.

## Model serving

Validate a deployment before starting it:

```bash
pea-serve deploy-check deployment.json pipeline.json
```

Start the optional FastAPI/Uvicorn serving runtime:

```bash
pea-serve serve pipeline.json \
  --version 0.63.0rc2 \
  --host 127.0.0.1 \
  --port 8000 \
  --api-key YOUR_RUNTIME_SECRET
```

Serving endpoints include:

- `GET /live`
- `GET /ready`
- `GET /metrics`
- `POST /predict`

## RC2 compatibility and migration

RC2 is intended to be compatible with RC1:

- Removed public symbols: 0
- Changed public signatures: 0
- Destructive schema migrations: none intentionally introduced

Before upgrading:

1. Back up model registries and monitoring databases.
2. Verify RC1 artifacts and checksums.
3. Install RC2 in an isolated environment.
4. Review `RC1_TO_RC2_API_COMPATIBILITY.json`.
5. Run language, package, connector, analytics, and serving smoke tests.
6. Validate rollback to RC1 before production promotion.

See `docs/MIGRATION_RC1_TO_RC2.md` for the focused migration guide.

## Validation

Run the automated test suite:

```bash
python -m pytest -q
```

Run the conformance command:

```bash
python -m pealang.cli conformance
```

RC2 recorded:

- 430 automated tests passed
- 500 conformance cases passed
- 250 fuzz iterations completed
- Zero automated failures
- RC1-to-RC2 public API compatibility passed

## RC2 versus later development

PeaLang 0.63 RC2 is the frozen stabilization line. The 0.64 alpha line begins new feature development, including distributed-compute work. Do not treat alpha features as part of RC2, and do not backport broad new APIs into RC2.

## GA release gates

PeaLang 1.0 GA remains blocked until all of the following are complete:

1. Manual third-party license review
2. Live database and cloud connector certification
3. Live SFTP, SharePoint, Redis, and Kubernetes testing
4. Independent security assessment
5. Multi-hour production-style soak and load testing
6. Signed publication of the wheel, source archive, SBOM, provenance statement, and release manifest

Passing the automated RC2 suite does not replace these external gates.

## Documentation map

Start with these files:

- `README.md`: installation and platform overview
- `RELEASE_NOTES.md`: RC2 release notes
- `CHANGELOG.md`: cumulative change history
- `VERSION_HISTORY.md`: release-by-release history
- `docs/API_STABILITY_POLICY.md`: public API and deprecation policy
- `docs/RC2_STABILIZATION.md`: RC2 stabilization scope
- `docs/MIGRATION_RC1_TO_RC2.md`: migration guidance
- `RC2_GATE_STATUS.md`: automated and external gate status
- `PUBLIC_API_SNAPSHOT.json`: RC2 public API snapshot
- `PUBLIC_API_SNAPSHOT_RC1.json`: preserved RC1 API snapshot
- `RC1_TO_RC2_API_COMPATIBILITY.json`: compatibility result
- `RELEASE_MANIFEST.json`: release metadata
- `RELEASE_INTEGRITY.md`: validation summary
- `RETENTION_AUDIT.json`: prior-version retention evidence

The repository also contains dedicated guides for embedding, connectors, databases, analytics, ML, MLOps, serving, distributed operations, Kubernetes security, and supply-chain controls.

## Security

- Never store credentials in PeaLang source files, connector definitions, model bundles, or Git history.
- Verify checksums and signatures before installing or loading release artifacts.
- Keep API keys, bearer tokens, database passwords, signing keys, and encryption keys in runtime secret providers.
- Review generated Kubernetes NetworkPolicy rules for your actual Redis, telemetry, registry, DNS, and external-service destinations.
- Treat model fairness and drift metrics as diagnostic evidence, not as automatic approval for consequential decisions.

## Release status

| Item | Status |
|---|---|
| Version | 0.63.0rc2 |
| Release type | Release Candidate 2 |
| Feature scope | Frozen |
| Automated tests | 430 passed |
| Conformance | 500 passed |
| Fuzzing | 250 iterations |
| RC1 API compatibility | Passed |
| Automated RC2 gate | Passed |
| PeaLang 1.0 GA | Blocked pending external gates |

## License

Review the repository license file and `DEPENDENCY_LICENSE_INVENTORY.json` before redistribution. Third-party optional integrations remain subject to their own licenses. Manual third-party license review is still a release-blocking RC gate.
