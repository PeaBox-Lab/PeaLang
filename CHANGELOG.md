# Changelog

## 1.0.0-experience (ongoing) - 2026-11-08

### Language and Runtime
- Added list comprehensions with filters and destructuring patterns.
- Added dict comprehensions with destructuring patterns.
- Added optional chaining (`?.` for properties, indexes, calls) and null coalescing (`??`).
- Added anonymous function expressions.
- Added multiline list/dict literals and function-call argument formatting.
- Added pattern matching as statements and expressions, including literal/wildcard/OR cases and guards.
- Added destructuring in `let` declarations and `for` loops (lists and records).
- Added membership operators `in` and `not in`.
- Added/expanded builtins: `enumerate`, `zip`, `sorted`, `reversed`, `map`, `filter`, `sum`, `any`, `all`, `min`, `max`, `abs`, `items`, `list`, `dict`, `bool`, `float`.

### Web (`web` / `std.web`)
- Added lightweight web app framework: routing, middleware, static files, request/response helpers.
- Added path params (`:id`), params/query/header/cookie access, JSON/form parsing helpers.
- Added response helpers (`json`, `html`, `text`, `redirect`, `error`), templates, and cookie setting.
- Added route groups (`app.group()`), `patch`/`options` methods, custom 404/error handlers.
- Added CORS support with preflight/header application.
- Added OpenAPI 3.0 generation from registered routes.

### Data Analysis (`analysis` / `std.analysis`)
- Added profiling, descriptive statistics, correlation, correlation matrix, quantiles, and outlier detection.
- Added cleaning/transforms: `clean_missing`, `fillna`, `impute`, `normalize`, `rename`, `drop_duplicates`, `sort_by`, `select`, `filter_rows`, `query`, `add_column`, `cumsum`.
- Added reshaping/combining: `group_by`, `pivot`, `join`/`merge`, `concat`, `sample`, `unique`, `value_counts`, `top_values`, `head`, `tail`.
- Added outputs/visualization: `to_csv`, `to_markdown`, `to_html`, `bar_chart`, `line_chart`, `summary`.

### Interop (`interop` / `std.interop`)
- Added Python bridge (`call_python`, `import_python`), native ctypes bridge, and process execution.
- Added HTTP helpers (`http_get`, `http_post`), JSON-RPC helper, JSON piping, environment lookup, and executable discovery.
- Added client/code stub generation for TypeScript, Java, and Python.

### UX, CLI, and Project Scaffolding
- Added `ux`/`std.ux` diagnostics (`doctor`, `explain`, `suggest`).
- Added project templates: `default`, `webapp`, `analysis`, `library`, `interop`.
- Added CLI commands/features: `eval -e`, `lint`, `doctor`, `templates`, `info`, improved version handling, and template-aware `init`.

### Language and Runtime (v103 additions)
- Added power operator `**`.
- Added helpers/builtins: `get`, `has`, `merge`, `push`, `pop`, `slice`, `contains`, `trim`, `replace`, `starts_with`, `ends_with`, `json_parse`, `json_dump`, `safe`, `now_ms`.
- Note: `//` remains a line-comment token (for compatibility with existing comment syntax); floor division can use `int(a / b)`.

### Web (v103 additions)
- Added route groups (`app.group()`), `patch`/`options` handlers, CORS preflight handling.
- Added helpers: `web.validate`, `web.file`, `web.sse`, `web.response`, `web.rate_limit`, `web.bearer_auth`.

### Data Analysis (v103 additions)
- Added I/O/conversion: `from_csv`, `from_json`, `to_json`.
- Added transforms/stats: `between`, `clip`, `mode`, `nunique`, `count`, `melt`, `transpose`.

### Interop and CLI (v103 additions)
- Added interop: `json_rpc`, `pipe_json`, `env`.
- Added CLI: `pea eval -e`, `pea info` (and version/info improvements).

### Language and Runtime (v104 additions)
- Added builtins/helpers: `chunk`, `flatten`, `uniq`, `pick`, `omit`, `clamp`, `uuid`, `randint`, `b64encode`, `b64decode`, `now_iso`.

### Data Analysis (v104 additions)
- Added `rank`, `pct_change`, `diff`, `rolling_mean`, `schema`.

