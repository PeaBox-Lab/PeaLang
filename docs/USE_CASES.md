# PeaLang Use Cases

PeaLang is designed to extend existing systems rather than replace them. This
document maps common application, data, and integration tasks to the language
features and namespaces that support them, and points at runnable examples.

Runnable programs live in `examples/use_cases/`. Each one is covered by the
regression suite (`tests/test_use_cases_v113.py`), so the examples stay valid as
the language evolves.

## 1. Data processing and analysis

PeaLang ships a dependency-light analysis surface that covers the work most
teams reach for pandas, dplyr, or SQL for. Records are ordinary lists of
dictionaries, so data can flow between PeaLang, JSON, CSV, Python, and databases
without an impedance mismatch.

| Task | PeaLang surface |
|---|---|
| Load CSV / JSON / JSONL files | `analysis.read_csv_file`, `analysis.read_json_file`, `analysis.read_jsonl_file` |
| Write CSV / JSON / JSONL files | `analysis.write_csv_file`, `analysis.write_json_file`, `analysis.write_jsonl_file` |
| Profile and describe | `analysis.profile`, `analysis.describe`, `analysis.summary`, `analysis.schema` |
| Clean data | `analysis.clean_missing`, `analysis.fillna`, `analysis.impute`, `analysis.dropna`, `analysis.drop_duplicates` |
| Transform columns | `analysis.add_column`, `analysis.cast`, `analysis.clip`, `analysis.normalize`, `analysis.zscore` |
| Aggregate | `analysis.group_by`, `analysis.value_counts`, `analysis.pivot`, `analysis.crosstab`, `analysis.melt` |
| Join and combine | `analysis.join` / `analysis.merge`, `analysis.concat`, `analysis.explode` |
| Time series | `analysis.shift` / `lag` / `lead`, `analysis.diff`, `analysis.pct_change`, `analysis.rolling_mean`, `analysis.ewm_mean` |
| Statistics | `analysis.correlation`, `analysis.corr_matrix`, `analysis.variance`, `analysis.skew`, `analysis.kurtosis`, `analysis.quantile`, `analysis.outliers` |
| SQL over records | `analysis.sql`, `analysis.sql_value` |
| Reports | `analysis.profile_markdown`, `analysis.profile_html`, `analysis.report_markdown`, `analysis.report_html`, `analysis.model_markdown`, `analysis.model_html`, `analysis.evaluation_markdown`, `analysis.evaluation_html`, `analysis.write_report_markdown`, `analysis.write_report_html`, `analysis.write_report_json` |

### SQL over in-memory records

`analysis.sql` loads records into an in-memory SQLite database and returns
records. This makes `GROUP BY`, window functions, CTEs, and `HAVING` available
without a database server, while keeping the output in the same record shape the
rest of the analysis namespace expects.

```pea
let orders = [
    {"customer": "c1", "month": "2026-01", "amount": 120},
    {"customer": "c1", "month": "2026-02", "amount": 80},
    {"customer": "c2", "month": "2026-01", "amount": 200}
]

print analysis.sql_value(orders, "SELECT SUM(amount) FROM data")

let monthly = analysis.sql(orders,
    "SELECT month, SUM(amount) AS revenue FROM data GROUP BY month ORDER BY month")
print monthly

let ranked = analysis.sql(orders,
    "SELECT customer, amount, RANK() OVER (PARTITION BY customer ORDER BY amount DESC) AS rnk FROM data")
```

Example: [`examples/use_cases/03_sql_analytics.pea`](../examples/use_cases/03_sql_analytics.pea)

### End-to-end pipeline

```pea
let raw = analysis.read_csv_file("sales.csv")
let clean = analysis.dropna(raw)
let enriched = analysis.add_column(clean, "revenue", function(row) {
    return row["units"] * row["price"]
})
let by_region = analysis.sql(enriched,
    "SELECT region, SUM(revenue) AS revenue FROM data GROUP BY region ORDER BY revenue DESC")
analysis.write_json_file("out/sales_report.json", by_region)
```

