# PeaLang

Readable automation, data, integration, orchestration, web, and AI workflow language.

PeaLang is an embeddable extension language designed for rules, workflows, integrations, data processing, web applications, automation, and controlled application customization.

PeaLang is designed to complement existing ecosystems such as Python, FastAPI, Java, TypeScript, React, databases, messaging systems, and enterprise applications rather than replace them.

## Release Status

Base version: **0.99.6** (security hardening baseline)  
Experience layer: **1.0.0-experience** (developer experience, language ergonomics, web/data/interop)

The 1.0.0-experience layer builds on the 0.99.6 security baseline with a comprehensive application-development surface while preserving the existing runtime, security, and integration foundations.

PeaLang v0.99.6 is a security-focused release following the v0.99.5 compatibility and release-readiness work.

The release addresses security findings identified after enabling GitHub CodeQL analysis against the reconstructed PeaLang repository history.

No new major feature family is introduced in v0.99.6.

The objective is to improve security while preserving the existing PeaLang language, runtime, SDK, data, integration, orchestration, ML, tooling, and enterprise capabilities.

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
 