### Web (v104 additions)
- Added `web.request_id()` middleware factory, `web.json_error()`, `web.etag()`.

### CLI (v104 additions)
- Added `pea new` (alias for `init`) and `pea serve-web <file>` (best-effort: runs file, serves exported `app` if not already serving).

### Language and Runtime (v105 additions)
- Added builtins/helpers: `coalesce`, `repeat`, `times`, `find`, `find_index`, `pluck`, `index_by`, `sort_by` (list by key).

### Data Analysis (v105 additions)
- Added `zscore`, `histogram`, `cut`.

### Web (v105 additions)
- Added `cache_control`, `basic_auth`, `no_content`, `created`, `accepted`.

### CLI (v105 additions)
- Added `pea eval -f <file>`.

### Language and Runtime (v106 additions)
- Added type predicates: `is_null`, `is_list`, `is_dict`, `is_string`, `is_number`, `is_bool`.
- Added helpers: `identity`, `tap`, `pad_start`, `pad_end`, `lines`, `words`, `floor`, `ceil`, `log`, `exp`, `pow`.

### Data Analysis (v106 additions)
- Added `ffill`, `bfill`, `dropna`, `cast`, `crosstab`.

### Web (v106 additions)
- Added `ok`, `problem` (application/problem+json), `pagination`, `parse_basic_auth`.

### Interop and CLI (v106 additions)
- Added interop file helpers: `read_text`, `write_text`, `read_json`, `write_json` (host-access; trusted contexts).
- Added `pea test -k` filter alias.

### Language and Runtime (v107 additions)
- Added builtins/helpers: `get_path`, `deep_merge`, `take`, `drop`, `partition`, `count_by`, `first`, `last`.

### Data Analysis (v107 additions)
- Added `duplicated`, `nlargest`, `nsmallest`, `pivot_wider`.

### Web (v107 additions)
- Added `not_found`, `method_not_allowed`, `url_join`.

### Interop (v107 additions)
- Added path/fs helpers (host access; trusted contexts): `glob`, `exists`, `mkdir_p`, `tempdir`, `basename`, `dirname`.

### Language and Runtime (v108 additions)
- Added builtins/helpers: `is_empty`, `compact`, `defaults`, `invert`, `to_pairs`, `from_pairs`, `sum_by`, `avg`, `capitalize`, `snake_case`, `kebab_case`, `slugify`, `truncate`, `union`, `intersection`, `difference`.

### Data Analysis (v108 additions)
- Added: `explode`, `where`, `shape`, `isna`, `notna`, `astype` (alias), `to_records`, `to_dict`, `str_transform`/`str_lower`/`str_upper`/`str_strip`/`str_contains`/`str_replace`.

### Web (v108 additions)
- Added status/response helpers: `unauthorized` (401), `forbidden` (403), `conflict` (409), `too_many_requests` (429), `gone` (410), `unprocessable` (422), `download`, `status`.

### Interop and CLI (v108 additions)
- Added interop path/OS helpers (host access; trusted contexts): `join_path`, `extname`, `stem`, `is_file`, `is_dir`, `abspath`, `cwd`, `platform`.
- Added `pea check --json` / `pea lint --json` machine-readable output.
- Added `pea analyze <file.json|csv> [--json] [--head N]` data profiling command.

### Language and Runtime (v109 additions)
- Added builtins/helpers: `has_path`, `set_path` (immutable), `map_values`, `map_keys`, `pick_by`, `omit_by`, `shuffle`, `product`, `median`, `parse_int`, `parse_float`, `strip_prefix`, `strip_suffix`, `sha256`, `url_encode`, `url_decode`, `html_escape`, `title_case`, `center`.

### Data Analysis (v109 additions)
- Added: `shift`, `lag`, `lead`, `cummax`, `cummin`, `cumprod`, `replace_values`, `one_hot`, `split_column`, `percentile` (alias).

### Web (v109 additions)
- Added: `bad_request`, `server_error`, `not_modified`, `moved_permanently`, `see_other`, `temporary_redirect`, `permanent_redirect`, `security_headers`, `parse_query`, `build_query`.

