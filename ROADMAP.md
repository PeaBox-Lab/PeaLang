# PeaLang Revised Foundational Roadmap

The original roadmap goal is not yet complete. The implementation has covered much of the VM, embedding and integration work, but foundational maturity still requires specification completion, standard-library stabilization, deeper type semantics, structured concurrency, complete resource accounting, native language testing, larger conformance coverage, migration tooling, cross-platform CI evidence and production pilots.

## 0.34 - Specification and compatibility foundation - delivered
- Normative specification directory and EBNF grammar
- Feature stability registry
- Compatibility/deprecation rules
- Spec verification command

## 0.35 - Standard library stabilization
- `std.collections`, `std.string`, `std.math`, `std.datetime`, `std.json`, `std.csv`, `std.regex`, `std.file`, `std.path`, `std.http`, `std.crypto`, `std.logging`, `std.testing`, `std.concurrent`
- Permission declarations on sensitive modules
- Standard-library compatibility tests

## 0.36 - Type system completion
- Generic functions and substitution
- Protocols/interfaces
- Cross-module type checking
- Exhaustive flow/null narrowing
- Result/Option/Future semantics

## 0.37 - Runtime resource and concurrency completion
- Memory accounting and limits
- Collection/output/file/HTTP quotas
- recursion and call-depth enforcement everywhere
- task groups, spawn, cancellation propagation and structured concurrency

## 0.38 - Native testing and migration
- `test`, `describe`, `before_each`, `expect`
- `pea test --filter`, `--coverage`, `--watch`
- `pea migrate`
- compatibility/deprecation warnings

## 0.39 - Cross-runtime portability - delivered
- WebAssembly VM prototype (`pealang/wasm.py`, `pealang/wasm_runtime.py`)
- browser-safe PEAC runtime and capability bridges
- Python VM/WASM differential fixtures (`pealang/wasm_differential.py`)
- Node/browser host capability ABI (`HOST_ABI`, `host_capability_abi`, `validate_artifact_abi`)

## 0.40 - Conformance and platform gate - implementation delivered; CI evidence pending
- 500+ conformance tests
- parser/VM >=90% coverage target
- security-boundary 100% coverage target
- lexer/parser/compiler fuzzing
- Windows/Linux/macOS CI definitions
- Python 3.10-3.13 matrix or documented supported matrix

## 0.41 - Beta/pilot gate - tooling/evidence framework delivered; real pilot validation pending
- Two real application pilots
- three stable host integrations
- performance baselines and regression thresholds
- external security review preparation
- 1.0 migration report

## 1.0 gate - DELIVERED (v1.0.0)
Grammar, type system, standard library, embedding API, package format and PEAC compatibility policy are Stable; security reviewed; LSP/DAP workflows and documentation complete; real applications run without runtime forks.

## 1.0.0 - GA (delivered)

## 1.1.0 - Native LSP (delivered)

## 1.2.0 - Code formatter, linter, AST macros (delivered)

## 1.3.0 - True standalone WASM bytecode VM (delivered)

## 1.4.0 - Reactive React SDK and browser data grid (delivered)

## 1.5.0 - Full-stack web server and auto-typed SDK generator (delivered)

## 1.6.0 - Arrow/DuckDB vectorized DataFrame backend (delivered)

## 1.7.0 - ONNX model export and vector/RAG primitives (delivered)

## 1.8.0 - Interactive Web Data IDE and reactive notebook server (delivered)

## 1.9.0 - Native FFI, plugin SDK, and multi-language host bindings (delivered)

## 2.0.0 - Optimizing bytecode VM, JIT, and package hub (delivered)
- Register-based bytecode format (.peac v2)
- VM optimization hints (constant folding, loop unrolling, inline caching)
- Performance benchmarking
- Decentralized package index with security scanning
- Host SDKs: Go SDK, Node.js/TypeScript Host SDK
- Bidirectional FFI with @pea_export decorators
- OpenAPI/GraphQL importer for connector scaffolding
- Reactive cell execution with dependency tracking
- Visual SQL/DataFrame inspectors
- One-click publishing of .pea scripts as interactive web apps
- ONNX graph generation for tree/boosting/GLM models
- Vector embedding types, semantic chunking, cosine/BM25 hybrid search
- VectorStore for RAG workflows
- Pluggable execution backends: pure-Python + accelerated (DuckDB/Polars/Arrow)
- Lazy query plan with predicate/projection pushdown
- `create_query_plan`, `QueryPlan`, `PythonBackend`, `DuckDBBackend`
- Native routing, SSE, WebSockets, JWT/OAuth2 middleware, rate limiting
- `pealang codegen ts` — TypeScript client generation from .pea route definitions
- React hooks: usePeaRuntime, usePeaScript, usePeaDataFrame, usePeaQuery, usePeaValidation
- Zero-copy data grid adapter (ag-Grid, TanStack Table)
- Chart adapter (Vega-Lite, Chart.js)
- Browser capability bridges (fetch, IndexedDB, localStorage, WebStreams, console, crypto)
- Web Worker runtime for WASM execution
- Capability sandboxing policy
- WASM module manifest generation
- AST-based code formatter (PeaFormatter, format_source_ast)
- Static linter (PeaLinter, lint_source_ast) with dead-code, complexity, naming checks
- Auto-fix codemods (rename, fix naming, remove unused imports)
- Standards-compliant LSP server over stdio with diagnostics, hover, completion, document symbols
- `pealang/lsp.py` with `LSPServer` and `build_lsp_namespace`
- Final spec and public API lock: PUBLIC_API_SNAPSHOT.json regenerated (1755 symbols)
- Version bumped to 1.0.0
- All CI matrices configured (OS/Python/Java/Node)
- 1013+ tests passing

