# PeaLang 1.0.0-experience Release Notes

**Date:** 2026-11-08  
**Base:** PeaLang 0.99.6 security-hardened runtime/tooling foundation  
**Scope:** Comprehensive developer-experience layer for language ergonomics, web apps, data analysis, cross-language interop, and CLI/tooling.

## Summary

This release delivers a broad, practical application-development surface on top of PeaLang's existing interpreter/VM, embedding, security, and integration foundations. It focuses on making PeaLang useful for day-to-day work: building web services, analyzing data, integrating with Python/native/process/HTTP systems, and working efficiently from the CLI.

## Highlights

### 1) Language Ergonomics
- **Comprehensions:** list comprehensions (`[x*2 for x in xs if cond]`) and dict comprehensions (`{k:v for [k,v] in items(d)}`), including destructuring patterns in comprehension targets.
- **Optional chaining / null coalescing:** `obj?.field`, `arr?.[i]`, `fn?.()`, `value ?? fallback`.
- **Anonymous functions:** `function(x){ return x + 1 }`.
- **Pattern matching:** `match` as statement and expression with literal patterns, wildcard `_`, OR patterns (`1,2 => ...`), and guards.
- **Destructuring:** `let [a,b]=...`, `let {name,score}=...`, and destructuring in `for` loops (`for [k,v] in pairs`, `for {name} in users`).
- **Operators & builtins:** `in` / `not in`; builtins including `enumerate`, `zip`, `sorted`, `reversed`, `map`, `filter`, `sum`, `any`, `all`, `min`, `max`, `abs`, `items`, `list`, `dict`, `bool`, `float`.

### 2) Web Applications (`web` / `std.web`)
- Lightweight `web.app()` with routing (`get/post/put/delete/patch/options`), route groups (`app.group("/api")`), middleware, static files, and custom 404/error handlers.
- Request model: method/path/headers/query/params/cookies/body/json/form helpers.
- Response helpers: `web.json/html/text/redirect/error`, `render_template`, `set_cookie`.
- CORS support with preflight handling/header application (`app.enable_cors()`).
- OpenAPI 3.0 generation from registered routes (`web.openapi(app, title, version)`), including path parameter conversion.

### 3) Data Analysis (`analysis` / `std.analysis`)
- Profiling/stats: `profile`, `describe`, `summary`, `correlation`, `corr_matrix`, `quantile`, `outliers`.
- Cleaning/transforms: `clean_missing`, `fillna`, `impute`, `normalize`, `rename`, `drop_duplicates`, `sort_by`, `select`, `filter_rows`, `query`, `add_column`, `cumsum`.
- Reshaping/combining: `group_by`, `pivot`, `join`/`merge`, `concat`, `sample`, `unique`, `value_counts`, `top_values`, `head`, `tail`.
- Output/visualization: `to_csv`, `to_markdown`, `to_html`, `bar_chart`, `line_chart`.

### 4) Cross-Language Interop (`interop` / `std.interop`)
- Python bridge (`call_python`, `import_python`) and native ctypes bridge (`load_library`, `call_native`).
- Process execution (`run`), JSON piping (`pipe_json`), executable discovery (`which`), and environment access (`env`).
- HTTP helpers (`http_get`, `http_post`) and JSON-RPC (`json_rpc`).
- Client/stub generation: `generate_typescript`, `generate_java`, `generate_python_stub`.

### 5) UX, CLI, and Project Templates
- `ux`/`std.ux`: `doctor`, `explain`, `suggest`.
- CLI additions/improvements: `pea eval -e`, `pea lint`, `pea doctor`, `pea templates`, `pea info`, `pea new`, `pea serve-web`, template-aware `pea init --template`.
- Templates: `default`, `webapp`, `analysis`, `library`, `interop`.

## Compatibility and Security Notes
- Builds on the **0.99.6** security baseline (SSH/SFTP fail-closed behavior, signing hardening, type-system ReDoS protections as documented for 0.99.6).
- Interop/process/native features can access host capabilities; use only in trusted contexts or with explicit runtime controls/permissions.
- Existing security, capability, and embedding controls remain the recommended boundary for untrusted extensions.

## Validation

```bash
python -m pytest -q
```

**Result:** 693 passed, 1 skipped.

