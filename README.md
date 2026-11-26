# PeaLang

Readable automation, data, integration, orchestration, web, and AI workflow language.

PeaLang is an embeddable extension language designed for rules, workflows, integrations, data processing, web applications, automation, and controlled application customization.

PeaLang is designed to complement existing ecosystems such as Python, FastAPI, Java, TypeScript, React, databases, messaging systems, and enterprise applications rather than replace them.

## Release Status

**Version: 3.1.48** — current tagged release across package, SDK, runtime, and specification metadata.

`3.1.48` is the unified release identifier for the tagged v3.1.48 line. Source version, SDK packages, container image label, runtime health output, registry user agent, release manifest, and language specification now report the same version. Historical release notes are kept in `docs/releases/` for provenance, but they do not define the current version.

See `ROADMAP.md` for the forward-looking plan, `CHANGELOG.md` for per-feature history, and `docs/CROSS_SECTOR_ADOPTION_PLAN.md` for the plan to make PeaLang credible across enterprise, data, web, mobile, games, embedded, and cloud sectors.

### Design Principles

PeaLang is built incrementally around a small set of promises:

- **Simple**: readable syntax and a low-ceremony CLI.
- **Usable**: batteries-included stdlib for data, web, automation, and interop.
- **Scalable**: modules, packages, lockfiles, dependency graphs, and workspace-oriented tooling.
- **Robust**: optional static typing, compiler/VM checks, conformance tests, and reproducible packages.
- **Secure**: capability-controlled execution, resource limits, signed packages, and supply-chain checks.
- **Extendable**: embeddable runtime plus host bindings for Python, Java, TypeScript, React, Go, Rust, and WebAssembly.

## What's New in 1.0.0-experience

### Language Ergonomics
- List comprehensions: `[x * 2 for x in xs if x > 1]`
- Dict comprehensions with destructuring: `{k: v * v for [k,v] in items(d)}`
- Optional chaining: `user?.profile?.city`, `handler?.()`, `arr?.[0]`
- Null coalescing: `value ?? "fallback"`
- Anonymous functions: `function(x) { return x + 1 }`
- Pattern matching (statement + expression): `match x { 1 => "one", 2,3 => "few", _ => "other" }`
- Destructuring in `let` and `for`: `let [a,b]=pair`, `let {name}=user`, `for [k,v] in pairs { ... }`
- Membership operators: `x in list`, `"sub" in "string"`, `x not in list`
- Power operator: `**` (`2 ** 10`)
- Rich builtins/helpers: `enumerate`, `zip`, `sorted`, `reversed`, `map`, `filter`, `sum`, `any`, `all`, `min`, `max`, `abs`, `items`, `get`, `has`, `get_path`, `has_path`, `set_path`, `merge`, `deep_merge`, `push`, `pop`, `slice`, `take`, `drop`, `first`, `last`, `contains`, `trim`, `replace`, `starts_with`, `ends_with`, `strip_prefix`, `strip_suffix`, `json_parse`, `json_dump`, `safe`, `now_ms`, `chunk`, `flatten`, `uniq`, `compact`, `partition`, `count_by`, `pick`, `omit`, `pick_by`, `omit_by`, `defaults`, `invert`, `map_values`, `map_keys`, `to_pairs`, `from_pairs`, `clamp`, `uuid`, `randint`, `shuffle`, `b64encode`, `b64decode`, `sha256`, `url_encode`, `url_decode`, `html_escape`, `now_iso`, `coalesce`, `repeat`, `times`, `find`, `find_index`, `pluck`, `index_by`, `sort_by`, `sum_by`, `avg`, `median`, `product`, `parse_int`, `parse_float`, type predicates (`is_null/is_list/is_dict/is_string/is_number/is_bool`, `is_empty`), `identity`, `tap`, `pad_start`, `pad_end`, `center`, `lines`, `words`, `capitalize`, `title_case`, `snake_case`, `kebab_case`, `slugify`, `truncate`, `union`, `intersection`, `difference`, `without`, `xor`, `zip_object`, `min_by`, `max_by`, `nth`, `initial`, `rest`, `ensure_list`, `ensure_dict`, `size`, `random_choice`, `sample_list`, `clone`, `deep_clone`, `deep_equal`, `group_by` (list), `frequencies`, `scan`, `pipe`, `apply`, `hex_encode`, `hex_decode`, `ensure_str`, `ensure_int`, `ensure_float`, `gcd`, `lcm`, `sign`, `is_even`, `is_odd`, `lerp`, `between` (scalar), `rotate`, `interleave`, `windows`, `dedupe_by`, `assoc`, `dissoc`, `rename_keys`, `format_number`, `floor`, `ceil`, `log`, `exp`, `pow`

### Web Applications (`web` / `std.web`)
- App/routing: `web.app()`, `app.get/post/put/delete/patch/options()`
- Path params: `/users/:id` and OpenAPI `{id}` conversion
- Route groups: `app.group("/api")`
- Request helpers: query, params, headers, cookies, JSON/form body
- Response helpers: `web.json/html/text/redirect/error/file/sse/response`, templates, cookies
- Validation, rate limiting, and auth/helpers: `web.validate`, `web.rate_limit`, `web.bearer_auth`, `web.request_id`, `web.json_error`, `web.etag`, `web.cache_control`, `web.basic_auth`, `web.no_content`, `web.created`, `web.accepted`, `web.ok`, `web.problem`, `web.pagination`, `web.parse_basic_auth`, `web.not_found`, `web.method_not_allowed`, `web.url_join`, `web.unauthorized`, `web.forbidden`, `web.conflict`, `web.too_many_requests`, `web.gone`, `web.unprocessable`, `web.bad_request`, `web.server_error`, `web.not_modified`, `web.moved_permanently`/`see_other`/`temporary_redirect`/`permanent_redirect`, `web.download`, `web.status`, `web.security_headers`, `web.parse_query`, `web.build_query`, `web.health`, `web.envelope`, `web.with_links`, `web.negotiate`, `web.request_logger`, `web.validation_error`, `web.content_type`, `web.merge_headers`, `web.query_int`/`web.query_bool`, `web.api_key_auth`, `web.method_is`, `web.accepts`/`web.accepts_json`/`web.accepts_html`, `web.no_cache`, `web.vary`, `web.link_header`
- Static files, middleware, custom 404/error handlers
- CORS support with preflight handling (`app.enable_cors()`)
- OpenAPI 3.0 generation: `web.openapi(app, title, version)`