Examples:
- [`examples/use_cases/01_sales_pipeline.pea`](../examples/use_cases/01_sales_pipeline.pea)
- [`examples/use_cases/02_analytics_report.pea`](../examples/use_cases/02_analytics_report.pea)

## 2. Statistical analysis and modelling

The `stats` namespace covers the work data professionals normally reach for
NumPy, SciPy, scikit-learn, or gonum to do. It is pure PeaLang, so it runs with
no third-party packages.

| Task | PeaLang surface |
|---|---|
| Descriptive statistics | `stats.mean`, `stats.median`, `stats.std`, `stats.quantile`, `stats.describe` |
| Correlation | `stats.pearson`, `stats.spearman`, `stats.kendall` |
| Linear algebra | `stats.solve`, `stats.inverse`, `stats.matmul`, `stats.determinant` |
| Distributions | `stats.normal_cdf`, `stats.t_cdf`, `stats.chi2_cdf`, `stats.normal_ppf` |
| Hypothesis tests | `stats.t_test_ind`, `stats.welch_t_test`, `stats.chi_square_test`, `stats.anova_oneway` |
| Regression | `stats.linear_regression`, `stats.multiple_regression`, `stats.polyfit` |
| Segmentation | `stats.kmeans`, `stats.pca` |
| Resampling | `stats.bootstrap`, `stats.random_normal`, `stats.random_uniform` |
| Confidence intervals | `stats.confidence_interval_mean`, `stats.confidence_interval_proportion`, `stats.bootstrap_ci` |
| Effect size and power | `stats.cohens_d`, `stats.hedges_g`, `stats.power_t_test`, `stats.sample_size_t_test` |
| Multiple comparisons | `stats.adjust_p_values` (`"bonferroni"`, `"holm"`, `"bh"`) |
| Nonparametric tests | `stats.mann_whitney_u`, `stats.wilcoxon_signed_rank`, `stats.kruskal_wallis`, `stats.friedman_test` |
| Regression diagnostics | `stats.ols`, `stats.predict_ols`, `stats.variance_inflation_factors`, `stats.residual_diagnostics` |
| Time series | `stats.acf`, `stats.pacf`, `stats.ljung_box`, `stats.holt_winters`, `stats.seasonal_decompose`, `stats.adf_test` |
| Record wrappers | `analysis.regression_report`, `analysis.time_series_report` |
| Generalized linear models | `stats.logistic_regression`, `stats.poisson_regression`, `stats.glm`, `stats.predict_glm` |
| Regularized regression | `stats.ridge_regression`, `stats.lasso_regression`, `stats.elastic_net` |
| Survival analysis | `stats.kaplan_meier`, `stats.log_rank_test`, `stats.cox_proportional_hazards`, `stats.concordance_index` |
| ARIMA forecasting | `stats.arima`, `stats.auto_arima` |
| Modeling wrappers | `analysis.glm_report`, `analysis.survival_report`, `analysis.arima_report` |
| Propensity and balance | `stats.propensity_scores`, `stats.covariate_balance` |
| Weighting and matching | `stats.ipw_ate`, `stats.aipw_ate`, `stats.propensity_match` |
| Quasi-experimental designs | `stats.difference_in_differences`, `stats.instrumental_variables`, `stats.regression_discontinuity` |
| Causal wrappers | `analysis.causal_report`, `analysis.did_report`, `analysis.iv_report`, `analysis.rdd_report` |
| Resampling | `stats.train_test_split`, `stats.k_fold`, `stats.stratified_k_fold` |
| Classification metrics | `stats.accuracy_score`, `stats.balanced_accuracy`, `stats.precision_recall_fscore`, `stats.roc_auc`, `stats.log_loss` |
| Regression metrics | `stats.mean_squared_error`, `stats.root_mean_squared_error`, `stats.mean_absolute_error`, `stats.r2_score` |
| Feature preparation | `stats.polynomial_features`, `stats.label_encode`, `stats.standardize_features`, `stats.minmax_features` |
| Evaluation wrappers | `analysis.train_test_split`, `analysis.evaluate_classification`, `analysis.evaluate_regression`, `analysis.add_polynomial_features` |
| Trees and forests | `stats.decision_tree`, `stats.predict_tree`, `stats.random_forest`, `stats.predict_forest` |
| Tree importance | `stats.tree_feature_importance`, `stats.forest_feature_importance` |
| Gradient boosting | `stats.gradient_boosting`, `stats.predict_boosting`, `stats.boosting_feature_importance` |
| Model selection | `stats.cross_validate`, `stats.grid_search`, `stats.random_search` |
| Model interpretation | `stats.permutation_importance`, `stats.partial_dependence` |
| Class imbalance | `stats.class_balance`, `stats.smote`, `stats.random_oversample`, `stats.random_undersample` |
| Feature pipelines | `stats.fit_pipeline`, `stats.transform_pipeline`, `analysis.model_pipeline` |
| Target encoding | `stats.target_encode`, `stats.target_apply` |
| Model persistence | `stats.save_model`, `stats.load_model`, `stats.model_summary` |
| Date features | `stats.date_parts`, `stats.calendar_features`, `analysis.date_features` |
| Tree wrappers | `analysis.tree_report`, `analysis.forest_report`, `analysis.boosting_report` |