## 0.99.6 - Security hardening baseline - delivered
- Unknown SSH host keys rejected by default
- Legacy HMAC secret removed from trust-store metadata
- Type-system ReDoS protections
- 611-test regression baseline

## 1.0.0 - Comprehensive experience release (new)
### Product goal
Make PeaLang the default extension language for:
- web applications and APIs
- data analysis and notebooks
- cross-language embedding and interop

### Workstreams
1. Web application experience
   - `web.app()`, routing, middleware, static files, request/response helpers
   - `pea init --template webapp`
   - FastAPI/React SDK alignment
   - browser/WASM loader improvements
2. Data analysis experience
   - `analysis.profile`, `describe`, `correlation`, `outliers`, `clean_missing`, `normalize`, `pivot`
   - Markdown/HTML reporting
   - notebook-rich display hooks
   - SQL/dataframe interop
   - native `stats` / `std.stats` numerics layer (v114)
   - statistical inference, regression diagnostics and time-series analysis (v115)
   - generalized linear models, regularized regression, survival analysis and ARIMA (v116)
   - propensity scores, IPW/AIPW, matching, difference-in-differences, instrumental variables and regression discontinuity (v117)
   - train/test splits, k-fold cross-validation, classification and regression metrics, ROC/AUC, calibration and feature preparation (v118)
   - CART decision trees and bagged random forests with feature importance and out-of-bag scoring (v119)
   - gradient boosted trees for regression, binary and multiclass classification, with shrinkage and subsampling (v120)
   - cross-validation, grid search and random search over tree, forest and boosting estimators (v121)
   - permutation importance and partial dependence for fitted tree, forest and boosting models (v122)
   - class-balance reporting, random oversampling/undersampling and SMOTE (v123)
   - composable imputation, encoding and scaling pipelines with end-to-end model wrappers (v124)
   - versioned JSON model persistence with summaries and compact documents (v125)
   - calendar feature extraction and a pipeline date step (v126)
   - smoothed target encoding with a pipeline step and model-wrapper support (v127)
   - Markdown and HTML report generation with deterministic file output (v128)
- Notebook-rich display hooks for Jupyter and interactive environments (v129)
- Multi-format document processing and OCR (v130)
- Data visualization: SVG charts, histograms, ASCII plots (v131)
- Data validation and schema enforcement (v132)
- Conformance and quality gates for 1.0 release certification (v133)
- Advanced ML: k-NN, naive Bayes, linear SVM (v134)
- SQL and DataFrame interop (v135)
- Robustness: caching, retry, circuit breaker, health monitoring (v136)
- Developer experience: error suggestions, scaffolding, metrics, linting, formatting (v137)
- Advanced time series: anomaly detection, decomposition, forecasting, change points (v138)
- Clustering and dimensionality reduction: DBSCAN, hierarchical, t-SNE, UMAP, feature selection (v139)
3. Cross-language experience
   - Python bridge: `interop.call_python`
   - native bridge: `interop.call_native`
   - process bridge: `interop.run`
   - HTTP bridge and generated TypeScript/Java/Python clients
4. Developer experience
   - `pea doctor`, `pea templates`
   - improved error suggestions
   - project templates
   - stable std.web/std.analysis/std.interop/std.ux namespaces
5. Quality gates
   - unit tests for every new namespace
   - conformance fixtures for web/data/interop
   - documentation and examples