### Data Analysis (`analysis` / `std.analysis`)
- Profiling and stats: `profile`, `describe`, `summary`, `correlation`, `corr_matrix`, `quantile`, `outliers`
- Cleaning: `clean_missing`, `fillna`, `impute`, `drop_duplicates`, `rename`
- Transform: `select`, `sort_by`, `filter_rows`, `query`, `group_by`, `pivot`, `join/merge`, `concat`, `add_column`, `cumsum`, `normalize`
- Exploration: `head`, `tail`, `sample`, `unique`, `value_counts`, `top_values`, `columns`
- Aggregates, I/O and extras: `mean_col`/`sum_col`/`min_col`/`max_col`/`median_col`, `corr`, `skew`, `kurtosis`, `expanding_mean`, `from_csv`, `from_json`/`from_jsonl`, `to_json`/`to_jsonl`, `to_records`, `to_dict`, `between`, `clip`, `mode`, `nunique`, `count`, `melt`, `transpose`, `rank`, `pct_change`, `diff`, `shift`/`lag`/`lead`, `rolling_mean`, `cummax`/`cummin`/`cumprod`, `schema`, `shape`, `isna`, `notna`, `zscore`, `histogram`, `cut`, `ffill`, `bfill`, `dropna`, `replace_values`, `cast`/`astype`, `crosstab`, `one_hot`, `duplicated`, `nlargest`, `nsmallest`, `pivot_wider`, `explode`, `where`, `split_column`, `drop_columns`, `keep_columns`, `assign`, `round_col`, `abs_col`, `variance`, `std`, `covariance`, `idxmax`, `idxmin`, `rolling_std`, `expanding_sum`/`expanding_max`/`expanding_min`, `sample_frac`, `ewm_mean`, `standardize`, `str_transform`/`str_lower`/`str_upper`/`str_strip`/`str_contains`/`str_replace`, `percentile`
- Output: `to_csv`, `to_markdown`, `to_html`, `bar_chart`, `line_chart`, `summary`
- SQL over records: `analysis.sql`, `analysis.sql_value` (in-memory SQLite; `GROUP BY`, window functions, CTEs)
- File-based IO: `analysis.read_csv_file`, `analysis.write_csv_file`, `analysis.read_json_file`, `analysis.write_json_file`, `analysis.read_jsonl_file`, `analysis.write_jsonl_file`
- Pandas-class helpers: `qcut`, `rolling_sum`/`rolling_min`/`rolling_max`/`rolling_median`/`rolling_var`, `expanding_std`/`expanding_var`/`expanding_median`, `interpolate`, `factorize`, `mask`, `select_dtypes`, `info`, `memory_usage`, `pivot_table`, `reset_index`/`set_index`, `agg`, `transform`, `group_by_multi`, `merge_multi`, `describe_all`, `missing_summary`, `winsorize`, `corr_spearman`, `date_range`
- Reporting (v128): `profile_markdown`, `profile_html`, `report_markdown`, `report_html`, `model_markdown`, `model_html`, `evaluation_markdown`, `evaluation_html`, `write_report_markdown`, `write_report_html`, `write_report_json`
- Notebook display (v129): `display_records`, `display_profile`, `display_model`, `display_evaluation`, `display_chart`, `display_report`
- Document processing & OCR (v130): `read_document`, `read_csv`, `read_json`, `read_jsonl`, `read_xml`, `read_html`, `read_docx`, `read_xlsx`, `read_pdf`, `ocr_available`, `ocr_extract_text`, `ocr_extract_data`, `detect_format`, `strip_html`
- Data visualization (v131): `bar_chart_svg`, `line_chart_svg`, `scatter_plot_svg`, `histogram_svg`, `ascii_bar_chart`, `ascii_line_chart`, `chart_to_file`
- Data validation (v132): `build_schema`, `validate_record`, `validate_records`, `check_type`, `data_quality_report`, `missing_summary`, `duplicate_rows`, `infer_schema`
- Conformance & quality gates (v133): `run_conformance_suite`, `check_api_stability`, `check_doc_coverage`, `environment_check`, `generate_quality_report`, `hash_source_tree`
- Advanced ML (v134): `knn_fit`, `knn_predict`, `knn_score`, `naive_bayes_fit`, `naive_bayes_predict`, `naive_bayes_score`, `svm_fit`, `svm_predict`, `svm_score`
- SQL/DataFrame interop (v135): `sql_query`, `sql_value`, `dataframe_from_records`, `dataframe_select`, `dataframe_filter`, `dataframe_sort`, `dataframe_groupby`, `dataframe_head`, `dataframe_tail`, `dataframe_describe`, `window_function`
- Robustness (v136): `LRUCache`, `memoize`, `retry`, `retry_call`, `CircuitBreaker`, `batch_process`, `chunked`, `parallel_map`, `health_check`, `system_info`, `stream_records`, `lazy_filter`, `lazy_map`, `data_fingerprint`, `schema_fingerprint`
- Developer experience (v137): `suggest_fix`, `explain_error_detailed`, `project_scaffold`, `code_metrics`, `lint_source`, `format_source`, `dependency_check`
- Advanced time series (v138): `zscore_anomalies`, `iqr_anomalies`, `moving_average_anomalies`, `seasonal_decompose_simple`, `holt_winters_forecast`, `exponential_smoothing_forecast`, `detect_change_points`, `polynomial_features_2d`, `interaction_features`
- Clustering (v139): `dbscan`, `hierarchical_clustering`, `tsne`, `umap`, `variance_threshold`, `correlation_filter`, `mutual_info_scores`, `silhouette_score`
- LSP (v1.1.0): `LSPServer`, `build_lsp_namespace` — standards-compliant language server with diagnostics, hover, completion, symbols
- Formatter (v1.2.0): `PeaFormatter`, `format_source_ast`, `PeaLinter`, `lint_source_ast`, `codemod_remove_unused_imports`, `codemod_rename_variable`, `codemod_fix_naming`
- WASM runtime (v1.3.0): `capability_bridge_source`, `web_worker_runtime_source`, `capability_sandbox_policy`, `wasm_module_manifest` — browser capability bridges, Web Worker runtime, sandboxing
- React SDK (v1.4.0): `generate_react_hooks`, `generate_data_grid_adapter`, `generate_chart_adapter` — React hooks, data grid adapter, chart adapter
- Web SDK (v1.5.0): `generate_typescript_client`, `sse_endpoint_source`, `websocket_handler_source`, `jwt_middleware_source`, `rate_limiter_source`, `api_versioning_source` — full-stack web server and auto-typed SDK
- Arrow backend (v1.6.0): `available_backends`, `preferred_backend`, `backend_info`, `create_query_plan`, `PythonBackend`, `DuckDBBackend` — pluggable DataFrame backends with lazy query optimization
- Vector/RAG (v1.7.0): `create_vector`, `cosine_similarity`, `chunk_text`, `bm25_score`, `hybrid_search`, `VectorStore`, `model_to_onnx`, `tree_to_onnx` — ONNX export and vector/RAG primitives
- Notebook IDE (v1.8.0): `ReactiveCell`, `ReactiveNotebook`, `inspect_dataframe`, `inspect_sql_result`, `publish_as_webapp`, `generate_notebook_html` — reactive notebook and web IDE
- Host bindings (v1.9.0): `register_host_function`, `generate_python_export`, `generate_typescript_export`, `generate_java_export`, `scaffold_go_sdk`, `scaffold_node_sdk`, `import_openapi`, `generate_connector_package` — FFI and multi-language host bindings
- VM optimizer (v2.0.0): `OptimizationHints`, `constant_fold`, `loop_unroll_hint`, `encode_bytecode_v2`, `decode_bytecode_v2`, `inspect_bytecode_v2`, `benchmark_vm`, `PackageIndex` — optimizing VM, JIT, package hub