```pea
let treatment = [72, 84, 91, 88, 79, 95]
let control = [65, 70, 72, 68, 75, 71]

print stats.describe(treatment)
let test = stats.t_test_ind(treatment, control)
print test["p_value"]

let fit = stats.linear_regression([1, 2, 3, 4], [2.1, 3.9, 6.2, 7.8])
print fit["slope"]
print fit["r_squared"]

let segments = stats.kmeans(customers, 3, 100, 42)
print segments["labels"]
```

Inference goes beyond description: confidence intervals, effect sizes, power,
multiple-comparison correction, regression diagnostics, and forecasting.

```pea
let ci = stats.confidence_interval_mean(treatment)
print ci["low"]
print ci["high"]

print stats.cohens_d(treatment, control)
print stats.adjust_p_values([0.01, 0.04, 0.03], "bh")

let model = analysis.regression_report(rows, "y", ["a", "b"])
print model["table"]
print stats.predict_ols(model, [[1, 1]])

let report = analysis.time_series_report(rows, "demand", 6, 3)
print report["acf"]
print report["decomposition"]
```

Predictive modeling goes one step further: GLMs with inference, regularized
regression, survival curves, and ARIMA forecasts.

```pea
let logit = stats.logistic_regression(features, labels, ["x"])
print logit["table"]

let ridge = stats.ridge_regression(features, target, 0.5, ["a", "b"])
print ridge["coefficients"]

let km = stats.kaplan_meier(times, events)
print km["median_survival"]

let cox = stats.cox_proportional_hazards(features, times, events, ["x"])
print cox["hazard_ratios"]

let forecast = stats.arima(demand, 1, 1, 0, 4)
print forecast["forecast"]

let model = analysis.glm_report(rows, "outcome", ["x"])
let survival = analysis.survival_report(patients, "time", "event", ["age"])
let arima = analysis.arima_report(rows, "demand", null, 3, 3, null, 4)
```

Causal questions use propensity scores, weighting, matching, and
quasi-experimental designs:

```pea
let ps = stats.propensity_scores(features, treatment, ["x1", "x2"])
print ps["overlap"]
print stats.covariate_balance(features, treatment, ["x1", "x2"])["max_abs_smd"]

let ipw = stats.ipw_ate(features, treatment, outcome, 0.0, 0.95, 200, 0)
print ipw["ate"]
print ipw["ci_low"]
print ipw["ci_high"]

let matched = stats.propensity_match(features, treatment, outcome, 0.2, 1, false)
print matched["att"]

let did = stats.difference_in_differences(outcome, treated, post)
print did["att"]

let iv = stats.instrumental_variables(instruments, endogenous, outcome)
print iv["endogenous_coefficient"]

let rdd = stats.regression_discontinuity(running, outcome, 0.0, 0.8, 1)
print rdd["estimate"]

let effect = analysis.causal_report(rows, "t", "y", ["x1", "x2"])
let panel = analysis.did_report(panel_rows, "y", "treated", "post")
let instrumented = analysis.iv_report(rows, "y", "x", "z")
let discontinuity = analysis.rdd_report(rows, "y", "running", 0.0, 0.8, 1)
```