New/updated coverage includes: language ergonomics (comprehensions, `in`/`not in`, `**`, match/destructuring, helpers/builtins), web routing/groups/CORS/OpenAPI/validation/SSE/file/auth/cache/status/redirect/security/health/envelope/validation/accepts helpers, analysis profiling/transforms/stats/IO/charts/melt/zscore/histogram/cut/shape/string/reshape/timeseries/encoding/columns/aggregates/jsonl/expanding, interop (Python/native/process/HTTP/JSON-RPC/env/files/paths/copy/hash/walk/temp/host-info/codegen), UX/templates, and CLI (`eval -e/-f`, `check/lint --json`, `analyze`, `web-openapi`/`openapi`, `hash`, `tree`, `env`, `version --json`, `quickstart`, `info`, `new`, `serve-web`, templates/doctor).

## Additional Batch Notes (v124)
- **Pipelines:** `pealang/pipeline.py` adds composable `impute`, `encode` and `scale` steps, applied in order.
- **Imputation:** `auto` uses means for numeric columns and modes for categorical ones; explicit `mean`, `median`, `mode`, `constant` and `zero` are available.
- **Encoding:** one-hot produces `name=level` columns, with missing values as a `null` level; ordinal produces level indices. Unseen categories become all-zero one-hot rows or `-1`.
- **Scaling:** standard z-scores and min-max scaling store their centers and scales for reuse.
- **Fit and transform:** `fit_pipeline` returns fitted steps, transformed rows, output names and input names; `transform_pipeline` reapplies the transformer to new rows.
- **Model wrappers:** `analysis.model_pipeline` fits a pipeline and estimator from records and stores the `preprocessor`, `output_features`, `importance` and training diagnostics; `analysis.predict_pipeline` scores records or a raw matrix.
- **Use case:** `examples/use_cases/20_feature_pipeline.pea` with categorical churn features, missing numeric values, an unseen region and a missing tenure.
- **Docs:** `docs/FEATURE_PIPELINES.md` and `help/PIPELINES.md`.
- **Tests:** `tests/test_pipeline_v124.py` and `tests/test_use_cases_v124.py`.

## Additional Batch Notes (v123)
- **Imbalance:** `pealang/imbalance.py` adds `class_balance`, `random_oversample`, `random_undersample` and `smote`.
- **Reporting:** `class_balance` returns class counts, shares, majority/minority classes and the imbalance ratio.
- **Resampling:** random oversampling duplicates minority rows to the majority count; random undersampling drops majority rows to the minority count; both are seeded and preserve original row order.
- **SMOTE:** synthesizes minority rows by interpolating between a base row and one of its `k` nearest same-class neighbors, handles multiclass targets, and duplicates single-row classes.
- **Record wrapper:** `analysis.balance_classes` accepts `"smote"`, `"oversample"` or `"undersample"` and adds before/after counts, row counts and imbalance ratios.
- **Use case:** `examples/use_cases/19_class_imbalance.pea` showing the recall and balanced-accuracy gain from resampling training rows only.
- **Docs:** `docs/CLASS_IMBALANCE.md` and `help/IMBALANCE.md`.
- **Tests:** `tests/test_imbalance_v123.py` and `tests/test_use_cases_v123.py`.

## Additional Batch Notes (v122)
- **Interpretation:** `pealang/interpret.py` adds `permutation_importance` and `partial_dependence` for fitted tree, forest and boosting models.
- **Permutation importance:** scores the untouched data as a baseline, shuffles each column `n_repeats` times with a seeded order, and reports the metric drop with mean and spread, ranked best-first.
- **Partial dependence:** sweeps selected features over an evenly spaced grid between their observed min and max and averages predictions. Classification curves add `classes` and per-class `probabilities`; `average` is the last (positive for binary) class.
- **Record wrapper:** `analysis.interpret_report` fits `"tree"`, `"forest"` or `"boosting"` from records and adds `features`, split-gain `importance`, `permutation_importance`, `partial_dependence`, `baseline`, `scoring` and `n_used`.
- **Use case:** `examples/use_cases/18_model_interpretation.pea` with boosted regression, signal-versus-noise ranking and probability curves.
- **Docs:** `docs/MODEL_INTERPRETATION.md` and `help/INTERPRETATION.md`.
- **Tests:** `tests/test_interpret_v122.py` and `tests/test_use_cases_v122.py`.