### Numerical and Statistical Computing (`stats` / `std.stats`)
- Descriptive: `mean`, `median`, `mode`, `quantile`, `percentile`, `iqr`, `variance`, `std`, `skew`, `kurtosis`, `covariance`, `pearson`/`correlation`, `spearman`, `kendall`, `entropy`, `gini`, `describe`
- Transforms: `zscore`, `minmax_scale`, `robust_scale`, `winsorize`, `cumsum`/`cumprod`/`cummax`/`cummin`, `diff`, `histogram`, `outliers_z`, `percentile_rank`
- Linear algebra: `dot`, `norm`, `distance`, `angle`, `add`/`sub`/`mul`/`div`/`scale`, `outer`, `transpose`, `identity`, `matmul`, `trace`, `solve`, `determinant`, `inverse`
- Distributions: `normal_pdf`/`normal_cdf`/`normal_ppf`/`normal_interval`, `uniform_*`, `exponential_*`, `binomial_*`, `poisson_*`, `t_pdf`/`t_cdf`/`t_ppf`, `f_cdf`/`f_ppf`, `chi2_cdf`/`chi2_ppf`
- Hypothesis tests: `t_test_1samp`, `t_test_ind`, `welch_t_test`, `t_test_paired`, `chi_square_test`, `anova_oneway`
- Inference: `confidence_interval_mean`, `confidence_interval_proportion`, `confidence_interval_diff_means`, `bootstrap_ci`, `cohens_d`, `hedges_g`, `eta_squared`, `power_t_test`, `sample_size_t_test`, `adjust_p_values`
- More tests: `z_test_1samp`, `proportion_test`, `z_test_proportions`, `fisher_exact`, `chi_square_goodness_of_fit`, `mann_whitney_u`, `wilcoxon_signed_rank`, `kruskal_wallis`, `friedman_test`, `sign_test`, `jarque_bera`, `permutation_test`
- Regression diagnostics: `ols`, `predict_ols`, `variance_inflation_factors`, `residual_diagnostics`
- Time series: `acf`, `pacf`, `ljung_box`, `difference_series`, `moving_average`, `simple_exponential_smoothing`, `holt_linear`, `holt_winters`, `seasonal_decompose`, `changepoint_cusum`, `adf_test`
- Record wrappers: `analysis.regression_report`, `analysis.time_series_report`
- Predictive modeling: `glm`, `logistic_regression`, `poisson_regression`, `predict_glm`, `ridge_regression`, `lasso_regression`, `elastic_net`
- Survival analysis: `kaplan_meier`, `log_rank_test`, `cox_proportional_hazards`, `concordance_index`
- Forecasting: `arima`, `auto_arima`
- Modeling wrappers: `analysis.glm_report`, `analysis.survival_report`, `analysis.arima_report`
- Causal inference: `propensity_scores`, `covariate_balance`, `ipw_ate`, `aipw_ate`, `propensity_match`, `difference_in_differences`, `instrumental_variables`, `regression_discontinuity`
- Causal wrappers: `analysis.causal_report`, `analysis.did_report`, `analysis.iv_report`, `analysis.rdd_report`
- Evaluation: `train_test_split`, `k_fold`, `stratified_k_fold`, `accuracy_score`, `balanced_accuracy`, `precision_recall_fscore`, `roc_curve`, `roc_auc`, `log_loss`, `brier_score`, `calibration_curve`
- Regression metrics: `mean_squared_error`, `root_mean_squared_error`, `mean_absolute_error`, `median_absolute_error`, `mean_absolute_percentage_error`, `r2_score`, `explained_variance_score`
- Feature preparation: `polynomial_features`, `label_encode`, `ordinal_encode`, `standardize_features`, `standardize_transform`, `minmax_features`, `minmax_transform`
- Evaluation wrappers: `analysis.train_test_split`, `analysis.evaluate_classification`, `analysis.evaluate_regression`, `analysis.add_polynomial_features`
- Trees and forests: `decision_tree`, `predict_tree`, `tree_feature_importance`, `random_forest`, `predict_forest`, `forest_feature_importance`
- Gradient boosting: `gradient_boosting`, `predict_boosting`, `boosting_feature_importance`
- Model selection: `cross_validate`, `grid_search`, `random_search`
- Model interpretation: `permutation_importance`, `partial_dependence`
- Class imbalance: `class_balance`, `smote`, `random_oversample`, `random_undersample`
- Feature pipelines: `fit_pipeline`, `transform_pipeline`
- Target encoding: `target_encode`, `target_apply`
- Date features: `is_date`, `date_parts`, `calendar_features`, `analysis.date_features`
- Tree wrappers: `analysis.tree_report`, `analysis.forest_report`, `analysis.boosting_report`
- Tuning wrappers: `analysis.tune_model`, `analysis.random_tune`
- Interpretation wrapper: `analysis.interpret_report`
- Imbalance wrapper: `analysis.balance_classes`
- Pipeline wrappers: `analysis.model_pipeline`, `analysis.predict_pipeline`
- Model persistence: `save_model`, `load_model`, `export_model`, `import_model`, `model_summary`
- Modelling: `linear_regression`, `multiple_regression`, `polyfit`, `polyval`, `r_squared`, `interpolate`, `linspace`, `arange`, `kmeans`, `pca`, `confusion_matrix`
- Sampling: `random_uniform`, `random_normal`, `random_binomial`, `random_poisson`, `bootstrap`
- Pure Python, dependency-free: no NumPy, SciPy, pandas, or gonum required