Evaluation closes the loop: split, cross-validate, score, and prepare features.

```pea
let split = stats.train_test_split(features, labels, 0.25, true, 7, labels)
print split["n_train"]
print split["n_test"]

let folds = stats.k_fold(len(rows), 5, true, 3)
for fold in folds {
    print fold["fold"] + ": " + str(fold["n_test"])
}

print stats.accuracy_score(actual, predicted)
print stats.precision_recall_fscore(actual, predicted)["f1"]
print stats.roc_auc(actual, scores)
print stats.log_loss(actual, probabilities)
print stats.r2_score(actual, predicted)
print stats.root_mean_squared_error(actual, predicted)

let expanded = stats.polynomial_features(features, 2)
print expanded["names"]
let scaled = stats.standardize_features(features)
print scaled["means"]

let holdout = analysis.train_test_split(rows, 0.25, 7, "label")
let quality = analysis.evaluate_classification(rows, "actual", "predicted", "score")
let errors = analysis.evaluate_regression(rows, "actual", "predicted")
let enriched = analysis.add_polynomial_features(rows, ["x1", "x2"], 2)
```

Tree models cover nonlinear targets and feature interactions:

```pea
let tree = stats.decision_tree(features, labels, "classification", 4, 2, 1)
print tree["classes"]
print stats.predict_tree(tree, new_features)["probabilities"]
print stats.tree_feature_importance(tree, ["x1", "x2"])

let forest = stats.random_forest(features, labels, "classification", 100, 6, 2, 1, "sqrt", true, 7)
print forest["oob_score"]
print stats.predict_forest(forest, new_features)["predicted"]
print stats.forest_feature_importance(forest, ["x1", "x2"])

let report = analysis.tree_report(rows, "label", ["x1", "x2"], "auto", 4)
let forest_report = analysis.forest_report(rows, "label", null, "auto", 100, 6, 2, 1, "sqrt", true, 7)
print report["train_accuracy"]
print forest_report["oob_score"]
```

Gradient boosting is the strongest general-purpose tabular model:

```pea
let boosted = stats.gradient_boosting(features, target, "regression", 100, 0.1, 3)
print stats.predict_boosting(boosted, new_features)["predicted"]

let classifier = stats.gradient_boosting(features, labels, "classification", 100, 0.1, 3)
print classifier["classes"]
print stats.predict_boosting(classifier, new_features)["probabilities"]

let stochastic = stats.gradient_boosting(features, target, "regression", 100, 0.1, 3, 2, 1, 0.8)
print stats.boosting_feature_importance(stochastic, ["x1", "x2"])

let boosted_report = analysis.boosting_report(rows, "label", ["x1", "x2"], "auto", 100, 0.1, 3)
print boosted_report["train_accuracy"]
print boosted_report["importance"][0]["feature"]
```

Model selection picks settings that generalize:

```pea
let cv = stats.cross_validate("boosting", features, target, "regression", {"n_estimators": 100, "learning_rate": 0.1}, 5, 0, "r2")
print cv["mean"]
print cv["std"]

let search = stats.grid_search("forest", features, labels, "classification", {"n_estimators": [50, 100], "max_depth": [2, 3]}, 5, 0, "accuracy")
print search["best_params"]
print search["best_score"]

let sampled = stats.random_search("boosting", features, target, "regression", {"n_estimators": [50, 100, 200], "learning_rate": [0.05, 0.1, 0.2]}, 6, 5, 7, "r2")
print sampled["best_params"]

let tuned = analysis.tune_model(rows, "label", ["x1", "x2"], "forest", "auto", {"n_estimators": [50, 100], "max_depth": [2, 3]}, 5, 0, "accuracy")
print tuned["best_model"]["importance"][0]["feature"]
```

Explain what the model learned with permutation importance and partial
dependence:

```pea
let report = stats.permutation_importance(model, features, target, "regression", 5, 0, "r2", ["x1", "x2"])
print report["importances"][0]["feature"]
print report["importances"][0]["mean"]

let curves = stats.partial_dependence(model, features, ["x1"], 10, "regression", ["x1", "x2"])["curves"]
print curves[0]["values"]
print curves[0]["average"]

let explained = analysis.interpret_report(rows, "y", ["x1", "x2"], "boosting", "regression", {"n_estimators": 100, "learning_rate": 0.1}, 5, 10, 0, "r2")
print explained["permutation_importance"][0]["feature"]
print explained["partial_dependence"][0]["average"]
```

Rare classes need resampling before fitting:

```pea
let balance = stats.class_balance(labels)
print balance["imbalance_ratio"]
print balance["counts"]

let synthetic = stats.smote(features, labels, 5, 7)
print synthetic["n"]
print synthetic["added"]

let over = stats.random_oversample(features, labels, 1)
let under = stats.random_undersample(features, labels, 1)
print over["n"]
print under["n"]

let balanced = analysis.balance_classes(rows, "label", ["x1", "x2"], "smote", 5, 0)
print balanced["after"]
let model = analysis.forest_report(balanced["rows"], "label", ["x1", "x2"], "classification")
print model["train_accuracy"]
```

Mixed and incomplete tables go through a pipeline before fitting:

```pea
let steps = [{"op": "impute", "method": "auto"}, {"op": "encode", "method": "onehot"}, {"op": "scale", "method": "standard"}]
let fitted = stats.fit_pipeline(steps, features, ["region", "plan", "spend"])
print fitted["names"]
print fitted["steps"][0]["missing"]
let new = stats.transform_pipeline(fitted, new_features)

let model = analysis.model_pipeline(rows, "churn", ["region", "plan", "spend"], null, "forest", "auto", {"n_estimators": 100})
print model["output_features"]
print model["train_accuracy"]
print analysis.predict_pipeline(model, new_rows)["predicted"]
```

Fitted models travel as versioned JSON, so a training run and a scoring job can
be separate scripts:

```pea
let model = analysis.model_pipeline(rows, "churn", ["region", "plan", "spend"], null, "forest", "auto", {"n_estimators": 100})
stats.save_model("churn_model.json", model)

// later, in another process
let loaded = stats.load_model("churn_model.json")
print stats.model_summary(loaded)["metrics"]["train_accuracy"]
print analysis.predict_pipeline(loaded, new_rows)["predicted"]
```

Date strings become numeric calendar columns, either as a matrix or directly in
records:

```pea
let matrix = stats.calendar_features(dates, ["year", "month", "weekday", "epoch_day"])
print matrix["names"]

let expanded = analysis.date_features(rows, "when", ["month", "weekday"], null, true)
print expanded[0]

// or as a pipeline step
let steps = [{"op": "impute", "method": "auto"}, {"op": "date", "parts": ["year", "month", "weekday"]}, {"op": "scale", "method": "standard"}]
let fitted = stats.fit_pipeline(steps, features, ["when", "spend"])
print fitted["names"]
```

High-cardinality categories can be target encoded, which keeps the column one
feature wide:

```pea
let encoder = stats.target_encode(stores, sales, 10.0, 1)
print encoder["prior"]
print stats.target_apply(encoder, ["alpha", "unseen"])

let steps = [
    {"op": "target", "columns": ["store"], "smoothing": 10.0},
    {"op": "encode", "method": "onehot"},
    {"op": "scale", "method": "standard"}
]
let fitted = stats.fit_pipeline(steps, features, ["store", "region", "spend"], target)
let model = analysis.model_pipeline(rows, "sales", ["store", "region"], steps, "tree", "regression", {"max_depth": 5})
print model["output_features"]
```

Pair `stats` with the pandas-class helpers in `analysis` for end-to-end work:

```pea
let clean = analysis.dropna(analysis.read_csv_file("customers.csv"))
let scored = analysis.qcut(clean, "spend", 4, ["low", "mid", "high", "top"])
let wide = analysis.pivot_table(scored, "region", "segment", "spend", "mean")
let profile = analysis.describe_all(wide)
```