### Interop and CLI (v109 additions)
- Added interop helpers (host access; trusted contexts; `remove_file` is destructive): `copy_file`, `remove_file`, `list_dir`, `stat`, `hash_file`.
- Added `pea web-openapi <file> [--title T] [--version V]` (extracts OpenAPI from a file defining `app`; suppresses `app.serve` during extraction).
- Added `pea hash <file> [--algo sha256]`.

### Language and Runtime (v110 additions)
- Added builtins/helpers: `min_by`, `max_by`, `without`, `xor`, `zip_object`, `ensure_list`, `ensure_dict`, `size`, `random_choice`, `sample_list`, `clone`, `deep_clone`, `deep_equal`, `nth`, `initial`, `rest`.

### Data Analysis (v110 additions)
- Added: `drop_columns`, `keep_columns`, `assign`, `round_col`, `abs_col`, `variance`, `std`, `covariance`, `idxmax`, `idxmin`.

### Web and UX (v110 additions)
- Added web helpers: `health`, `envelope`, `with_links`, `negotiate`, `request_logger` (middleware factory).
- Added `ux.quickstart()` and `ux.commands()`.

### Interop, CLI, and Templates (v110 additions)
- Added interop helpers (host access; trusted contexts): `walk`, `readlines`, `writelines`, `tempfile`.
- Added `pea openapi` alias for `web-openapi` and `pea quickstart`.
- Added project template: `api` (CORS, `/health`, envelope/items endpoints, 404 handler).

### Language and Runtime (v111 additions)
- Added builtins/helpers: `group_by` (list→dict of lists), `frequencies`, `scan`, `hex_encode`/`hex_decode`, `ensure_str`/`ensure_int`/`ensure_float`, `pipe`, `apply`.

### Data Analysis (v111 additions)
- Added aggregates: `mean_col`, `sum_col`, `min_col`, `max_col`, `median_col`.
- Added stats/series: `skew`, `kurtosis`, `expanding_mean`, `corr` (alias).
- Added I/O: `to_jsonl`, `from_jsonl`.

### Web (v111 additions)
- Added: `validation_error`, `content_type`, `merge_headers`, `query_int`, `query_bool`, `api_key_auth`, `method_is`.

### Interop, CLI, and Templates (v111 additions)
- Added interop helpers (host access; trusted contexts): `env_all`, `expanduser`, `expandvars`, `touch`, `head_file`, `tail_file`.
- Added CLI: `pea tree [path]`, `pea version --json`.
- Added project template: `etl` (JSON load/transform/profile starter).

### Documentation and Quality
- Updated `README.md`, `docs/USER_GUIDE.md`, `CHANGELOG.md`, and `docs/RELEASE_NOTES_1.0_EXPERIENCE.md`.
- Added/expanded tests for v102–v111 features (language, analysis, web, interop/UX, CLI/templates).
- Regression baseline: **686 passed, 1 skipped**.

## 0.99.6 - 2026-10-27
- Closed CodeQL high-severity findings in SFTP host verification, legacy HMAC trust storage, and type-system regular expressions.
- Removed automatic acceptance of unknown SSH host keys; SFTP now fails closed using known-host verification.
- Stopped copying HMAC secret material into the legacy trust-store JSON; Ed25519 remains the recommended public package-signing mechanism.
- Hardened type-system source matching with bounded inputs and non-ambiguous structural patterns to mitigate regular-expression denial of service.
- Added security regression tests and cumulative release documentation.
## 0.99.5 - 2026-10-26
- Fixed TypeScript/React Node 24 diagnostic failures and stale client dependency.
- Added Java and Node CI plus OS/Python and security workflows.


## 0.99.4 - 2026-10-26
- Replaced MD5 CycloneDX serial generation with UUIDv5.
- Added AST security regression tests and real scanner workflow.
- Added no new feature family.


## 0.99.3 - 2026-10-26
- Historical retention recovery, comparator v2, protected removals, ledgers, fixtures and examples.


## 0.99.2 - 2026-10-26
- Added machine-checkable pre-1.0 evidence inventory and fail-closed gate.
- Added evidence directories for tests, compatibility, security, packaging, install and approvals.
- Normalized active SDK/core release metadata to 0.99.2.
- Added no new feature family.