### Cross-Language Interop (`interop` / `std.interop`)
- Python: `call_python`, `import_python`
- Native: `load_library`, `call_native` (ctypes-based)
- Process: `run`, `pipe_json`, `which`
- HTTP: `http_get`, `http_post`, `json_rpc`
- Environment/util/files: `env`, `pipe_json`, `read_text`/`write_text`, `read_json`/`write_json`, `copy_file`, `remove_file` (destructive), `list_dir`, `stat`, `hash_file`, `walk`, `readlines`, `writelines`, `tempfile`, `touch`, `head_file`, `tail_file`, `env_all`, `expanduser`, `expandvars`, `glob`, `exists`, `mkdir_p`, `tempdir`, `basename`, `dirname`, `join_path`, `extname`, `stem`, `is_file`, `is_dir`, `abspath`, `cwd`, `platform`, `cpu_count`, `hostname`, `user`, `pid` (host access; trusted contexts)
- Go: `go_run` (compile/run Go source), `go_available`, `go_version`, `generate_go` (Go client)
- Code generation: `generate_typescript`, `generate_java`, `generate_python_stub`, `generate_go`

### Developer Experience (`ux` / `std.ux`, CLI)
- `ux.doctor()`, `ux.explain()`, `ux.suggest()`
- CLI: `pea run`, `eval -e/-f`, `repl`, `check/lint [--json]`, `fmt`, `test`, `compile`, `vm`, `dis`, `analyze [--json]`, `web-openapi`/`openapi`, `hash`, `tree`, `env <NAME>|--keys`, `version [--json]`, `quickstart`, `init/new --template`, `serve-web`, `doctor`, `templates`, `info`, `project`, `serve`, `stdlib`, `typecheck`
- Project templates: `default`, `webapp`, `api`, `analysis`, `etl`, `automation`, `library`, `interop`

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

## Modern Language Ergonomics

```pea
# Comprehensions
let xs = [1,2,3,4]
let doubled = [x * 2 for x in xs if x > 1]          # [4, 6, 8]
let pairs = [[1,10],[2,20]]
let values = [v for [k,v] in pairs]                 # [10, 20]
let sq = {k: v*v for [k,v] in items({"a":2,"b":3})}

# Optional chaining and null coalescing
let city = user?.profile?.city ?? "unknown"
let result = handler?.()

# Anonymous functions and functional builtins
let mapped = list(map(function(x){ return x*10 }, [1,2,3]))
let evens = list(filter(function(x){ return x % 2 == 0 }, xs))
print sorted(xs)
print 2 in xs
print "ell" in "hello"

# Pattern matching
let label = match status {
  200, 201 => "ok"
  404 => "not found"
  _ => "error"
}

# Destructuring
let [a, b] = [10, 20]
let {name, score} = {"name":"Ada", "score": 91}
for {name} in users { print name }
for [k,v] in items(data) { print k }
```

## Web Applications

```pea
let app = web.app()
app.enable_cors("*")

function home(req) {
  return web.json({"message": "Hello", "query": req["query"]})
}
function get_user(req) {
  return web.json({"id": req["params"]["id"]})
}

app.get("/", home)
app.get("/users/:id", get_user)

let api = app.group("/api")
api.get("/ping", function(req){ return web.json({"ok": true}) })

let spec = web.openapi(app, "My API", "1.0.0")
# app.serve("127.0.0.1", 8080)
```

## Data Analysis

```pea
let data = [{"name":"Ada","score":91,"team":"a"},{"name":"Linus","score":84,"team":"a"}]
print analysis.summary(data)
print analysis.describe(data, "score")
let top = analysis.query(data, "score", ">", 85)
let grouped = analysis.group_by(data, "team", "score", "mean")
let filled = analysis.fillna(data, 0, "score")
print analysis.to_csv(top)
print analysis.bar_chart(data, "name", "score")
```

### Statistics and numerical computing

`stats` provides the NumPy/SciPy/gonum-class layer in pure PeaLang.

```pea
let values = [72, 84, 91, 88, 79, 95]
print stats.describe(values)
print stats.pearson([1, 2, 3], [2, 4, 6])

let fit = stats.linear_regression([1, 2, 3, 4], [2.1, 3.9, 6.2, 7.8])
print fit["slope"]
print fit["r_squared"]

let test = stats.t_test_ind(values, [65, 70, 72, 68, 75, 71])
print test["p_value"]

let segments = stats.kmeans([{"spend": 10}, {"spend": 12}, {"spend": 80}], 2, 100, 42)
print segments["labels"]

// inference, regression diagnostics and forecasting
let ci = stats.confidence_interval_mean(values)
print ci["low"]
print ci["high"]
print stats.cohens_d(values, [65, 70, 72, 68, 75, 71])
print stats.adjust_p_values([0.01, 0.04, 0.03], "bh")

let model = analysis.regression_report([
    {"a": 1, "b": 0, "y": 2},
    {"a": 0, "b": 1, "y": 3},
    {"a": 1, "b": 1, "y": 5}
], "y")
print model["table"]
print stats.predict_ols(model, [[1, 1]])

let forecast = stats.holt_winters([10, 20, 30, 11, 21, 31, 12, 22, 32], 3, 0.3, 0.1, 0.3, 2)
print forecast["forecast"]

// predictive modeling, survival analysis and ARIMA
let logit = stats.logistic_regression([[1], [2], [3], [4], [5], [6], [7], [8]], [0, 1, 0, 1, 1, 0, 1, 1], ["x"])
print logit["table"]
print stats.predict_glm(logit, [[5]])["predicted"]

let ridge = stats.ridge_regression([[1, 0], [0, 1], [1, 1]], [2, 3, 5], 0.5, ["a", "b"])
print ridge["coefficients"]

let km = stats.kaplan_meier([1, 2, 3, 4], [1, 1, 0, 1])
print km["median_survival"]

let arima = stats.arima([10, 20, 30, 11, 21, 31, 12, 22, 32], 1, 1, 0, 2)
print arima["forecast"]

// causal inference
let treatment = [0, 1, 0, 1, 0, 1, 0, 1]
let outcome = [1, 2, 3, 4, 5, 6, 7, 8]
let ps = stats.propensity_scores([[1], [2], [3], [4], [5], [6], [7], [8]], treatment, ["x"])
print ps["overlap"]
let ipw = stats.ipw_ate([[1], [2], [3], [4], [5], [6], [7], [8]], treatment, outcome, 0.0, 0.95, 50, 1)
print ipw["ate"]

let did = stats.difference_in_differences([1, 2, 3, 4, 2, 3, 6, 7], [0, 0, 0, 0, 1, 1, 1, 1], [0, 0, 1, 1, 0, 0, 1, 1])
print did["att"]

// model evaluation and feature preparation
let split = stats.train_test_split([[1], [2], [3], [4], [5], [6], [7], [8]], [0, 0, 1, 1, 0, 1, 1, 1], 0.25, true, 7)
print split["n_train"]
print stats.accuracy_score([0, 0, 1, 1], [0, 1, 1, 1])
print stats.roc_auc([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8])
print stats.r2_score([1, 2, 3], [1, 2, 3])
print stats.polynomial_features([[2, 3]], 2)["names"]

// decision trees and random forests
let tree = stats.decision_tree([[0], [1], [2], [3], [4], [5]], [0, 0, 0, 1, 1, 1], "classification", 3)
print stats.predict_tree(tree, [[0], [5]])["predicted"]
let forest = stats.random_forest([[0], [1], [2], [3], [4], [5]], [0, 0, 0, 1, 1, 1], "classification", 25, 4, 2, 1, "sqrt", true, 7)
print forest["oob_score"]
print stats.forest_feature_importance(forest, ["x"])[0]["importance"]

// gradient boosting
let boosted = stats.gradient_boosting([[0], [1], [2], [3], [4], [5]], [0, 0, 0, 1, 1, 1], "classification", 40, 0.1, 3)
print stats.predict_boosting(boosted, [[0], [5]])["predicted"]
print stats.boosting_feature_importance(boosted, ["x"])[0]["importance"]

// cross-validation and hyperparameter search
let tuned = stats.grid_search("boosting", [[0], [1], [2], [3], [4], [5]], [0, 0, 0, 1, 1, 1], "classification", {"n_estimators": [10, 20], "max_depth": [2, 3]}, 3, 1, "accuracy")
print tuned["best_params"]
print tuned["best_score"]

// permutation importance and partial dependence
let explained = stats.permutation_importance(boosted, [[0], [1], [2], [3], [4], [5]], [0, 0, 0, 1, 1, 1], "classification", 3, 0, "accuracy", ["x"])
print explained["importances"][0]["feature"]
let curve = stats.partial_dependence(boosted, [[0], [1], [2], [3], [4], [5]], ["x"], 3, "classification", ["x"])["curves"][0]
print curve["average"]

// class imbalance
print stats.class_balance([0, 0, 0, 0, 1])["imbalance_ratio"]
let balanced = stats.smote([[0], [1], [2], [3], [4], [5]], [0, 0, 0, 0, 0, 1], 2, 0)
print balanced["n"]
print balanced["added"]

// feature pipelines: impute, encode, scale
let steps = [{"op": "impute", "method": "auto"}, {"op": "encode", "method": "onehot"}, {"op": "scale", "method": "standard"}]
let fitted = stats.fit_pipeline(steps, [["red", 1.0], [null, 2.0], ["blue", 3.0]], ["color", "x"])
print fitted["names"]
print fitted["features"]

// target encoding: compress high-cardinality categories
let encoder = stats.target_encode(["a", "a", "b", "b"], [1.0, 3.0, 10.0, 14.0], 10.0, 1)
print stats.target_apply(encoder, ["a", "b", "unseen"])

// model persistence: save, reload and score
stats.save_model("model.json", fitted)
let loaded = stats.load_model("model.json")
print stats.model_summary(loaded)["steps"]

// date features: calendar parts from strings
let matrix = stats.calendar_features(["2024-01-05", "2024-02-10"], ["year", "month", "weekday"])
print matrix["names"]
print matrix["features"]
```

