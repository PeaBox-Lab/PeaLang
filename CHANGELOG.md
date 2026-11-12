# Changelog

## 1.0.0-experience (ongoing) - 2026-11-08

### Feature pipelines (v124)
- Added `pealang/pipeline.py`, a dependency-free preprocessing layer exposed through `stats` / `std.stats`.
- Added ordered steps for imputation (`auto`, `mean`, `median`, `mode`, `constant`, `zero`), encoding (`onehot`, `ordinal` / `label`) and scaling (`standard`, `minmax`).
- Added `fit_pipeline`, which learns fill values, category levels, centers and scales and returns the transformed training rows with output column names.
- Added `transform_pipeline`, which reapplies a fitted transformer to new rows; unseen categories become all-zero one-hot rows or `-1` ordinal codes.
- Added model wrappers `analysis.model_pipeline` and `analysis.predict_pipeline`, which fit a pipeline and estimator from raw records and score new records end to end.
- Added runnable use case `examples/use_cases/20_feature_pipeline.pea` with categorical churn features, missing numeric values and unseen-category scoring.
- Added `docs/FEATURE_PIPELINES.md` and `help/PIPELINES.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported pipeline helpers from the Python package (`build_pipeline_namespace`, `stats_fit_pipeline`, `stats_transform_pipeline`).
- Added regression coverage: `tests/test_pipeline_v124.py` and `tests/test_use_cases_v124.py`.

### Class imbalance (v123)
- Added `pealang/imbalance.py`, a dependency-free resampling layer exposed through `stats` / `std.stats`.
- Added `class_balance`, reporting class counts, shares, majority/minority classes and the imbalance ratio.
- Added seeded `random_oversample` and `random_undersample`, which balance classes by duplicating minority rows or dropping majority rows.
- Added seeded `smote`, which synthesizes minority rows by interpolating between a base row and one of its `k` nearest same-class neighbors; it handles multiclass targets and duplicates single-row classes.
- Added record-friendly wrapper `analysis.balance_classes`, with before/after counts, row counts and imbalance ratios.
- Added runnable use case `examples/use_cases/19_class_imbalance.pea` showing the recall and balanced-accuracy gain from resampling only the training rows.
- Added `docs/CLASS_IMBALANCE.md` and `help/IMBALANCE.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported imbalance helpers from the Python package (`build_imbalance_namespace`, `stats_class_balance`, `stats_random_oversample`, `stats_random_undersample`, `stats_smote`).
- Added regression coverage: `tests/test_imbalance_v123.py` and `tests/test_use_cases_v123.py`.

### Model interpretation (v122)
- Added `pealang/interpret.py`, a dependency-free explanation layer for fitted tree, forest and boosting models, exposed through `stats` / `std.stats`.
- Added `permutation_importance`, which scores the baseline, shuffles each feature `n_repeats` times, and reports the metric drop with mean and spread, ranked best-first.
- Added `partial_dependence`, which sweeps selected features over an evenly spaced grid and averages predictions, with per-class probability curves for classification.
- Added record-friendly wrapper `analysis.interpret_report`, which fits `"tree"`, `"forest"` or `"boosting"` from records and adds split-gain importance, permutation importance, partial dependence curves, baseline and scoring.
- Added runnable use case `examples/use_cases/18_model_interpretation.pea` covering boosted regression, signal-versus-noise ranking and probability curves.
- Added `docs/MODEL_INTERPRETATION.md` and `help/INTERPRETATION.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported interpretation helpers from the Python package (`build_interpret_namespace`, `stats_permutation_importance`, `stats_partial_dependence`).
- Added regression coverage: `tests/test_interpret_v122.py` and `tests/test_use_cases_v122.py`.

### Model selection (v121)
- Added `pealang/selection.py`, a dependency-free tuning layer exposed through `stats` / `std.stats`.
- Added `cross_validate`, which scores `"tree"`, `"forest"` or `"boosting"` estimators with k-fold cross-validation, stratified folds for classification, per-fold scores and mean/standard deviation.
- Added `grid_search` and seeded `random_search`, both returning ranked candidate tables, `best_params`, `best_score`, `best_std` and a `best_model` refit on all rows.
- Added scoring selection with `"auto"` plus `r2`, `explained_variance`, `mse`, `rmse`, `mae`, `accuracy`, `balanced_accuracy`, `f1`, `roc_auc` and `log_loss`, including lower-is-better ranking for error and loss metrics.
- Added record-friendly wrappers `analysis.tune_model` and `analysis.random_tune`, with `features`, `n_used` and a `best_model.importance` table.
- Added runnable use case `examples/use_cases/17_model_selection.pea` covering boosted-regression grid search and forest random search.
- Added `docs/MODEL_SELECTION.md` and `help/SELECTION.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported selection helpers from the Python package (`build_selection_namespace`, `stats_cross_validate`, `stats_grid_search`, `stats_random_search`).
- Added regression coverage: `tests/test_selection_v121.py` and `tests/test_use_cases_v121.py`.