## 0.99.1 - 2026-10-26
- Closed the pre-1.0 repository audit without adding features.
- Classified all intentional abstract interface methods.
- Added component maturity and known-limitations documents.
- Normalized SDK metadata and cumulative changelog structure.
- Added automated audit-closure tests and fail-closed 1.0 guidance.

0.99.0-rc1 - 2026-10-26
- Added final blocker/waiver closure gate.
- Added final documentation-review gate.
- Added 1.0.0 artifact signature, provenance and SBOM gates.
- Added authoritative GO-1.0/NO-GO dossier contract.

## 0.98.0-rc1 - 2026-10-26
- Added signed staging release-rehearsal evidence gates.
- Added clean-install, upgrade and rollback integrity drills.
- Added support/incident/rollback operational rehearsal gates.
- Added consolidated rehearsal approval and NO-GO behavior for missing real evidence.

## 0.97.0-rc1 - 2026-10-26
- Added launch-candidate frozen-change, signed-artifact/provenance, operational-playbook and rollback gates.
- Added explicit release/security/operations approval requirements.

## 0.96.0-rc1 - 2026-10-26
- Added documentation/support and packaging/operations readiness gates.
- Added verified release-evidence consolidation and residual-risk closure.
- Added final 1.0 readiness dossier with three-owner approval requirement.

## 0.95.0-rc1 - 2026-10-26
- Added real release-evidence ingestion contracts.
- Added critical/high blocker burn-down and waiver validation.
- Added wheel/sdist/container signature and provenance verification gates.
- Added staging release dry-run and rollback acceptance.
- Added explicit 1.0 GO/NO-GO decision requiring human approvals.

## 0.94.0-rc1 - 2026-10-26
- Added Windows/Linux/macOS and Python 3.10-3.13 install/upgrade/rollback/offline-install matrix gates.
- Added wheel/sdist/container plus SBOM/provenance reproducibility gates.
- Added dependency/license/security review closure and operational-runbook gates.
- Added consolidated 1.0 evidence-readiness gate.

## 0.93.0-rc1 - 2026-10-26
- Added extended-duration repeated-run soak certification.
- Added broader ecosystem evidence certification.
- Added disaster-recovery/state-restoration integrity and RTO drills.
- Added repeated-build reproducibility checks and consolidated RC gate digest.


## 0.92.0-rc1 - 2026-10-25
- Added RC evidence freshness and staleness enforcement.
- Added upgrade/rollback/re-upgrade drills with integrity-digest comparison.
- Added repeated-build API/diagnostic/bytecode drift surveillance.
- Added security/performance/memory trend gates, ecosystem certification and recovery drills.
- Added waiver expiry/ownership controls and consolidated RC2 certification gate.

## 0.91.0-rc1 - 2026-10-25
- Added cross-platform Windows/Linux/macOS and Python 3.10-3.13 soak-evidence contracts.
- Added supported-version upgrade and rollback/integrity validation.
- Added frozen API/diagnostic/bytecode compatibility surveillance.
- Added security, performance, packaging and offline-install soak aggregation.
- Added blocker/waiver validation and a consolidated RC go/no-go gate.

## 0.90.0-rc1 - 2026-10-25
- Froze intended public syntax, runtime, package, diagnostic and versioned bytecode compatibility surfaces for 1.0.
- Added canonical API freeze manifests and SHA-256 API-contract digests.
- Added additive/breaking API classification and approval-required breaking-change gates.
- Added the machine-readable 1.0 compatibility contract, tests and release documentation.
- Corrected stale Containerfile version references for the 0.90 RC line.

## 0.89.0-rc1 - 2026-10-25
- Froze new feature families for release-candidate hardening.
- Added blocker/high-severity defect and waiver registry contracts.
- Added consolidated regression, API, security, performance, supply-chain, migration, tooling, documentation and cross-platform readiness gates.
- Added tamper-evident RC readiness report digest.
- Added tests, release notes, known-issues registry and retention evidence.

## 0.89.0-alpha.1 - 2026-10-25
- Froze new feature families for RC hardening.
- Added consolidated release evidence and GO/NO-GO decisions.
- Added blocker/high-severity defect closure and scoped waivers.
- Added RC readiness tests and documentation.