See [`docs/DATA_SCIENCE.md`](docs/DATA_SCIENCE.md),
[`docs/STATISTICAL_INFERENCE.md`](docs/STATISTICAL_INFERENCE.md),
[`docs/ADVANCED_MODELING.md`](docs/ADVANCED_MODELING.md),
[`docs/CAUSAL_INFERENCE.md`](docs/CAUSAL_INFERENCE.md),
[`docs/MODEL_EVALUATION.md`](docs/MODEL_EVALUATION.md),
[`docs/TREE_MODELS.md`](docs/TREE_MODELS.md),
[`docs/GRADIENT_BOOSTING.md`](docs/GRADIENT_BOOSTING.md),
[`docs/MODEL_SELECTION.md`](docs/MODEL_SELECTION.md),
[`docs/MODEL_INTERPRETATION.md`](docs/MODEL_INTERPRETATION.md),
[`docs/CLASS_IMBALANCE.md`](docs/CLASS_IMBALANCE.md),
[`docs/FEATURE_PIPELINES.md`](docs/FEATURE_PIPELINES.md),
[`docs/TARGET_ENCODING.md`](docs/TARGET_ENCODING.md),
[`docs/MODEL_PERSISTENCE.md`](docs/MODEL_PERSISTENCE.md), and
[`docs/DATE_FEATURES.md`](docs/DATE_FEATURES.md) for the full reference.

## Cross-Language Interop

```pea
# Python
let root = interop.call_python("math", "sqrt", 81)

# Process
let out = interop.run("python", ["--version"])
let piped = interop.pipe_json(["python", "-c", "import json,sys; print(json.dumps({'ok':True}))"])

# HTTP / JSON-RPC
let resp = interop.http_get("https://api.example.com/data")
let rpc = interop.json_rpc("https://example.com/rpc", "add", [1,2])

# Code generation
let ts = interop.generate_typescript("http://127.0.0.1:8787")
```

## Developer Experience and CLI

```bash
pea run app.pea
pea eval -e "print [x*x for x in [1,2,3]]"
pea check src/
pea lint src/
pea fmt src/
pea test tests/
pea doctor
pea templates
pea init myapp --template webapp
pea info
pea compile app.pea
pea vm app.pea
pea repl
```

Namespaces: `web`/`std.web`, `analysis`/`std.analysis`, `stats`/`std.stats`, `interop`/`std.interop`, `ux`/`std.ux`.

## Library Lifecycle

PeaLang ships a complete library workflow — from scaffolding a project to publishing it to a registry and managing it as a dependency. All commands operate on a project's `pea.toml` manifest and `pea.lock` lockfile.

### Scaffolding and building

```bash
pea lib new mylib --template library     # scaffold a new library project
pea lib build mylib [-o out.pelib]       # build a .pelib package
pea build mylib --library                # equivalent build via the general command
pea lib quality mylib                    # run quality gates on a library
```

### Publishing and installing

```bash
pea publish mylib [--registry URL] [--token TOKEN]        # publish to a registry
pea publish mylib --dry-run                                # build + verify without uploading
pea lib publish mylib --dry-run                            # same, via the lib subcommand
pea publish mylib --sign --private-key key [--publisher ID] # build, sign, and publish
pea publish mylib --namespace acme [--private] [--allow bob] # publish into a namespace, optionally privately
pea lib inspect mylib-0.1.0.pelib [--json]                 # inspect a built package without installing
pea install mylib [@version]                               # install from default registry
pea install mylib @1.0.0 --verify --public-key key.pub     # verify signature before installing
pea info mylib [--token TOKEN]                             # show registry package info
pea search mylib [--token TOKEN]                           # search registry packages
```

### Signing and trusted keys