### Gradient boosted trees (v120)
- Added `pealang/boosting.py`, a dependency-free gradient boosting layer exposed through `stats` / `std.stats`.
- Regression uses squared-error boosting with a mean base prediction. Binary classification uses logistic loss with a log-odds base and Newton leaf updates. Multiclass classification uses softmax loss with one tree per class per round and the Friedman `(K - 1) / K` leaf multiplier.
- Added `gradient_boosting`, `predict_boosting` and `boosting_feature_importance`, with `learning_rate`, `max_depth`, `min_samples_split`, `min_samples_leaf`, seeded row `subsample` and `max_features`.
- Added record-friendly wrapper `analysis.boosting_report`, with automatic task inference, in-sample diagnostics and binary log loss.
- Improved `analysis._infer_task`: `auto` now treats non-numeric and low-cardinality integer targets as classification, so multiclass tables work without an explicit task.
- Added runnable use case `examples/use_cases/16_gradient_boosting.pea` covering holdout regression, nonlinear binary classification and overlapping multiclass classification.
- Added `docs/GRADIENT_BOOSTING.md` and `help/BOOSTING.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported boosting helpers from the Python package (`build_boosting_namespace`, `stats_gradient_boosting`, `stats_predict_boosting`, `stats_boosting_importance`).
- Added regression coverage: `tests/test_boosting_v120.py` and `tests/test_use_cases_v120.py`.

### Decision trees and random forests (v119)
- Added `pealang/trees.py`, a dependency-free CART and random-forest layer exposed through `stats` / `std.stats`.
- Trees: `decision_tree` for regression (squared error) and classification (Gini), with `max_depth`, `min_samples_split`, `min_samples_leaf`, seeded `max_features`, and `predict_tree` returning predictions, class probabilities and class order.
- Forests: `random_forest` with bootstrap sampling, per-split feature subsets, averaged regression or probability predictions, and out-of-bag scoring (`oob_score`, `oob_predictions`).
- Importance: `tree_feature_importance` and `forest_feature_importance` return sorted `{feature, importance}` tables from accumulated split gain.
- Added record-friendly wrappers `analysis.tree_report` and `analysis.forest_report`, with automatic task inference for boolean and 0/1 targets, in-sample diagnostics, and feature selection from numeric columns.
- Fixed regression out-of-bag prediction to report `null` for rows that were never out of bag instead of dividing by zero.
- Added runnable use case `examples/use_cases/15_trees_forests.pea` covering nonlinear regression, OOB R², two-feature classification and feature importance.
- Added `docs/TREE_MODELS.md` and `help/TREES.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, the README and the roadmap.
- Exported tree helpers from the Python package (`build_tree_namespace`, `stats_decision_tree`, `stats_random_forest`, `stats_predict_tree`, `stats_predict_forest`, `stats_tree_importance`, `stats_forest_importance`).
- Added regression coverage: `tests/test_trees_v119.py` and `tests/test_use_cases_v119.py`.