Examples:
- [`examples/use_cases/06_statistical_analysis.pea`](../examples/use_cases/06_statistical_analysis.pea)
- [`examples/use_cases/07_matrix_regression.pea`](../examples/use_cases/07_matrix_regression.pea)
- [`examples/use_cases/08_segmentation_clustering.pea`](../examples/use_cases/08_segmentation_clustering.pea)
- [`examples/use_cases/09_inference_report.pea`](../examples/use_cases/09_inference_report.pea)
- [`examples/use_cases/10_forecasting_pipeline.pea`](../examples/use_cases/10_forecasting_pipeline.pea)
- [`examples/use_cases/11_glm_survival.pea`](../examples/use_cases/11_glm_survival.pea)
- [`examples/use_cases/12_arima_forecasting.pea`](../examples/use_cases/12_arima_forecasting.pea)
- [`examples/use_cases/13_causal_inference.pea`](../examples/use_cases/13_causal_inference.pea)
- [`examples/use_cases/14_model_evaluation.pea`](../examples/use_cases/14_model_evaluation.pea)
- [`examples/use_cases/15_trees_forests.pea`](../examples/use_cases/15_trees_forests.pea)
- [`examples/use_cases/16_gradient_boosting.pea`](../examples/use_cases/16_gradient_boosting.pea)
- [`examples/use_cases/17_model_selection.pea`](../examples/use_cases/17_model_selection.pea)
- [`examples/use_cases/18_model_interpretation.pea`](../examples/use_cases/18_model_interpretation.pea)
- [`examples/use_cases/19_class_imbalance.pea`](../examples/use_cases/19_class_imbalance.pea)
- [`examples/use_cases/20_feature_pipeline.pea`](../examples/use_cases/20_feature_pipeline.pea)
- [`examples/use_cases/21_model_persistence.pea`](../examples/use_cases/21_model_persistence.pea)
- [`examples/use_cases/22_date_features.pea`](../examples/use_cases/22_date_features.pea)
- [`examples/use_cases/23_target_encoding.pea`](../examples/use_cases/23_target_encoding.pea)
- [`examples/use_cases/24_reporting.pea`](../examples/use_cases/24_reporting.pea)
- [`examples/use_cases/25_notebook.pea`](../examples/use_cases/25_notebook.pea)
- [`examples/use_cases/26_documents.pea`](../examples/use_cases/26_documents.pea)
- [`examples/use_cases/27_visualization.pea`](../examples/use_cases/27_visualization.pea)
- [`examples/use_cases/28_validation.pea`](../examples/use_cases/28_validation.pea)
- [`examples/use_cases/29_conformance.pea`](../examples/use_cases/29_conformance.pea)
- [`examples/use_cases/30_advanced_ml.pea`](../examples/use_cases/30_advanced_ml.pea)
- [`examples/use_cases/31_sql_interop.pea`](../examples/use_cases/31_sql_interop.pea)
- [`examples/use_cases/32_robustness.pea`](../examples/use_cases/32_robustness.pea)
- [`examples/use_cases/33_devx.pea`](../examples/use_cases/33_devx.pea)
- [`examples/use_cases/34_timeseries.pea`](../examples/use_cases/34_timeseries.pea)
- [`examples/use_cases/35_clustering.pea`](../examples/use_cases/35_clustering.pea)
- [`examples/use_cases/36_formatter.pea`](../examples/use_cases/36_formatter.pea)

See [`docs/DATA_SCIENCE.md`](DATA_SCIENCE.md),
[`docs/STATISTICAL_INFERENCE.md`](STATISTICAL_INFERENCE.md),
[`docs/ADVANCED_MODELING.md`](ADVANCED_MODELING.md),
[`docs/CAUSAL_INFERENCE.md`](CAUSAL_INFERENCE.md),
[`docs/MODEL_EVALUATION.md`](MODEL_EVALUATION.md),
[`docs/TREE_MODELS.md`](TREE_MODELS.md), and
[`docs/GRADIENT_BOOSTING.md`](GRADIENT_BOOSTING.md), and
[`docs/MODEL_SELECTION.md`](MODEL_SELECTION.md), and
[`docs/MODEL_INTERPRETATION.md`](MODEL_INTERPRETATION.md), and
[`docs/CLASS_IMBALANCE.md`](CLASS_IMBALANCE.md),
[`docs/FEATURE_PIPELINES.md`](FEATURE_PIPELINES.md) and
[`docs/TARGET_ENCODING.md`](TARGET_ENCODING.md) and
[`docs/MODEL_PERSISTENCE.md`](MODEL_PERSISTENCE.md) and
[`docs/DATE_FEATURES.md`](DATE_FEATURES.md) for the full reference.