```bash
pea registry keys generate publisher.key [--public-key publisher.key.pub]
pea registry keys trust publisher.key.pub [--label NAME] [--trust-store PATH]
pea registry keys configure REGISTRY_URL KEY_ID... [--name NAME] [--trust-store PATH]
pea registry keys rotate OLD_KEY_ID NEW_KEY.pub [--trust-store PATH]
pea registry keys revoke KEY_ID [--reason REASON] [--trust-store PATH]
pea registry keys list [--trust-store PATH]
```

The default trust store is `~/.pealang/trust.json`. Registry servers can load a
shared trust store with `pea registry serve --trust-store PATH` so publisher keys are
verified at upload time.

### Registry namespaces and private packages

```bash
pea registry register-publisher <token> <publisher-id> [--storage DIR]
pea registry namespace create <namespace> <principal> [--storage DIR]
pea registry namespace list [--storage DIR]
pea publish mylib --registry URL --token TOKEN --namespace acme --private --allow bob
```

A publisher may use its own namespace or one explicitly authorized with
`pea registry namespace create`. Private packages are hidden from `pea info`,
`pea search`, the registry index, and downloads unless the caller supplies a token
for an allowed principal. Public packages keep their existing behavior.

### Reproducible libraries

```bash
pea lib reproducible mylib [--runs 2]                      # verify byte-identical rebuilds
pea lib provenance mylib-0.1.0.pelib [--json]               # verify embedded build evidence
```

Built `.pelib` files embed `provenance.json` with sorted tar entries, zeroed
timestamps/ownership, source/bytecode/manifest/exports checksums, lockfile hash,
dependencies, and the PeaLang builder version.

### Dependency management

```bash
pea lock                                 # generate pea.lock from pea.toml
pea lock --check                         # detailed drift report (CI-friendly exit code)
pea lock --update                        # deterministically refresh pea.lock from pea.toml
pea lock --update --registry-resolve     # resolve registry semver ranges to concrete versions
pea registry resolve mylib ^1.0 --json  # inspect available versions and select a match
pea deps                                 # list project dependencies
pea deps --tree                          # show the nested dependency tree (warns on cycles/conflicts)
pea deps --tree --json                   # machine-readable graph safety report
pea deps --security [path] [--advisories FILE] [--policy FILE]  # advisory + license scan
pea install                              # install all dependencies from pea.lock
pea update [path]                        # refresh installed libraries from pea.lock
pea outdated [path]                      # report missing/outdated/up-to-date libraries
pea uninstall <name> [path]              # remove a single installed library
pea clean [path] [--all]                 # remove .pea_modules (and optionally pea.lock)
```

`pea deps --security` checks `pea.lock` against local advisory and license policy
files. Advisories are JSON objects with `id`, `package`, `affected`, `severity`,
`summary`, and optional `fixed_version`. Policies support `max_severity`,
`allow_licenses`, `deny_licenses`, `require_license`, and `ignore_advisories`.
Defaults are loaded from `.pealang/advisories.json` and
`.pealang/security-policy.json`, then from `~/.pealang/`. The command exits with
status 1 when a blocking advisory or license violation is found.

### Workspaces

```bash
pea workspace init [path] [--name NAME]                     # create pea.workspace.toml
pea workspace add <workspace-path> <member-path>             # add a member project
pea workspace list [path] [--json]                           # list members and manifests
pea workspace graph [path]                                   # check local links and cycles
pea workspace lock [path] [--registry-resolve] [--offline]   # refresh all member locks
```

Workspace manifests are TOML files named `pea.workspace.toml`:

```toml
[workspace]
name = "platform"
members = [
  "libs/core",
  "apps/api",
]
```

Path dependencies that point at another member, and `workspace = true` dependencies,
become local workspace links. `pea workspace graph` detects cycles and duplicate
member names; `pea workspace lock` writes each member's `pea.lock` plus a deterministic
`pea.workspace.lock` with the build order and manifest/lock checksums.

### Offline cache and air-gapped installs

```bash
pea cache put mylib-1.0.0.pelib [--signature mylib-1.0.0.sig] [--name mylib] [--version 1.0.0]
pea cache get mylib [@version] [--registry URL]
pea cache list [--cache-dir DIR]
pea cache remove mylib 1.0.0
pea cache export packages.tar.gz [--cache-dir DIR]
pea cache import packages.tar.gz [--cache-dir DIR]
pea install mylib @1.0.0 --verify --offline --public-key key.pub [--cache-dir DIR]
```

The cache is content-addressed under `~/.pealang/package_cache` by default and stores
each package beside its detached signature. `export`/`import` produce a portable,
deterministic gzip bundle for air-gapped machines. Offline verified installs reuse
the cached package and signature, recheck the SHA-256, and still require Ed25519
verification through `--public-key`, `--key-id`, or the configured trust store.

### Trusted plugins and capability policy

```bash
pea plugin init myplugin plugins/myplugin.py --capability language-function --function greet
pea plugin init myplugin plugins/myplugin.py --signature plugins/myplugin.py.sig --key-id KEY_ID --trusted-key KEY_ID --require-signature
pea plugin list [--root DIR] [--policy FILE] [--trust-store PATH]
pea plugin verify .pealang/plugins/myplugin.json [--root DIR] [--policy FILE]
pea plugin load .pealang/plugins/myplugin.json [--root DIR] [--policy FILE] [--trust-store PATH]
```

Plugin manifests live in `.pealang/plugins/*.json` and record the plugin module,
version, declared symbols, SHA-256, and optional detached Ed25519 signature. The
policy at `.pealang/plugin-policy.json` allow-lists capabilities and signing keys;
unknown capabilities, checksum changes, untrusted keys, revoked keys, and invalid
signatures stop loading before any plugin code is imported. `pea plugin load` registers
only the declared functions, types, operators, and namespaces with the extension
registry.

### Structured errors and typed catch

```pea
try {
    throw error("TypeError", "bad value", "E_TYPE", error("ValueError", "root"))
} catch TypeError e {
    print e["kind"]        # TypeError
    print e["code"]        # E_TYPE
    print e["cause"]["code"]  # ValueError
}
```

`error(kind, message, code, cause)` creates a structured error value. `throw`
preserves that value, and `catch` bindings expose `schema`, `kind`, `message`,
`code`, `cause`, `context`, `source`, `line`, `column`, `end_line`, `end_col`,
`frames`, and `trace`. Typed catches such as `catch TypeError as e` work the
same in the interpreter and bytecode VM, and builtin failures such as division
by zero, bad indexes, missing keys, and type errors are converted into typed
structured errors. Plain thrown values still stringify to their message for
backward compatibility.

### Generics v2

```pea
protocol Printable { function to_string() -> String }

function show<T: Printable>(value: T) -> String {
    return "printable"
}

function first<T>(items: List<T>) -> T? {
    return null
}
```