### Model evaluation and feature preparation (v118)
- Added `pealang/evaluation.py`, a dependency-free assessment layer exposed through `stats` / `std.stats`.
- Resampling: `train_test_split` with optional stratification by largest-remainder allocation, `k_fold`, and `stratified_k_fold` with clear validation when a class is smaller than the fold count.
- Classification metrics: `accuracy_score`, `balanced_accuracy`, `precision_recall_fscore` with per-class and macro/weighted/micro summaries.
- Ranking and probability metrics: tie-aware `roc_auc`, `roc_curve`, `log_loss`, `brier_score`, and `calibration_curve`.
- Regression metrics: `mean_squared_error`, `root_mean_squared_error`, `mean_absolute_error`, `median_absolute_error`, `mean_absolute_percentage_error`, `r2_score`, and `explained_variance_score`.
- Feature preparation: `polynomial_features` (powers, interactions, optional bias), `label_encode`, `ordinal_encode`, `standardize_features` / `standardize_transform`, and `minmax_features` / `minmax_transform`.
- Added record-friendly wrappers `analysis.train_test_split`, `analysis.evaluate_classification`, `analysis.evaluate_regression`, and `analysis.add_polynomial_features`.
- Added runnable use case `examples/use_cases/14_model_evaluation.pea` with holdout scoring, a manual five-fold loop, ROC/AUC, log loss, and feature preparation.
- Added `docs/MODEL_EVALUATION.md` and `help/EVALUATION.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, and the README.
- Exported evaluation helpers from the Python package (`build_evaluation_namespace`, `stats_train_test_split`, `stats_k_fold`, `stats_accuracy`, `stats_roc_auc`, `stats_mse`, `stats_r2_score`, and related aliases).
- Added regression coverage: `tests/test_evaluation_v118.py` and `tests/test_use_cases_v118.py`.

### Causal inference (v117)
- Added `pealang/causal.py`, a dependency-free causal layer exposed through `stats` / `std.stats`.
- Propensity scores: `propensity_scores` with fitted probabilities, logit scores, ATE/ATT weights, overlap diagnostics, and the underlying logistic coefficient table.
- Balance diagnostics: `covariate_balance` with standardized mean differences and weighted SMDs for assessing covariate balance before and after weighting.
- Weighting estimators: `ipw_ate` (Hajek IPW for the ATE and ATT) and `aipw_ate` (doubly robust augmented IPW), both with propensity-refitting bootstrap standard errors and confidence intervals.
- Matching: `propensity_match` with nearest-neighbour matching on the logit propensity score, configurable caliper, ratio, and replacement.
- Difference-in-differences: `difference_in_differences` with an interaction term, covariates, and optional cluster-robust standard errors.
- Instrumental variables: `instrumental_variables` with two-stage least squares, first-stage F statistic, and a Sargan overidentification test.
- Regression discontinuity: `regression_discontinuity` with separate local polynomials, bandwidth selection, and a sharp jump estimate.
- Added record-friendly wrappers `analysis.causal_report`, `analysis.did_report`, `analysis.iv_report`, and `analysis.rdd_report`.
- Added runnable use case `examples/use_cases/13_causal_inference.pea`.
- Added `docs/CAUSAL_INFERENCE.md` and `help/CAUSAL.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, and the README.
- Exported causal helpers from the Python package (`build_causal_namespace`, `stats_propensity_scores`, `stats_covariate_balance`, `stats_ipw_ate`, `stats_aipw_ate`, `stats_propensity_match`, `stats_did`, `stats_iv`, `stats_rdd`).
- Added regression coverage: `tests/test_causal_v117.py` and `tests/test_use_cases_v117.py`.