## 0.88.0-alpha.1 - 2026-10-25
- Added LSP and DAP compatibility certification contracts.
- Added stable diagnostic code/severity registry and snapshots.
- Added deterministic editor capability negotiation.
- Added reproducible breakpoint/stack/variable debugging fixtures.
- Added combined developer-tooling certification gates, tests and documentation.

## 0.87.0-alpha.1 - 2026-10-25
- Added agent tool isolation, approval replay protection, budgets and audit certification.

## 0.86.0-alpha.1 - 2026-10-25
- Added ML and serving conformance.

## 0.85.0-alpha.1 - 2026-10-25
- Added connector capability profiles and certification suites.
- Added SQL dialect, binding and transaction conformance contracts.
- Added streaming checkpoint, replay and deduplication semantics.
- Added object-store pagination, range-read and multipart-failure fixtures.
- Added certification gates, tests, release notes and retention evidence.

## 0.84.0-alpha.1 - 2026-10-25
- Added parent-child cancellation and deadline propagation.
- Added fail-fast structured task-group lifecycle guarantees.
- Added retry safety and idempotency-key payload validation.
- Added graceful shutdown, draining and resilience release gates.
- Added stress-oriented regression tests, release notes and retention evidence.

## 0.83.0-alpha.1 - 2026-10-25
- Added representative benchmark-suite execution with mean, p50, p95, p99, throughput and peak-memory evidence.
- Added prior-baseline performance regression budgets and automated gates.
- Added named compiler/runtime hot-path profiling.
- Added cache load/eviction metrics and memory-pressure probes.
- Added benchmark baseline serialization, tests, release notes and retention evidence.

## 0.82.0-alpha.1 - 2026-10-25
- Added deterministic source manifests and tamper verification.
- Added CycloneDX SBOM and SLSA/in-toto provenance verification.
- Added Ed25519 detached release-manifest signing and verification.
- Added dependency-lock and offline-install evidence plus packaging quality gates.
- Added tests, release notes, retention evidence and handover.

## 0.81.0-alpha.1 - 2026-10-25
- Added machine-readable deprecation lifecycle enforcement.
- Added deterministic, resumable and reversible migration execution.
- Added public API snapshots, diffs and breaking-change gates.
- Added upgrade fixtures, tests, release notes and retention evidence.

## 0.80.0-alpha.1 - 2026-10-25
- Added W3C trace-context propagation and parent/child spans.
- Added bounded span export and metric cardinality controls.
- Added liveness/readiness operational contracts.
- Added redacted diagnostic bundles with SHA-256 manifests.
- Added tests, release notes, operations guide, retention report and handover.


## 0.79.0a1 - Enterprise integration hardening
- Added chained credential providers and normalized integration profiles.
- Added shared timeout, rate-limit, authentication and availability error taxonomy.
- Added exponential retry/backoff with jitter and circuit-breaker recovery.
- Added correlation IDs and connector health reports.
- Retained v0.78 security controls and all previous connector implementations.

## 0.78.0a1 - Security hardening
- Added reusable trust-boundary validation for text, collection, path and URL inputs.
- Added private/loopback/link-local network blocking for host URL validation.
- Added recursive credential and bearer-token redaction.
- Added tamper-evident SHA-256/HMAC audit chains.
- Added v0.78 security regression tests while retaining the cumulative release history.


## 0.77.0 - 2026-10-25
- Added repeatable runtime performance and allocation-memory probes.
- Added mean/p95 latency and peak-memory budget gates.
- Added a dependency-free bounded LRU cache with eviction and hit-rate metrics.
- Retained the clean documentation layout and v0.76 release-hardening gates.

## 0.76.0 - 2026-10-25
- Added adversarial agent-policy probes and deterministic probe summaries.
- Added public API compatibility gating with explicit approved-removal handling.
- Added integrated test, security, API and file-retention release thresholds.
- Reorganized release notes, retention evidence and project metadata under `docs/` while retaining one root cumulative changelog and detailed README.

## 0.75.0 - 2026-10-25
- Added persistent SQLite agent audit trails, durable approval records, deterministic approval IDs, actor/reason capture, and audited tool-execution evidence.