## Additional Batch Notes (v121)
- **Selection:** `pealang/selection.py` adds `cross_validate`, `grid_search` and `random_search` for `"tree"`, `"forest"` and `"boosting"` estimators, selected by name.
- **Cross-validation:** stratified folds for classification when every class has at least `folds` samples, plain k-fold otherwise; results include per-fold scores, `mean`, `std` and `higher_is_better`.
- **Search:** grid search evaluates every combination; random search samples `n_iter` distinct seeded candidates. Both rank candidates, return `best_params`/`best_score`/`best_std`, and refit the winner on all rows.
- **Scoring:** `"auto"` picks `r2` or `accuracy`; regression also supports `explained_variance`, `mse`, `rmse`, `mae`, and classification supports `balanced_accuracy`, `f1`, `roc_auc`, `log_loss`, with lower-is-better ranking for error and loss metrics.
- **Record wrappers:** `analysis.tune_model` and `analysis.random_tune` add `features`, `n_used` and a `best_model.importance` table.
- **Use case:** `examples/use_cases/17_model_selection.pea` with boosted-regression grid search and forest random search.
- **Docs:** `docs/MODEL_SELECTION.md` and `help/SELECTION.md`.
- **Tests:** `tests/test_selection_v121.py` and `tests/test_use_cases_v121.py`.

## Additional Batch Notes (v120)
- **Boosting:** `pealang/boosting.py` adds `gradient_boosting` for regression (squared error), binary classification (logistic loss) and multiclass classification (softmax), with `learning_rate`, shallow base trees, seeded row `subsample` and `max_features`.
- **Leaf updates:** binary and multiclass stages use Newton leaf values; multiclass applies the Friedman `(K - 1) / K` multiplier and fits one tree per class per round.
- **Prediction and importance:** `predict_boosting` returns predictions, class probabilities and class order; `boosting_feature_importance` averages per-tree split gain.
- **Record wrapper:** `analysis.boosting_report` with automatic task inference, in-sample diagnostics and binary log loss. `auto` now recognizes non-numeric and low-cardinality integer targets as classification.
- **Use case:** `examples/use_cases/16_gradient_boosting.pea` with holdout regression, binary classification and overlapping multiclass classification.
- **Docs:** `docs/GRADIENT_BOOSTING.md` and `help/BOOSTING.md`.
- **Tests:** `tests/test_boosting_v120.py` and `tests/test_use_cases_v120.py`.

## Additional Batch Notes (v119)
- **Trees:** `pealang/trees.py` adds CART `decision_tree` for regression (squared error) and classification (Gini), with `max_depth`, `min_samples_split`, `min_samples_leaf`, seeded `max_features`, and `predict_tree` returning predictions plus class probabilities.
- **Forests:** `random_forest` bagging with bootstrap sampling, per-split feature subsets, averaged predictions, and out-of-bag scoring (`oob_score`, `oob_predictions`).
- **Importance:** `tree_feature_importance` and `forest_feature_importance` return sorted `{feature, importance}` tables from accumulated split gain.
- **Record wrappers:** `analysis.tree_report` and `analysis.forest_report` with automatic task inference and in-sample diagnostics.
- **Use case:** `examples/use_cases/15_trees_forests.pea`.
- **Docs:** `docs/TREE_MODELS.md` and `help/TREES.md`.
- **Tests:** `tests/test_trees_v119.py` and `tests/test_use_cases_v119.py`.

## Additional Batch Notes (v118)
- **Evaluation:** `pealang/evaluation.py` adds deterministic `train_test_split` with stratification, `k_fold`, and `stratified_k_fold`.
- **Metrics:** classification (`accuracy_score`, `balanced_accuracy`, `precision_recall_fscore`), ranking and probability (`roc_auc`, `roc_curve`, `log_loss`, `brier_score`, `calibration_curve`), and regression (`mean_squared_error`, `root_mean_squared_error`, `mean_absolute_error`, `median_absolute_error`, `mean_absolute_percentage_error`, `r2_score`, `explained_variance_score`).
- **Feature preparation:** `polynomial_features`, `label_encode`, `ordinal_encode`, `standardize_features` / `standardize_transform`, and `minmax_features` / `minmax_transform`.
- **Record wrappers:** `analysis.train_test_split`, `analysis.evaluate_classification`, `analysis.evaluate_regression`, and `analysis.add_polynomial_features`.
- **Use case:** `examples/use_cases/14_model_evaluation.pea`.
- **Docs:** `docs/MODEL_EVALUATION.md` and `help/EVALUATION.md`.
- **Tests:** `tests/test_evaluation_v118.py` and `tests/test_use_cases_v118.py`.