### Predictive modeling and survival analysis (v116)
- Added `pealang/modeling.py`, a dependency-free modeling layer exposed through `stats` / `std.stats`.
- Generalized linear models: `glm` with Gaussian, binomial (logit), and Poisson (log) families, fitted by iteratively reweighted least squares; convenience wrappers `logistic_regression` and `poisson_regression`; prediction with `predict_glm`.
- GLM results include a coefficient table with standard errors, z-statistics, p-values, confidence intervals, deviance, null deviance, pseudo-R², AIC/BIC, covariance, fitted values, and convergence status.
- Regularized regression: `ridge_regression` (closed form), `lasso_regression` (coordinate descent), and `elastic_net`.
- Survival analysis: `kaplan_meier` (Greenwood confidence bands), `log_rank_test`, `cox_proportional_hazards` (Newton-Raphson, Breslow ties, hazard ratios, concordance), and `concordance_index`.
- Time-series forecasting: `arima` (ARIMA(p, d, q) by conditional least squares with integrated forecasts) and `auto_arima` (AIC order selection with optional ADF differencing).
- Added record-friendly wrappers `analysis.glm_report`, `analysis.survival_report`, and `analysis.arima_report`.
- Added runnable use cases: GLM/survival report and ARIMA forecasting.
- Added `docs/ADVANCED_MODELING.md` and `help/MODELING.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, and the README.
- Exported modeling helpers from the Python package (`build_modeling_namespace`, `stats_glm`, `stats_logistic_regression`, `stats_poisson_regression`, `stats_ridge_regression`, `stats_lasso_regression`, `stats_kaplan_meier`, `stats_cox`, `stats_arima`, `stats_auto_arima`, and related names).
- Added regression coverage: `tests/test_modeling_v116.py`, `tests/test_survival_v116.py`, `tests/test_use_cases_v116.py`.

### Statistical inference and time series (v115)
- Added `pealang/inference.py`, a dependency-free inference, regression-diagnostics and time-series engine layered onto `stats` / `std.stats`.
- Estimation: `standard_error`, `confidence_interval_mean` (Student-t), `confidence_interval_proportion` (Wilson), `confidence_interval_diff_means` (Welch), `margin_of_error`, `bootstrap_ci` (percentile bootstrap).
- Effect size and power: `cohens_d`, `hedges_g`, `eta_squared`, `power_t_test`, `sample_size_t_test`.
- Multiple comparisons: `adjust_p_values` / `multiple_comparison` with Bonferroni, Holm, and Benjamini-Hochberg methods.
- Parametric tests: `z_test_1samp`, `proportion_test`, `z_test_proportions`, `fisher_exact`, `chi_square_goodness_of_fit`.
- Nonparametric tests: `mann_whitney_u`, `wilcoxon_signed_rank`, `kruskal_wallis`, `friedman_test`, `sign_test`, all with tie handling where applicable.
- Normality and resampling: `jarque_bera`, `normality_test`, `permutation_test`.
- Regression diagnostics: `ols` (coefficient table, standard errors, t/p values, confidence intervals, R², adjusted R², F-test, AIC/BIC, Durbin-Watson, covariance), `predict_ols` (prediction intervals), `variance_inflation_factors`, `residual_diagnostics`.
- Time series: `acf`, `pacf` (Durbin-Levinson), `ljung_box`, `difference_series` (regular and seasonal), `moving_average`, `simple_exponential_smoothing`, `holt_linear`, `holt_winters`, `seasonal_decompose`, `changepoint_cusum`, `adf_test`.
- Added inverse distributions `t_ppf`, `chi2_ppf`, and `f_ppf` to `stats`.
- Added record-friendly wrappers `analysis.regression_report` and `analysis.time_series_report`.
- Added runnable use cases: statistical inference report and forecasting pipeline.
- Added `docs/STATISTICAL_INFERENCE.md` and `help/INFERENCE.md`; extended `docs/DATA_SCIENCE.md`, `docs/USE_CASES.md`, and the README.
- Exported inference helpers from the Python package (`build_inference_namespace`, `stats_confidence_interval_mean`, `stats_cohens_d`, `stats_ols`, `stats_acf`, `stats_holt_winters`, `stats_adf_test`, and related names).
- Added regression coverage: `tests/test_inference_v115.py`, `tests/test_timeseries_v115.py`, `tests/test_use_cases_v115.py`.

### Native data science toolkit (v114)
- Added `pealang/numerics.py`, a dependency-free numerical, statistical and modelling engine exposed as the first-class `stats` namespace and the stable `std.stats` module.- Descriptive statistics: `mean`, `median`, `mode`, `quantile`, `percentile`, `iqr`, `variance`, `std`, `skew`, `kurtosis`, `covariance`, `pearson`/`correlation`, `spearman`, `kendall`, `entropy`, `gini`, `describe`.
- Transforms and sampling: `zscore`, `minmax_scale`, `robust_scale`, `winsorize`, `cumsum`/`cumprod`/`cummax`/`cummin`, `diff`, `histogram`, `outliers_z`, `percentile_rank`, `random_uniform`/`normal`/`binomial`/`poisson`, `bootstrap`.
- Linear algebra: `dot`, `norm`, `distance`, `angle`, elementwise arithmetic, `outer`, `transpose`, `identity`, `matmul`, `trace`, `solve`, `determinant`, `inverse`.
- Probability distributions: normal, uniform, exponential, binomial, Poisson, Student's t, F, and chi-square PDFs/CDFs plus `normal_ppf` and `normal_interval`.
- Hypothesis tests: one-sample/independent/Welch/paired t-tests, chi-square, and one-way ANOVA, each returning statistic, degrees of freedom, and p-value.
- Modelling: `linear_regression`, `multiple_regression`, `polyfit`/`polyval`, `r_squared`, `interpolate`, `linspace`, `arange`, k-means (k-means++), PCA, and `confusion_matrix`.
- Extended `analysis` with pandas-class helpers: `qcut`, `rolling_sum`/`min`/`max`/`median`/`var`, `expanding_std`/`var`/`median`, `interpolate`, `factorize`, `mask`, `select_dtypes`, `info`, `memory_usage`, `pivot_table`, `reset_index`/`set_index`, `agg`, `transform`, `group_by_multi`, `merge_multi`, `describe_all`, `missing_summary`, `winsorize`, `corr_spearman`, `date_range`.
- Added runnable use cases: statistical analysis, matrix regression, and customer segmentation.
- Added `docs/DATA_SCIENCE.md` and `help/NUMERICS.md`.
- Exported stats helpers from the Python package (`build_stats_namespace`, `stats_linear_regression`, `stats_kmeans`, `stats_pca`, and related names).
- Added regression coverage: `tests/test_numerics_v114.py`, `tests/test_analysis_v114.py`, `tests/test_stats_namespace_v114.py`, `tests/test_use_cases_v114.py`.

### Data processing and polyglot delivery (v113)
- Added `analysis.sql` and `analysis.sql_value`: run SQL (including `GROUP BY`, window functions and CTEs) over in-memory records via SQLite, returning records in the same shape as the rest of the analysis namespace.
- Added file-based data IO: `analysis.read_csv_file`, `analysis.write_csv_file`, `analysis.read_json_file`, `analysis.write_json_file`, `analysis.read_jsonl_file`, `analysis.write_jsonl_file`.
- Added Go interoperability: `interop.go_run` (compile/run Go source with graceful missing-toolchain handling), `interop.go_available`, `interop.go_version`, and `interop.generate_go` (dependency-free Go client for the runtime service).
- Added `data` and `polyglot` project templates (`pea init --template data|polyglot`).
- Added runnable use-case programs under `examples/use_cases/`: sales pipeline, analytics report, SQL analytics, polyglot bridge, and web data API.
- Added `docs/USE_CASES.md` plus `help/DATA_PIPELINES.md` and `help/POLYGLOT.md`.
- Exported the new analysis and Go helpers from the Python package (`analyze_sql`, `analyze_read_csv`, `generate_go_client`, `go_run`, and related names).
- Added regression coverage: `tests/test_analysis_sql_v113.py`, `tests/test_go_interop_v113.py`, `tests/test_use_cases_v113.py`.

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

### Language and Runtime (v112 additions)
- Added builtins/helpers: `gcd`, `lcm`, `sign`, `is_even`, `is_odd`, `lerp`, `rotate`, `interleave`, `windows` (sliding), `dedupe_by`, `assoc`, `dissoc`, `rename_keys`, `format_number`, `between` (scalar).

### Data Analysis (v112 additions)
- Added: `rolling_std`, `expanding_sum`, `expanding_max`, `expanding_min`, `sample_frac`, `ewm_mean`, `standardize` (alias of `zscore`).

### Web (v112 additions)
- Added: `accepts`, `accepts_json`, `accepts_html`, `no_cache`, `vary`, `link_header`.

### Interop, CLI, and Templates (v112 additions)
- Added interop helpers (host access; trusted contexts): `cpu_count`, `hostname`, `user`, `pid`.
- Added CLI: `pea env <NAME>` / `pea env --keys`.
- Added project template: `automation`.

### Documentation and Quality
- Updated `README.md`, `docs/USER_GUIDE.md`, `CHANGELOG.md`, and `docs/RELEASE_NOTES_1.0_EXPERIENCE.md`.
- Added/expanded tests for v102–v112 features (language, analysis, web, interop/UX, CLI/templates).
- Regression baseline: **693 passed, 1 skipped**.

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