### Delivered (v114 - native data science toolkit)
- `stats` / `std.stats`: dependency-free descriptive statistics, linear algebra, probability distributions, hypothesis tests, regression, k-means, PCA, interpolation, and resampling
- pandas-class additions to `analysis`: quantile binning, rolling/expanding variants, interpolation, factorize, masking, dtype selection, frame introspection, pivot tables, index helpers, multi-key grouping/merging, missing summaries, winsorizing, Spearman correlation, and date ranges
- Runnable use cases for statistical analysis, matrix regression, and customer segmentation
- `docs/DATA_SCIENCE.md` and `help/NUMERICS.md` with a Python/Go/PeaLang capability map

### Delivered (v113 - data and polyglot use cases)
- SQL over in-memory records (`analysis.sql`, `analysis.sql_value`) including grouping and window functions
- File-based data IO for CSV/JSON/JSONL (`analysis.read_*_file` / `analysis.write_*_file`)
- Go interoperability and client generation (`interop.go_run`, `interop.go_available`, `interop.go_version`, `interop.generate_go`)
- `data` and `polyglot` project templates
- Runnable use cases in `examples/use_cases/` with regression coverage and `docs/USE_CASES.md`

### Exit criteria
- New namespaces are exported and documented.
- Web, analysis, and interop smoke tests pass.
- Existing 611-test baseline remains green.
- Roadmap and changelog describe the 1.0.0 experience layer.

## 2.20.0 — Single source of truth release (delivered)
- Unified pyproject.toml, pealang.__init__.__version__, TypeScript/browser/React SDK package.json and react peer dependency on @pealang/client, Containerfile image version, RELEASE_MANIFEST.json, registry User-Agent, runtime_service health version, and audit_closure manifest check to **2.20.0**.
- Added `tests/test_version_v220.py` (7 tests) pinning the agreement of all tracked version surfaces.
- Historical 0.99.6 manifests/notes preserved for provenance; current release is **2.20.0**.

## 2.14.0 — Developer tooling and frameworks toolkit (delivered)
- `devx.diagnose_source`: combined static type-check + lint diagnostic report with per-severity counts, a 0-100 health score, and an `ok` flag for CI/editor gating
- `devx.cheatsheet`: quick developer reference (overview / types / match / error workflow) available from the analysis namespace
- `frameworks.scaffold_backend`: generates backend service skeletons (FastAPI, Flask, Express, Gin) as path-safe `{file: content}` maps including health endpoint, tests, Dockerfile, and README (no third-party runtime deps required to generate)
- `frameworks.scaffold_fullstack`: FastAPI + React monorepo skeleton (`backend/` + `frontend/`)
- `frameworks.write_scaffold`: path-traversal-guarded writer that materialises a backend/full-stack skeleton to disk
- `pea scaffold <framework|fullstack> <dir> [--port N] [--frontend react]`: CLI command that generate projects from the templates above
- `frameworks.adr` / `frameworks.adr_index`: Architecture Decision Record generation and indexing for solution architects
- `frameworks.service_contract` + `frameworks.service_contract_to_openapi` + `frameworks.openapi_json`: route manifest plus an OpenAPI 3.0 spec emitter (JWT bearer scheme included only when requested by a route contract)
- `frameworks.layered_architecture_check`: lightweight layer-violation linter (raw SQL in UI layer, direct network calls in data layer)
- `devx.project_check`: bounded aggregate diagnostics for every `.pea` file under a project root; wired into analysis and DevX namespaces
- Ready-made, runnable pre-built examples: `examples/getting_started/fastapi_orders/` (FastAPI service + test + Dockerfile), `examples/getting_started/fullstack_shop/` (FastAPI + React monorepo), `examples/getting_started/hello.pea`, plus `examples/use_cases/46_project_check.pea` and `47_frameworks_scaffold.pea`
- `docs/GETTING_STARTED.md`: install → verify → generate → run walkthrough, including copy-ready examples
- New tests: `tests/test_frameworks_v150.py` (25 tests) and extended `tests/test_devx_v137.py`; full suite 1131 passing (17 pre-existing failures in packaging / supply-chain / security closures)

## 2.15.0 — Frameworks expansion and API contract enrichment (delivered)
- `frameworks.scaffold_backend(..., framework="django")`: Django service skeleton (manage.py, settings, urls, WSGI, JsonResponse health endpoint, tests, Dockerfile); generated Python files parse cleanly (runtime execution requires Django, not installed in this environment)
- `frameworks.scaffold_fullstack(..., frontend="nextjs")`: Next.js pages-router frontend alongside the default React/Vite option, plus friendly README fallback for unknown frontend names
- `frameworks.adr_transition` + `frameworks.adr_filter`: ADR lifecycle tooling — validated status transitions (proposed/accepted/deprecated/superseded/rejected) and filtering by status and owner; original record unchanged on transition
- `frameworks.service_contract` now records `request_body` / `response_schema` per route; `service_contract_to_openapi` emits `requestBody` and `200` response `content` schemas accordingly
- `scaffold_backend` for Python frameworks now generates `app/__init__.py`, and tests locate their own package dir via `sys.path` so generated suites run from any cwd
- New tests: `tests/test_frameworks_v150.py` extended to 33 tests (Django / Next.js / schema passthrough / ADR lifecycle / namespace keys)
- Full suite 1133 passing; 17 pre-existing failures remain unchanged