## Additional Batch Notes (v117)
- **Causal inference:** `pealang/causal.py` adds propensity scores (`propensity_scores`), balance diagnostics (`covariate_balance`), IPW and doubly robust effects (`ipw_ate`, `aipw_ate`), nearest-neighbour matching (`propensity_match`), difference-in-differences (`difference_in_differences`), two-stage least squares (`instrumental_variables`), and regression discontinuity (`regression_discontinuity`).
- **Record wrappers:** `analysis.causal_report`, `analysis.did_report`, `analysis.iv_report`, and `analysis.rdd_report`.
- **Use case:** `examples/use_cases/13_causal_inference.pea`.
- **Docs:** `docs/CAUSAL_INFERENCE.md` and `help/CAUSAL.md`.
- **Tests:** `tests/test_causal_v117.py` and `tests/test_use_cases_v117.py`.

## Additional Batch Notes (v116)
- **Predictive modeling:** `pealang/modeling.py` adds inferential generalized linear models (`glm`, `logistic_regression`, `poisson_regression`), regularized regression (`ridge_regression`, `lasso_regression`, `elastic_net`), survival analysis (`kaplan_meier`, `log_rank_test`, `cox_proportional_hazards`, `concordance_index`), and ARIMA forecasting (`arima`, `auto_arima`).
- **Record wrappers:** `analysis.glm_report`, `analysis.survival_report`, and `analysis.arima_report`.
- **Use cases:** `examples/use_cases/11_glm_survival.pea` and `12_arima_forecasting.pea`.
- **Docs:** `docs/ADVANCED_MODELING.md` and `help/MODELING.md`.
- **Tests:** `tests/test_modeling_v116.py`, `tests/test_survival_v116.py`, `tests/test_use_cases_v116.py`.

## Additional Batch Notes (v115)
- **Statistical inference:** `pealang/inference.py` adds confidence intervals (Student-t, Wilson, Welch, bootstrap), effect sizes and power, multiple-comparison correction (Bonferroni/Holm/BH), parametric and nonparametric tests, normality and permutation tests.
- **Regression diagnostics:** `stats.ols` returns a full coefficient table with standard errors, t/p values, confidence intervals, R², adjusted R², F-test, AIC/BIC, Durbin-Watson and covariance; `predict_ols`, `variance_inflation_factors`, and `residual_diagnostics` complete the workflow.
- **Time series:** `acf`, `pacf`, `ljung_box`, `difference_series`, `moving_average`, `simple_exponential_smoothing`, `holt_linear`, `holt_winters`, `seasonal_decompose`, `changepoint_cusum`, and `adf_test`, plus `analysis.regression_report` and `analysis.time_series_report`.
- **Use cases:** `examples/use_cases/09_inference_report.pea` and `10_forecasting_pipeline.pea`.
- **Docs:** `docs/STATISTICAL_INFERENCE.md` and `help/INFERENCE.md`.
- **Tests:** `tests/test_inference_v115.py`, `tests/test_timeseries_v115.py`, `tests/test_use_cases_v115.py`.

## Additional Batch Notes (v114)
- **Native data science:** `pealang/numerics.py` exposes `stats` / `std.stats` with descriptive statistics, linear algebra, probability distributions, hypothesis tests, regression, k-means, PCA, interpolation, and resampling — all dependency-free.
- **pandas-class analysis:** `analysis` gains `qcut`, `rolling_sum`/`min`/`max`/`median`/`var`, `expanding_std`/`var`/`median`, `interpolate`, `factorize`, `mask`, `select_dtypes`, `info`, `memory_usage`, `pivot_table`, `reset_index`/`set_index`, `agg`, `transform`, `group_by_multi`, `merge_multi`, `describe_all`, `missing_summary`, `winsorize`, `corr_spearman`, and `date_range`.
- **Use cases:** `examples/use_cases/06_statistical_analysis.pea`, `07_matrix_regression.pea`, and `08_segmentation_clustering.pea` with regression coverage in `tests/test_use_cases_v114.py`.
- **Docs:** `docs/DATA_SCIENCE.md` and `help/NUMERICS.md`.
- **Tests:** `tests/test_numerics_v114.py`, `tests/test_analysis_v114.py`, `tests/test_stats_namespace_v114.py`.