Static analysis now keeps generic contracts, scopes type parameters such as `T`,
infers type arguments from literals and typed variables at call sites, and
reports `G201`–`G204` diagnostics for arity, inference, bound, and argument
mismatches. Generic-aware compatibility checks nested arguments such as
`List<Int>` versus `List<String>` without changing legacy broad compatibility.
Runtime annotations are still erased, so these functions execute as before;
`analyze_project()` also exposes collected generic contracts.

### Protocols and traits

```pea
protocol Printable { function to_string() -> String }

trait Serializable

function show<T: Printable>(value: T) -> String {
    return "printable"
}
```

Protocols now perform structural signature checks on record fields encoded as
`Function<P1,...,Pn,R>`, with `P201`–`P205` diagnostics for missing members,
non-function fields, wrong arity, parameter mismatches, and return mismatches.
A bare `Function` field remains a wildcard for backward compatibility. Traits
are marker contracts, and conformance checks are scoped to protocols or traits
referenced by generic bounds so unrelated records are not reported. All protocol
and trait declarations are erased before runtime and are exposed through
`SemanticResult` and `analyze_project()`. Protocol diagnostics are available via
`pea semantic` and `pea typecheck-project`.

### Iterators

```pea
let it = iter([1, 2])
print next(it)          # 1
print has_next(it)      # true
for x in it { print x } # 2
```

`iter()` returns a lazy `PeaIterator` with non-consuming `peek()` and
`has_next()` checks. `next()` returns a value or an optional default when the
iterator is exhausted. The same iterator helpers work in the interpreter,
bytecode VM, and async VM; loops close iterators deterministically, including
on `break`. Static analysis accepts `Iterable<T>` and `Iterator<T>` annotations,
infers element types from `iter()` and `next()`, and reports `I201` for values
known not to be iterable. Existing eager helpers such as `range`, `enumerate`,
`zip`, `map`, and `filter` are unchanged.

### Structured async concurrency

```pea
async function load_all() {
    let jobs = [api.fetch("a"), api.fetch("b")]
    return await concurrency.gather(jobs)
}

async function with_deadline() {
    return await concurrency.timeout(1.5, api.fetch("slow"))
}
```

The async VM now exposes a `concurrency` namespace with `sleep`, `spawn`,
`gather`, `timeout`, `result`, and `cancel`. Spawned tasks inherit a structured
cancellation scope, and a VM `CancellationToken` cancels that whole scope.
Static analysis represents `async function` results as `Future<T>`, infers the
value type of `await`, and reports `A201` when a known non-future is awaited.
Async annotations are erased before runtime parsing, so existing programs are
unchanged.

### Module resolution

```pea
import "api.client" as client
print client.value
```

Imports now share one resolver across the interpreter, bytecode VM, and async
VM. Dotted specifiers resolve to `modules/api/client.pea` or
`modules/api/client/__init__.pea`, and project manifests supply dependency
paths. Aliased imports are cached and circular imports are reported clearly.
Project analysis exposes the module graph and reports `M201` for unresolved
imports and `M203` for cycles.

### Safe metaprogramming

```pea
print double 3
```

Macro expansion is explicit and bounded. `SafeMacro` patterns use named
metavariables such as `$value`, and templates may use hygiene markers such as
`@tmp` to introduce fresh identifiers. Definitions are validated before use,
expansion work is limited, and issues are reported as `MG101`-`MG203`. Use
`expand_source_macros()` for source transformation or
`compile_source_with_macros()` to expand and compile in one step. Legacy string
macros remain available, and the default compile pipeline is unchanged.

### Resource scopes

```pea
using conn = open_connection() {
    print conn.query("select 1")
}
```

The `using` statement binds a resource for the block only. Values exposing
`close()` or `dispose()` are cleaned up when the block exits, including exits
caused by errors, and nested scopes unwind in LIFO order. Hosts can use
`ResourceScope` and `ResourceScopeManager` directly for bounded child budgets,
deferred cleanup, and scope snapshots. The `scopes` namespace exposes
`current()`, `snapshot()`, and `dispose()` to programs, and project analysis
reports `R201`/`R202` for duplicate or reassigned scope bindings.

### Conformance suite

```bash
pea conformance-v2
```

The v2 conformance suite runs a curated set of language-core cases across the
interpreter and bytecode VM, plus macro expansion, static diagnostic, and
module-graph cases. Each result records the runtime output or diagnostic codes
observed, and `conformance_gate_v2()` reduces the report to a stable PASS/FAIL
gate for CI. The original `pea conformance` differential and fuzz harness is
unchanged.

### Frozen 3.0 core

```bash
pea freeze
```

Phase 70 closes Wave 1 with a stable core-freeze gate. It combines the v2
conformance report, public API removal checks, specification verification, and
an explicit `CORE_SURFACES` manifest. `verify_core_freeze()` returns the same
PASS/FAIL report to hosts, and `core_freeze_report()` includes the manifest
digest for release evidence. Additions remain compatible; unexpected public API
removals fail the gate.

### Bytecode optimizer

```bash
pea optimize app.pea --verify
```

Phase 71 opens Wave 2 with a conservative peephole optimizer for portable
`.peac` bytecode. It folds literal arithmetic and comparisons, removes dead
literal pushes, and removes unreachable blocks while remapping every jump,
handler, and iterator target. Optimization operates on a deep copy, so the
original module stays available for comparison. `optimize_report()` returns
pass counts, a deterministic digest, and a PASS/FAIL gate; `--verify` runs both
modules on the VM and compares output and result before reporting success.

### Fast interpreter

```bash
pea fast app.pea --verify --benchmark
```

Phase 72 adds a direct-handler interpreter that pre-binds each supported
bytecode instruction to a closure and runs it with an explicit program counter.
Calls, imports, exception handlers, iterators, and object access automatically
fall back to the standard VM, so program meaning never changes.
`verify_fast_parity()` compares output and results from both executors, and
`--optimize` runs the Phase 71 optimizer before execution.

### Bytecode JIT

```bash
pea jit app.pea --verify --benchmark
```

Phase 73 adds a profile-guided trace JIT on top of the fast interpreter. A
profiling pass counts instructions, hot loop back-edges become bounded traces,
and integer arithmetic is specialized behind type guards. A guard failure
deoptimizes to the standard handler, so program meaning never changes.
`verify_jit_parity()` requires identical VM and JIT output and results;
`--optimize` runs the Phase 71 optimizer first, and `--threshold` tunes the hot
loop cutoff.

### Native backend

```bash
pea native app.pea --verify --benchmark --emit app.c
```

Phase 74 lowers the supported bytecode subset to deterministic native IR and
emits a self-contained C source artifact for host compilation. Modules outside
that subset stay on the standard VM, so adding the backend never changes program
meaning. `verify_native_parity()` requires identical VM and native output and
results; `--optimize` runs the Phase 71 optimizer first.