## 0.73.0 - 2026-10-25
- Added optional ONNX Runtime inference, tensor/DataFrame and PyTorch interchange, and policy-governed natural-language query planning.

## 0.72.0 - 2026-10-25
- Merged interactive dashboard controls/bindings, browser REPL and dataset inspection, plus Jupyter kernel protocol and rich DataFrame rendering.

## 0.71.0 - 2026-10-24
- Combined three roadmap targets: dataset/column lineage, pipeline observability with SLA/alerts/audit, and a declarative dashboard DSL with React rendering.

## 0.70.0 - 2026-10-24
- Added durable SQLite orchestration state, retries with backoff/jitter, deterministic idempotency, interval scheduling, logical dates, run history, and backfill execution.

## 0.69.0 - 2026-10-24
- Added DAG/task definitions, dependency validation, cycle detection, deterministic topological ordering, execution layers, declarative graph loading, and local DAG execution.

## 0.68.0 - 2026-10-24
- Added RabbitMQ and WebSocket connectors, explicit RabbitMQ acknowledgement controls, QoS/prefetch, JSON messaging, and an in-memory message bus.

## 0.67.0 - 2026-10-24
- Added Kafka producer/consumer integration, consumer groups, manual commits, security options, batch publishing, and an in-memory test broker.

## 0.66.0 - 2026-10-24
- Added event-time streams, watermarks, late-event handling, tumbling/sliding windows, and persistent idempotent delivery semantics.

## 0.65.0 - 2026-10-24
- Added partitioning, bounded JSONL scans, predicate/projection pushdown, spill execution and checkpoints.


## 0.64.0a1 - 2026-10-24
- Added engine-neutral distributed compute plans and Local/Arrow/Polars/Spark adapters.
## 0.63.0rc2 - 2026-10-24
- RC2 stabilization: refreshed validation evidence, RC1 API compatibility checks and migration/operator guidance.
## 0.63.0rc1 - 2026-10-24
- Froze feature scope for RC1 and added API compatibility, deprecation policy, integration gates, threat model and migration guidance.
## 0.62.0 - 2026-10-24
- Added release-candidate packaging, SBOM/provenance, checksums, artifact verification, Containerfile, CI matrix and v1 readiness assessment.
## 0.61.0 - 2026-10-24
- Added secure Kubernetes YAML, security contexts, NetworkPolicy/PDB/topology controls, drain handling and RC stabilization checks.
## 0.60.0 - 2026-10-23
- Added distributed serving backends, load/performance gates, OpenTelemetry hooks and Kubernetes operations.
## 0.59.0 - 2026-10-23
- Added resilient serving with rate/concurrency limits, timeouts, logs/traces, secure loading, live reload and rollback.
## 0.57.0 - 2026-10-23
- Added portable pipelines, SQLite monitoring, policy/deployment manifests and MLOps CLI commands.
## 0.56.0 - 2026-10-23
- Added secure model bundles, monitoring stores, alerts, promotion gates, canary routing and rollback controls.
## 0.55.0 - 2026-10-23
- Added model bundles, inference/audit APIs, drift and fairness diagnostics, calibration, registry lifecycle and FastAPI serving.
## 0.54.0 - 2026-10-23
- Added production ML pipelines, cross-validation, tuning, regularization, multiclass classification and governance artifacts.
## 0.53.0 - 2026-10-23
- Added ML foundations: preprocessing, linear/logistic regression, evaluation, k-fold indices, persistence and pipelines.
## 0.52.0 - 2026-10-23
- Added forecasting baselines, evaluation metrics, seasonal decomposition, grouped forecasts, chart-ready series and optional acceleration benchmarks.
## 0.51.0 - 2026-10-23
- Added grouped and time-series analytics with resampling, shifts, changes, expanding/EWM windows and interpolation.
## 0.50.0 - 2026-10-23
- Added DataFrame analytics and statistics: summaries, quantiles, dispersion, correlation, frequencies, crosstabs, ranking, cumulative/rolling calculations, outliers and profiling.
## 0.49.0 - 2026-10-23
- Hardened connector runtime with token providers, profiles, health checks, certification matrices and Graph/SharePoint paging.
## 0.48.0 - 2026-10-23
- Added Microsoft Graph/SharePoint connector foundation, secret providers, capability metadata and connector certification.
## 0.47.0 - 2026-10-23
- Added S3, Azure Blob, ADLS Gen2 and GCS object storage connectors with common file and DataFrame operations.
## 0.46.0 - 2026-10-23
- Added OData and SFTP cloud connectors with pagination, query options, secure transfers and DataFrame ingestion.
## 0.45.0 - 2026-10-23
- Added Connector SDK with registry, transport abstraction, retries, auth helpers, REST and GraphQL connectors, pagination and DataFrame conversion.
## 0.44.0 - 2026-10-23
- Added SQL/database layer with SQLite, optional database adapters, discovery, parameterized queries, transactions, batching and SQLite upsert.
## 0.43.0 - 2026-10-23
- Added DataFrame Engine: joins, grouped aggregations, expressions, null handling, pivot/unpivot, window row numbers and expanded LazyFrame operations.
## 0.42.0 - 2026-10-23
- Added PeaLang Data foundation: schema model, DataFrame/LazyFrame, connector registry, CSV/JSON/JSONL and core transforms.
## 0.41.0 - 2026-10-23
- Added beta/pilot readiness model, candidate pilots, performance regression gate, security-review preparation and 1.0 migration-readiness report.
## 0.40.0 - 2026-10-23
- Added 500-case conformance corpus, differential runner, fuzz harness, security-boundary suite and multi-platform/Python CI definitions.
## 0.39.0 - 2026-10-23
- Added WebAssembly containers, browser ABI/policy, SDK and CLI.
## 0.38.0 - 2026-10-23
- Added native test/expect runner, filtering, coverage baseline, watch-mode portability baseline and migration CLI.
## 0.37.0 - 2026-10-23
- Added complete resource limit accounting and structured concurrency with cancellation propagation.
## 0.36.0 - 2026-10-23
- Added generic contracts/substitution/inference, protocols, project-wide contract analysis, and Result/Option/Future semantics foundation.
## 0.35.0 - 2026-10-23
- Stabilized the 14-module `std.*` standard library, capability gates, manifest, CLI inspection and compatibility tests.