## Additional Batch Notes (v113)
- **Data processing:** `analysis.sql` / `analysis.sql_value` run SQLite SQL (grouping, window functions, CTEs) over in-memory records; `analysis.read_csv_file`, `analysis.write_csv_file`, `analysis.read_json_file`, `analysis.write_json_file`, `analysis.read_jsonl_file`, `analysis.write_jsonl_file` provide file-based IO.
- **Go interop:** `interop.go_run` compiles and runs Go source with graceful missing-toolchain handling; `interop.go_available`, `interop.go_version`, and `interop.generate_go` provide discovery and client generation.
- **Templates:** `data` and `polyglot` project templates.
- **Use cases:** runnable programs in `examples/use_cases/` (sales pipeline, analytics report, SQL analytics, polyglot bridge, web data API) with regression coverage in `tests/test_use_cases_v113.py`, `tests/test_analysis_sql_v113.py`, and `tests/test_go_interop_v113.py`.
- **Docs:** `docs/USE_CASES.md`, `help/DATA_PIPELINES.md`, `help/POLYGLOT.md`.
- **CLI:** `pea templates` now prints one template per line.

## Additional Batch Notes (v112)
- **Builtins:** `gcd`, `lcm`, `sign`, `is_even`/`is_odd`, `lerp`, `rotate`, `interleave`, `windows` (sliding), `dedupe_by`, `assoc`, `dissoc`, `rename_keys`, `format_number`, `between` (scalar).
- **Analysis:** `rolling_std`, `expanding_sum`/`expanding_max`/`expanding_min`, `sample_frac`, `ewm_mean`, `standardize`.
- **Web:** `accepts`, `accepts_json`, `accepts_html`, `no_cache`, `vary`, `link_header`.
- **Interop (host, trusted):** `cpu_count`, `hostname`, `user`, `pid`.
- **CLI/Templates:** `pea env <NAME>` / `--keys`, `automation` template.

## Additional Batch Notes (v111)
- **Builtins:** `group_by` (list), `frequencies`, `scan`, `hex_encode`/`hex_decode`, `ensure_str`/`ensure_int`/`ensure_float`, `pipe`, `apply`.
- **Analysis:** `mean_col`/`sum_col`/`min_col`/`max_col`/`median_col`, `skew`, `kurtosis`, `expanding_mean`, `corr` (alias), `to_jsonl`/`from_jsonl`.
- **Web:** `validation_error`, `content_type`, `merge_headers`, `query_int`/`query_bool`, `api_key_auth`, `method_is`.
- **Interop (host, trusted):** `env_all`, `expanduser`, `expandvars`, `touch`, `head_file`/`tail_file`.
- **CLI/Templates:** `pea tree [path]`, `pea version --json`, `etl` project template.

## Additional Batch Notes (v110)
- **Builtins:** `min_by`, `max_by`, `without`, `xor`, `zip_object`, `ensure_list`, `ensure_dict`, `size`, `random_choice`, `sample_list`, `clone`, `deep_clone`, `deep_equal`, `nth`, `initial`, `rest`.
- **Analysis:** `drop_columns`, `keep_columns`, `assign`, `round_col`, `abs_col`, `variance`, `std`, `covariance`, `idxmax`, `idxmin`.
- **Web/UX:** `web.health`, `web.envelope`, `web.with_links`, `web.negotiate`, `web.request_logger`; `ux.quickstart`, `ux.commands`.
- **Interop (host, trusted):** `walk`, `readlines`, `writelines`, `tempfile`.
- **CLI/Templates:** `pea openapi` alias, `pea quickstart`, `api` project template.

## Additional Batch Notes (v109)
- **Builtins:** `has_path`, `set_path` (immutable), `map_values`, `map_keys`, `pick_by`, `omit_by`, `shuffle`, `product`, `median`, `parse_int`, `parse_float`, `strip_prefix`, `strip_suffix`, `sha256`, `url_encode`, `url_decode`, `html_escape`, `title_case`, `center`.
- **Analysis:** `shift`, `lag`, `lead`, `cummax`, `cummin`, `cumprod`, `replace_values`, `one_hot`, `split_column`, `percentile` (alias).
- **Web:** `bad_request`, `server_error`, `not_modified`, `moved_permanently`, `see_other`, `temporary_redirect`, `permanent_redirect`, `security_headers`, `parse_query`, `build_query`.
- **Interop (host, trusted; `remove_file` destructive):** `copy_file`, `remove_file`, `list_dir`, `stat`, `hash_file`.
- **CLI:** `pea web-openapi <file> [--title T] [--version V]`, `pea hash <file> [--algo sha256]`.