## 3. Polyglot delivery (Python, Go, TypeScript, Java)

PeaLang is a coordination layer. Complex programs can keep their data plane in
another runtime and use PeaLang for orchestration, rules, and reporting.

| Runtime | Integration |
|---|---|
| Python | `interop.call_python`, `interop.import_python` |
| Native libraries | `interop.load_library`, `interop.call_native` |
| Go | `interop.go_run`, `interop.go_available`, `interop.go_version`, `interop.generate_go` |
| Any process | `interop.run`, `interop.pipe_json` |
| HTTP services | `interop.http_get`, `interop.http_post`, `interop.json_rpc` |
| TypeScript client | `interop.generate_typescript` |
| Java client | `interop.generate_java` |
| Python stub | `interop.generate_python_stub` |

### Calling Python

```pea
let root = interop.call_python("math", "sqrt", 169)
print "python sqrt: " + str(root)
```

### Running Go programs

`interop.go_run` compiles and runs a Go program from source and returns captured
stdout/stderr. It is intended for small, auditable data transforms and does not
require a Go SDK dependency.

```pea
let result = interop.go_run("package main\n\nimport \"fmt\"\n\nfunc main() { fmt.Println(42) }")
print result["stdout"]
```

When Go is not installed, `go_run` returns `{"ok": false, "available": false}`
instead of raising, so pipelines can degrade gracefully:

```pea
if interop.go_available() {
    print "go: " + interop.go_version()
} else {
    print "go toolchain not installed"
}
```

### Generating typed clients

```pea
let go = interop.generate_go("http://127.0.0.1:8787")
let ts = interop.generate_typescript("http://127.0.0.1:8787")
let java = interop.generate_java("http://127.0.0.1:8787")
interop.write_text("client.go", go)
interop.write_text("client.ts", ts)
interop.write_text("Client.java", java)
```

Example: [`examples/use_cases/04_polyglot_bridge.pea`](../examples/use_cases/04_polyglot_bridge.pea)

## 4. Web applications and APIs

Build small services with routing, middleware, validation, and OpenAPI output,
then serve analysis results directly.

```pea
let app = web.app()
app.enable_cors("*")

function summary(req) {
    let groups = analysis.group_by(data, "team", "score", "mean")
    return web.json({"groups": groups})
}

app.get("/summary", summary)
```

Example: [`examples/use_cases/05_web_data_api.pea`](../examples/use_cases/05_web_data_api.pea)

## 5. Automation and ETL

Use `interop.walk`, `interop.read_text`, and the analysis IO helpers to build
repeatable file-based pipelines, then schedule them with the DAG orchestration
surface.

```pea
let files = interop.glob("inbox/*.json")
for file in files {
    let rows = analysis.read_json_file(file)
    let clean = analysis.dropna(rows)
    analysis.write_json_file("processed/" + interop.basename(file), clean)
}
```

## 6. Rules, workflows, and embedded extensions

PeaLang embeds in Python, FastAPI, Java, TypeScript, React, and browser/WASM
hosts. Hosts expose narrow capabilities and PeaLang programs call them through
`VMRuntime`/`PeaRuntime`, `std.testing`, and the permission model.

## Running the examples

```bash
pea run examples/use_cases/01_sales_pipeline.pea
pea run examples/use_cases/03_sql_analytics.pea
pea run examples/use_cases/04_polyglot_bridge.pea
```

Scaffold a new project from a related template:

```bash
pea init mydata --template data
pea init mybridge --template polyglot
```

## Adding your own use case

1. Put the program under `examples/use_cases/`.
2. Keep output deterministic so it can be asserted in a test.
3. Add a regression test in `tests/test_use_cases_v114.py` (or the matching version file).
4. Document the scenario in this file.