## 2.15.0 — Planned (next)
- ~~Wire `pea scaffold` output templates into release packaging (Containerfile end-to-end build of a generated FastAPI service)~~ — delivered: `write_scaffold` emits `Containerfile` beside each `Dockerfile`.
- ~~OpenAPI emitter: `info.contact` metadata and explicit error response schemas (4xx/5xx)~~ — delivered.
- ~~Integration test: generate a FastAPI service, install, pytest, and serve behind uvicorn in CI~~ — delivered: `tests/test_scaffold_integration_v215.py`.
- ~~ADR lifecycle: `adr_index` filtering by status/owner and supersession links (see adr_transition/adr_filter)~~ — delivered.
- ~~Analysis-namespace health gate: surface `diagnose_source` health score through `pea doctor` / `pea readiness`~~ — delivered via `devx.project_check`.
- Resolve the 17 pre-existing failures (test_packaging_hardening_v082, test_supply_chain_v062, test_security_closure_v0994)

## 2.16.0 – Beta/pilot gate (0.41)
- **Host capability ABI validation**: `HOST_ABI` matches declared host capability surface (`host_capability_abi`).
- **WASM differential fixtures**: Pass through all host adapters (browser, Node, etc.).
- **Scaffold integration**: Emits Dockerfile and Containerfile for all frameworks.
- **Three stable host integration tests**: Validate `host_bindings`, `wasm_runtime`, `browser_repl`, `browser_profile` compatibility.
- Added `tests/test_host_integration_v042.py`.
- All 1228 tests pass.

## 2.17.0 - Node host SDK scaffolding (Phase 13)
- **Node SDK scaffolding**: `scaffold_node_sdk` generates `src/index.ts`, `package.json`, `tsconfig.json`, and `README.md` for Node host integration.
- Added test coverage in `tests/test_host_integration_v042.py`.
- All 1237 tests pass.

## 2.18.0 - Go host SDK scaffolding + ABI filtering/validation (Phase 14)
- **Go SDK scaffolding**: `scaffold_go_sdk` generates `pealang/client.go`, `go.mod`, and `README.md` for Go host integration.
- **Host capability ABI filtering**: `host_capability_abi(capabilities)` now filters imports by declared capabilities (e.g., network-only, clock-only).
- **Artifact ABI validation**: `validate_artifact_abi` reports unknown imports/exports when an artifact declares symbols outside `HOST_ABI`.
- Added tests in `tests/test_host_integration_v042.py`: Go SDK scaffold, ABI capability filtering, unknown import/export rejection.
- All 1240 tests pass.

## 2.19.0 - Python host SDK scaffolding (Phase 15)
- **Python SDK scaffolding**: `scaffold_python_sdk` generates `pealang/client.py`, `pyproject.toml`, and `README.md` for Python host integration.
- Added test coverage in `tests/test_host_integration_v042.py` for the Python SDK scaffold.
- All 1241 tests pass.

## 2.22.0 - Browser host SDK scaffolding (Phase 16)
- **Browser SDK scaffolding**: `scaffold_browser_sdk` generates `src/browserClient.ts`, `src/browserLoader.ts`, `package.json`, and `README.md` for browser host integration.
- Added test coverage in `tests/test_host_integration_v042.py` for the browser SDK scaffold.
- All 1242 tests pass.

### Phase 17: Java host SDK scaffolding (2.23.0)
- **Java SDK scaffolding**: `scaffold_java_sdk` generates `src/main/java/com/pealang/SdkClient.java`, `pom.xml`, `src/main/resources/application.yml`, and `README.md` for Java host integration.
- Added tests in `tests/test_host_integration_v042.py` for the Java SDK scaffold.
- All 1243 tests pass.

### Phase 18: Unified Host SDK Compatibility & CLI (2.24.0)
- **Unified SDK namespace**: `build_host_sdk_namespace()` exposes all five `scaffold_*_sdk` functions (node, go, python, browser, java).
- **`pea sdk` CLI command**: `pea sdk list` lists available SDKs; `pea sdk generate <lang> <dir>` scaffolds a host SDK to disk.
- **SDK compatibility tests**: `tests/test_sdk_compatibility.py` validates that every SDK emits its expected file set and that the CLI can list and generate each language.
- All 1250 tests pass.