## Additional Batch Notes (v108)
- **Builtins:** `is_empty`, `compact`, `defaults`, `invert`, `to_pairs`, `from_pairs`, `sum_by`, `avg`, `capitalize`, `snake_case`, `kebab_case`, `slugify`, `truncate`, `union`, `intersection`, `difference`.
- **Analysis:** `explode`, `where`, `shape`, `isna`, `notna`, `astype` (alias), `to_records`, `to_dict`, `str_transform`/`str_lower`/`str_upper`/`str_strip`/`str_contains`/`str_replace`.
- **Web:** `unauthorized`, `forbidden`, `conflict`, `too_many_requests`, `gone`, `unprocessable`, `download`, `status`.
- **Interop (host, trusted):** `join_path`, `extname`, `stem`, `is_file`, `is_dir`, `abspath`, `cwd`, `platform`.
- **CLI:** `pea check --json` / `pea lint --json`, `pea analyze <file.json|csv> [--json] [--head N]`.

## Additional Batch Notes (v107)
- **Builtins:** `get_path`, `deep_merge`, `take`, `drop`, `partition`, `count_by`, `first`, `last`.
- **Analysis:** `duplicated`, `nlargest`, `nsmallest`, `pivot_wider`.
- **Web:** `not_found`, `method_not_allowed`, `url_join`.
- **Interop (host, trusted):** `glob`, `exists`, `mkdir_p`, `tempdir`, `basename`, `dirname`.

## Additional Batch Notes (v106)
- **Builtins:** type predicates (`is_null/is_list/is_dict/is_string/is_number/is_bool`), `identity`, `tap`, `pad_start`, `pad_end`, `lines`, `words`, `floor`, `ceil`, `log`, `exp`, `pow`.
- **Analysis:** `ffill`, `bfill`, `dropna`, `cast`, `crosstab`.
- **Web:** `ok`, `problem` (RFC7807-style), `pagination`, `parse_basic_auth`.
- **Interop:** `read_text`, `write_text`, `read_json`, `write_json` (host access; use in trusted contexts).
- **CLI:** `pea test -k` filter alias.

## Additional Batch Notes (v105)
- **Builtins:** `coalesce`, `repeat`, `times`, `find`, `find_index`, `pluck`, `index_by`, `sort_by` (list by key).
- **Analysis:** `zscore`, `histogram`, `cut`.
- **Web:** `cache_control`, `basic_auth`, `no_content`, `created`, `accepted`.
- **CLI:** `pea eval -f <file>`.

## Additional Batch Notes (v104)
- **Builtins:** `chunk`, `flatten`, `uniq`, `pick`, `omit`, `clamp`, `uuid`, `randint`, `b64encode`, `b64decode`, `now_iso`.
- **Analysis:** `rank`, `pct_change`, `diff`, `rolling_mean`, `schema`.
- **Web:** `request_id` middleware, `json_error`, `etag`.
- **CLI:** `pea new`, `pea serve-web <file>` (best-effort).

## Additional Batch Notes (v103)
- **`**` power operator** added; `//` is intentionally kept as line-comment syntax for compatibility (use `int(a/b)` for floor division).
- **Builtins/helpers:** `get`, `has`, `merge`, `push`, `pop`, `slice`, `contains`, `trim`, `replace`, `starts_with`, `ends_with`, `json_parse`, `json_dump`, `safe`, `now_ms`.
- **Web:** route groups, `patch`/`options`, CORS preflight, `validate`, `file`, `sse`, `response`, `rate_limit`, `bearer_auth`.
- **Analysis:** `from_csv`/`from_json`/`to_json`, `between`, `clip`, `mode`, `nunique`, `count`, `melt`, `transpose`.
- **Interop/CLI:** `json_rpc`, `pipe_json`, `env`; `pea eval -e`, `pea info`.

## Upgrade/Adoption Guidance
- Start with `pea doctor` and `pea templates`.
- For a web service: `pea init myapi --template webapp`.
- For data workflows: use `analysis.*` / `std.analysis.*` and `pea eval -e` for quick checks.
- For host integration: prefer the embedding/service APIs and explicit capability controls; use `interop` only where host access is intended and trusted.