### WASM backend

```bash
pea wasm-backend app.pea --verify --benchmark --emit app.wasm --wat app.wat
```

Phase 75 lowers the supported bytecode subset to typed WASM IR wrapped in a
custom-section WebAssembly module. `--emit` writes the `.wasm` artifact and
`--wat` writes a reviewable text form; `inspect_wasm_backend()` reads the
manifest and IR back from a saved artifact. Unsupported modules stay on the
standard VM, and `verify_wasm_backend_parity()` requires identical VM and
backend output and results.

### Parallel runtime and profiling

```bash
pea parallel app.pea --verify --tasks 4 --workers 2
pea profiler app.pea --verify --emit profile.json
pea perf-gate app.pea --iterations 5
```

Phase 76 runs isolated bytecode tasks in a bounded worker pool while preserving
task order for output and results; async or module-importing tasks fall back to
the standard VM. Phase 77 records deterministic opcode, function, and line
counters with `profile_module()` and `RuntimeProfiler`. Phase 78 combines timing
budgets with parity, conformance, and frozen-core evidence in a versioned 4.0
gate. All three surfaces are additive and keep the frozen 3.0 contract intact.

### Language server v2

```bash
pea lsp --capabilities
pea lsp app.pea --check --symbols --emit lsp.json
```

Phase 81 adds a deterministic LSP v2 layer alongside the v1 server. It exposes
versioned capabilities, full and incremental document synchronization, and
inspectable diagnostics, symbols, hover, completion, references, rename,
formatting, folding, inlay hints, and semantic tokens. `lsp_v2_report()` produces
a stable capability/document digest, and `lsp_v2_gate()` reduces it to a
PASS/FAIL decision for editor tooling checks.

### Debug adapter v2

```bash
pea dap-v2 --capabilities
pea dap-v2 app.pea --breakpoint 3 --check --emit dap.json
```

Phase 82 adds a deterministic DAP v2 layer alongside the existing debug servers.
It provides versioned capabilities, reproducible VM-backed launch and resume,
conditional and hit-conditional breakpoints, and inspectable stack, scope,
variable, evaluation, and exception responses. `dap_v2_report()` summarizes the
session and snapshot fingerprint with a stable digest, and `dap_v2_gate()`
reduces it to a PASS/FAIL decision for debugger tooling checks.

### Formatter v3

```bash
pea fmt-v3 --capabilities
pea fmt-v3 app.pea --check --indent 2 --emit fmt.json
pea fmt-v3 app.pea --write
```

Phase 83 adds a deterministic formatter v3 alongside the existing formatter. It
preserves comments and string contents, validates formatting profiles, and
reports unified diffs, long lines, idempotence, and bytecode parity evidence.
`formatter_v3_report()` produces a stable digest over those results, and
`formatter_v3_gate()` reduces it to a PASS/FAIL decision for editor and CI checks.

### Linter v3

```bash
pea lint-v3 --capabilities
pea lint-v3 app.pea --check --max-complexity 8 --emit lint.json
pea lint-v3 app.pea --check --fail-on-warning
```

Phase 84 adds a deterministic linter v3 alongside the existing linter. It emits
stable rule codes with fix hints, deterministic ordering, and digests that ignore
host paths. `lint_v3_report()` summarizes the findings with a recomputable
digest, and `lint_v3_gate()` supplies a CI-ready PASS/FAIL decision with optional
strict warning handling.

### Test framework v2

```bash
pea test-v2 --capabilities
pea test-v2 tests --check --filter auth --emit tests.json
pea test-v2 tests --check --fail-fast --max-failures 0
```

Phase 85 adds a deterministic test framework v2 alongside the existing
`pea test` runner. It assigns stable case IDs, orders cases deterministically,
and omits elapsed timings and raw host paths from evidence and digests.
`TestProfileV2` validates filtering, fail-fast behavior, and the allowed failure
count; `test_v2_report()` and `test_v2_gate()` provide reproducible CI results.

### Project queries

```bash
pea version <path>                       # query a project/library version
pea audit [path]                         # audit permissions and lockfile integrity
```

Every dependency command emits structured JSON where useful, making scripts and CI pipelines straightforward to build on top of the lifecycle.

## Use Cases

PeaLang is built to deliver complex programs across data, web, and polyglot
workloads. Runnable examples live in `examples/use_cases/` and are covered by
the regression suite. See [`docs/USE_CASES.md`](docs/USE_CASES.md) for the full
map.

### Data processing and analysis

```pea
let raw = analysis.read_csv_file("sales.csv")
let clean = analysis.dropna(raw)
let enriched = analysis.add_column(clean, "revenue", function(row) {
    return row["units"] * row["price"]
})
let by_region = analysis.sql(enriched,
    "SELECT region, SUM(revenue) AS revenue FROM data GROUP BY region ORDER BY revenue DESC")
analysis.write_json_file("out/sales_report.json", by_region)
print analysis.to_markdown(analysis.profile(enriched))
```

SQL runs over ordinary records in an in-memory SQLite database, so `GROUP BY`,
window functions, and CTEs are available without a server. CSV, JSON, and JSONL
file IO keeps pipelines portable.

### Polyglot delivery (Python, Go, TypeScript, Java)

```pea
let root = interop.call_python("math", "sqrt", 169)
if interop.go_available() {
    let result = interop.go_run("package main\n\nimport \"fmt\"\n\nfunc main() { fmt.Println(42) }")
    print result["stdout"]
}
interop.write_text("client.go", interop.generate_go("http://127.0.0.1:8787"))
interop.write_text("client.ts", interop.generate_typescript("http://127.0.0.1:8787"))
```

`interop.go_run` compiles and runs Go source and degrades gracefully when the Go
toolchain is missing. Generated Go, TypeScript, and Java clients target the
PeaLang runtime HTTP service.

### Web data APIs

```pea
let app = web.app()
app.get("/summary", function(req) {
    return web.json({"groups": analysis.group_by(data, "team", "score", "mean")})
})
```

Scaffold related projects with `pea init mydata --template data` or
`pea init mybridge --template polyglot`.

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

PeaLang provides a `std.*` namespace (v1.0 manifest) covering common application functionality, plus application-focused modules:

- Core: `std.collections`, `std.string`, `std.math`, `std.datetime`, `std.json`, `std.csv`, `std.regex`, `std.path`, `std.testing`, `std.crypto`
- Controlled capabilities: `std.file`, `std.http`, `std.logging`, `std.concurrent`
- Experience layer: `std.web`, `std.analysis`, `std.interop`, `std.ux`

Inspect modules:

```bash
pea stdlib
```

Sensitive operations require explicit permissions/capabilities in embedded or controlled runtimes (filesystem, HTTP/network, logging, concurrency, and host interop/process access depending on context).

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
 