### Language specification
- Added implementation-independent language specification, EBNF grammar, feature stability registry, compatibility/deprecation contract, spec CLI, and revised foundational roadmap.

### Registry metadata
- Added canonical registry indexes, sequence/replay protection, immutable version policy, package expiration, publisher namespaces, persistent registry state, and environment-based Bearer credentials.

### Package authenticity
- Added Ed25519 public-key package signatures, public trust store, revocation, HTTPS registry transport, verified install, offline cache, and lockfile hash enforcement.

### Package archives
- Added signed .peapkg support, trusted publisher keys, verification, safe extraction, HTTPS registry policy, installation receipts, and dependency-confusion defenses.

### Tooling and conformance
- Added VM profiling, line coverage, benchmark tooling, and observer hooks.
- Added interpreter-versus-VM differential conformance coverage.
- Added source inventory/hash comparison and strengthened release integrity gates.
- Added profile/benchmark CLI commands and hardening documentation.

## 0.29.0 - 2026-10-22
- Added TypeScript SDK, React hooks, browser-safe capabilities, and schema UI integration.
## 0.28.0 - 2026-10-22
- Added Java runtime sidecar and Java SDK.
## 0.27.0 - 2026-10-22
- Added package ecosystem foundation.
## 0.26.0 - 2026-10-22
- Added native async VM.
## 0.24.0 - 0.25.0
- Added semantic analysis and FastAPI integration.
## 0.18.0 - 0.23.0
- Added embedding, types, compiler/VM, capability safety, exceptions, imports, and VM DAP.
## 0.1.0 - 0.17.0
- Established the language and tooling foundations.


## 0.74.0-alpha.1 - 2026-10-25
- Added agent dry-run tool planning.
- Added deterministic tool allow/deny policy gates.
- Added host approval gates for sensitive agent actions.
- Added tool-call budget enforcement.
- Moved historical development handovers to `docs/handover/` for a cleaner project root.
- Added agent governance documentation and regression tests.
