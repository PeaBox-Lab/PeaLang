# PeaLang for Data Science

PeaLang ships a dependency-free numerical and statistical toolkit so data work
does not require NumPy, SciPy, pandas, or gonum at runtime. The surface is
available two ways:

- `stats.*` — global namespace, always available.
- `std.stats.*` — stable standard-library module.

Records remain ordinary lists of dictionaries, so results flow directly into
`analysis`, `web`, SQL, JSON, and the polyglot bridges.

## Why it matters

| Need | Python | Go | PeaLang |
|---|---|---|---|
| Descriptive statistics | `numpy.mean`, `scipy.stats` | `gonum/stat` | `stats.mean`, `stats.describe` |
| Linear algebra | `numpy.linalg` | `gonum/mat` | `stats.solve`, `stats.inverse`, `stats.matmul` |
| Distributions | `scipy.stats` | `gonum/stat/distuv` | `stats.normal_cdf`, `stats.t_cdf`, `stats.chi2_cdf` |
| Hypothesis tests | `scipy.stats.ttest_ind` | manual | `stats.t_test_ind`, `stats.anova_oneway` |
| Regression | `numpy.polyfit`, `sklearn` | `gonum/stat` | `stats.linear_regression`, `stats.multiple_regression`, `stats.polyfit` |
| Inference | `scipy.stats`, `statsmodels` | `gonum/stat` | `stats.ols`, `stats.confidence_interval_mean`, `stats.t_test_ind` |
| Predictive models | `statsmodels`, `scikit-learn` | custom | `stats.glm`, `stats.ridge_regression`, `stats.cox_proportional_hazards` |
| Forecasting | `statsmodels`, `pmdarima` | custom | `stats.arima`, `stats.auto_arima` |
| Causal effects | `statsmodels`, `DoWhy`, `EconML` | custom | `stats.ipw_ate`, `stats.difference_in_differences`, `stats.instrumental_variables` |
| Model evaluation | `scikit-learn.metrics`, `model_selection` | custom | `stats.train_test_split`, `stats.k_fold`, `stats.roc_auc`, `stats.r2_score` |
| Clustering / PCA | `scikit-learn` | custom | `stats.kmeans`, `stats.pca` |
| Tabular transforms | pandas | custom | `analysis.*` |

Everything is pure Python: no wheels, no compiler, no native dependencies. It
works in constrained, embedded, browser-adjacent, and air-gapped environments.

## Descriptive statistics

```pea
let values = [72, 84, 91, 88, 79, 95, 67, 81]

print stats.mean(values)
print stats.median(values)
print stats.std(values)
print stats.variance(values)
print stats.quantile(values, 0.9)
print stats.iqr(values)
print stats.describe(values)
```

`describe` returns count, mean, std, min, q1, median, q3, max, iqr, skew, and
kurtosis in one record.

Correlation helpers accept two sequences and skip missing values pairwise:

```pea
print stats.pearson(xs, ys)
print stats.spearman(xs, ys)
print stats.kendall(xs, ys)
print stats.covariance(xs, ys)
```

## Scaling and transforms

```pea
print stats.zscore(values)
print stats.minmax_scale(values)
print stats.robust_scale(values)
print stats.winsorize(values, 0.05, 0.95)
print stats.cumsum(values)
print stats.diff(values, 1)
print stats.histogram(values, 10)
```

## Linear algebra

```pea
let a = [[3, 1], [1, 2]]
print stats.determinant(a)
print stats.inverse(a)
print stats.solve(a, [9, 8])
print stats.matmul([[1, 2], [3, 4]], [[5, 6], [7, 8]])
print stats.transpose(a)
print stats.identity(3)
print stats.trace(a)
print stats.norm([3, 4])
print stats.dot([1, 2, 3], [4, 5, 6])
```

`solve` uses partial-pivoted Gauss-Jordan elimination and raises a clear error
for singular matrices.

## Probability distributions

```pea
print stats.normal_pdf(0)
print stats.normal_cdf(0)
print stats.normal_ppf(0.975)
print stats.normal_interval(0.95)
print stats.uniform_cdf(0.5)
print stats.exponential_cdf(1)
print stats.binomial_pmf(2, 4, 0.5)
print stats.poisson_pmf(3, 2.5)
print stats.t_cdf(2.0, 10)
print stats.f_cdf(1.5, 3, 20)
print stats.chi2_cdf(3.84, 1)
```

## Hypothesis tests

```pea
let treatment = [72, 84, 91, 88, 79, 95]
let control = [65, 70, 72, 68, 75, 71]

let t = stats.t_test_ind(treatment, control)
print t["t"]
print t["df"]
print t["p_value"]

print stats.welch_t_test(treatment, control)
print stats.t_test_1samp(treatment, 80)
print stats.t_test_paired(treatment, control)
print stats.chi_square_test([[10, 20], [20, 10]])
print stats.anova_oneway(treatment, control)
```

Every test returns a record with the statistic, degrees of freedom, and
`p_value`.

## Inference, diagnostics, and time series

The inference layer answers the questions that follow descriptive statistics:
how precise an estimate is, how large the effect is, whether it survives
multiple comparisons, and what the series will do next.

```pea
let treatment = [72, 84, 91, 88, 79, 95, 67, 81]
let control = [65, 70, 72, 68, 75, 71, 69, 73]

// precision and effect size
print stats.confidence_interval_mean(treatment)
print stats.confidence_interval_proportion(30, 100)
print stats.cohens_d(treatment, control)
print stats.power_t_test(0.5, 64)
print stats.sample_size_t_test(0.5, 0.8)

// many tests at once
print stats.adjust_p_values([0.01, 0.04, 0.03], "bh")

// nonparametric alternatives
print stats.mann_whitney_u(treatment, control)
print stats.kruskal_wallis([1, 2, 3], [4, 5, 6], [7, 8, 9])
print stats.permutation_test(treatment, control, "mean", 2000, 42)

// regression with a full diagnostic table
let model = stats.ols([[1, 0], [0, 1], [1, 1], [2, 2]], [2, 3, 5, 9], ["a", "b"])
print model["table"]
print model["r_squared"]
print stats.variance_inflation_factors([[1, 0], [0, 1], [1, 1], [2, 2]], ["a", "b"])

// time series
print stats.acf([10, 20, 30, 11, 21, 31], 3)
print stats.ljung_box([10, 20, 30, 11, 21, 31], 3)
print stats.holt_winters([10, 20, 30, 11, 21, 31, 12, 22, 32], 3, 0.3, 0.1, 0.3, 2)
print stats.changepoint_cusum([1, 1, 1, 1, 10, 10, 10, 10], 0.5)
print stats.adf_test([1, 2, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11], 1)
```

Record-friendly wrappers:

```pea
let model = analysis.regression_report(rows, "y")
let report = analysis.time_series_report(rows, "demand", 6, 3)
```

See [`docs/STATISTICAL_INFERENCE.md`](STATISTICAL_INFERENCE.md) for the full
reference.

## Predictive modeling, survival analysis and ARIMA

The modeling layer turns inference into predictive models: generalized linear
models, regularized regression, survival analysis, and ARIMA forecasting.

```pea
// logistic regression with a full coefficient table
let x = [[1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12]]
let y = [0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1]
let logit = stats.logistic_regression(x, y, ["x"])
print logit["table"]
print logit["pseudo_r_squared"]
print stats.predict_glm(logit, [[3], [9]])["predicted"]

// Poisson regression
let counts = [1, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10]
print stats.poisson_regression(x, counts, ["x"])["coefficients"]

// ridge, lasso and elastic net
let features = [[1, 0], [0, 1], [1, 1], [2, 2], [3, 1], [2, 3]]
let target = [2, 3, 5, 9, 10, 11]
print stats.ridge_regression(features, target, 0.5, ["a", "b"])["coefficients"]
print stats.lasso_regression(features, target, 0.5, ["a", "b"])["coefficients"]
print stats.elastic_net(features, target, 0.5, 0.5, ["a", "b"])["coefficients"]

// survival analysis
let km = stats.kaplan_meier([1, 2, 3, 4, 5], [1, 1, 0, 1, 0])
print km["median_survival"]
print stats.log_rank_test([1, 2, 3, 4, 5], [1, 1, 1, 1, 1], [2, 3, 4, 5, 6], [1, 1, 1, 1, 1])["p_value"]
let cox = stats.cox_proportional_hazards([[0.1], [0.5], [1.0], [1.5], [2.0], [0.2], [0.7], [1.2], [1.7], [2.2]], [1, 2, 2, 3, 4, 5, 5, 6, 7, 8], [1, 1, 1, 1, 0, 1, 1, 0, 1, 1], ["x"])
print cox["hazard_ratios"]
print cox["concordance"]

// ARIMA
let fit = stats.arima([10, 20, 30, 11, 21, 31, 12, 22, 32, 13, 23, 33, 14, 24, 34, 15, 25, 35], 1, 1, 0, 2)
print fit["forecast"]
print stats.auto_arima([10, 20, 30, 11, 21, 31, 12, 22, 32, 13, 23, 33, 14, 24, 34, 15, 25, 35], 2, 2, 1, 2)["order"]
```

Record-friendly wrappers:

```pea
let model = analysis.glm_report(rows, "y", ["x"])
let survival = analysis.survival_report(patients, "time", "event", ["age"])
let forecast = analysis.arima_report(rows, "demand", [1, 1, 0], 3, 3, null, 2)
```

See [`docs/ADVANCED_MODELING.md`](ADVANCED_MODELING.md) for the full reference.

## Causal inference

The causal layer estimates treatment effects from observational and
quasi-experimental data: propensity scores, IPW/AIPW, matching,
difference-in-differences, instrumental variables, and regression
discontinuity.

```pea
// propensity scores and balance
let ps = stats.propensity_scores(features, treatment, ["x1", "x2"])
print ps["overlap"]
print stats.covariate_balance(features, treatment, ["x1", "x2"])["max_abs_smd"]

// inverse-probability weighting and doubly robust estimation
let ipw = stats.ipw_ate(features, treatment, outcome, 0.0, 0.95, 200, 0)
print ipw["ate"]
print ipw["ci_low"]
print ipw["ci_high"]
print stats.aipw_ate(features, treatment, outcome, 0.0, 0.95, 200, 0)["ate"]

// nearest-neighbour matching
let matched = stats.propensity_match(features, treatment, outcome, 0.2, 1, false)
print matched["att"]
print matched["n_matched"]

// difference-in-differences
let did = stats.difference_in_differences(outcome, treated, post)
print did["att"]
print did["table"]

// instrumental variables
let iv = stats.instrumental_variables(instruments, endogenous, outcome)
print iv["endogenous_coefficient"]
print iv["first_stage"]["f_statistic"]

// regression discontinuity
let rdd = stats.regression_discontinuity(running, outcome, 0.0, 0.8, 1)
print rdd["estimate"]
```

Record-friendly wrappers:

```pea
let effect = analysis.causal_report(rows, "t", "y", ["x1", "x2"])
let did = analysis.did_report(panel, "y", "treated", "post")
let iv = analysis.iv_report(rows, "y", "x", "z")
let rdd = analysis.rdd_report(rows, "y", "running", 0.0, 0.8, 1)
```

See [`docs/CAUSAL_INFERENCE.md`](CAUSAL_INFERENCE.md) for assumptions,
diagnostics, and the full reference.

## Model evaluation and feature preparation

The evaluation layer answers how well a model generalizes: train/test splits,
k-fold and stratified k-fold indices, classification and regression metrics,
ROC/AUC, probability scoring, calibration, and feature encoders and transforms.

```pea
// deterministic train/test split, optionally stratified by label
let split = stats.train_test_split(features, labels, 0.25, true, 7, labels)
print split["n_train"]
print split["n_test"]

// fold indices for a manual cross-validation loop
let folds = stats.k_fold(len(rows), 5, true, 3)
let stratified = stats.stratified_k_fold(labels, 5, true, 3)

// classification metrics
print stats.accuracy_score(actual, predicted)
print stats.balanced_accuracy(actual, predicted)
print stats.precision_recall_fscore(actual, predicted)["per_class"]
print stats.roc_auc(actual, scores)
print stats.log_loss(actual, probabilities)
print stats.calibration_curve(actual, probabilities, 10)["table"]

// regression metrics
print stats.mean_squared_error(actual, predicted)
print stats.root_mean_squared_error(actual, predicted)
print stats.r2_score(actual, predicted)

// feature preparation
print stats.polynomial_features([[2, 3]], 2)["names"]
print stats.label_encode(["red", "green", "red"])["codes"]
let scaled = stats.standardize_features(features)
print stats.standardize_transform(new_features, scaled["means"], scaled["scales"])
```

Record-friendly wrappers:

```pea
let split = analysis.train_test_split(rows, 0.25, 7, "label")
let quality = analysis.evaluate_classification(rows, "actual", "predicted", "score")
let errors = analysis.evaluate_regression(rows, "actual", "predicted")
let expanded = analysis.add_polynomial_features(rows, ["x1", "x2"], 2)
```

See [`docs/MODEL_EVALUATION.md`](MODEL_EVALUATION.md) for the full reference.

## Regression and modelling

```pea
let x = [1, 2, 3, 4, 5]
let y = [2.1, 3.9, 6.2, 7.8, 10.1]

let fit = stats.linear_regression(x, y)
print fit["slope"]
print fit["intercept"]
print fit["r_squared"]

let multi = stats.multiple_regression([[1, 0], [0, 1], [1, 1]], [2, 3, 5])
print multi["coefficients"]

let curve = stats.polyfit(x, [1, 4, 9, 16, 25], 2)
print stats.polyval(curve, 6)
```

## Clustering and dimensionality reduction

```pea
let customers = [
    {"spend": 10, "visits": 2},
    {"spend": 12, "visits": 3},
    {"spend": 80, "visits": 12},
    {"spend": 85, "visits": 11}
]

let km = stats.kmeans(customers, 2, 100, 42)
print km["labels"]
print km["centers"]
print km["inertia"]

let pc = stats.pca(customers, 2)
print pc["explained_variance_ratio"]
print pc["projected"]
```

`kmeans` uses k-means++ seeding. `pca` uses power iteration over the covariance
matrix, so no third-party linear algebra is required.

## Sampling and resampling

```pea
print stats.random_uniform(5, 0, 1, 42)
print stats.random_normal(5, 0, 1, 42)
print stats.random_binomial(5, 10, 0.5, 42)
print stats.random_poisson(5, 2.0, 42)

let boot = stats.bootstrap([1, 2, 3, 4, 5], "mean", 1000, 42)
print boot["ci_low"]
print boot["ci_high"]
```

Pass an explicit seed whenever you need reproducible output.

## Tabular workflows

`stats` handles the math; `analysis` handles the frame. They compose directly.

```pea
let rows = analysis.read_csv_file("measurements.csv")
let clean = analysis.dropna(rows)

// pandas-class helpers
let scored = analysis.qcut(clean, "value", 4, ["low", "mid", "high", "top"])
let smooth = analysis.rolling_median(scored, "value", 5)
let summary = analysis.describe_all(smooth)
let missing = analysis.missing_summary(clean)
let grouped = analysis.group_by_multi(clean, ["region", "segment"], "value", "mean")
let wide = analysis.pivot_table(clean, "region", "segment", "value", "mean")

analysis.write_json_file("summary.json", [summary])
```

### pandas-class additions

| pandas | PeaLang |
|---|---|
| `pd.qcut` | `analysis.qcut` |
| `df.rolling().sum/min/max/median/var()` | `analysis.rolling_sum/min/max/median/var` |
| `df.expanding().std/var/median()` | `analysis.expanding_std/var/median` |
| `Series.interpolate` | `analysis.interpolate` |
| `pd.factorize` | `analysis.factorize` |
| `df.mask` | `analysis.mask` |
| `df.select_dtypes` | `analysis.select_dtypes` |
| `df.info()` | `analysis.info` |
| `df.memory_usage()` | `analysis.memory_usage` |
| `pd.pivot_table` | `analysis.pivot_table` |
| `df.reset_index` / `set_index` | `analysis.reset_index` / `set_index` |
| `df.agg` | `analysis.agg` |
| `df.transform` | `analysis.transform` |
| `groupby([...]).agg(...)` | `analysis.group_by_multi` |
| `merge` on multiple keys | `analysis.merge_multi` |
| `df.describe()` for all columns | `analysis.describe_all` |
| `df.isna().sum()` | `analysis.missing_summary` |
| winsorizing | `analysis.winsorize` |
| `spearman` correlation | `analysis.corr_spearman` |
| `pd.date_range` | `analysis.date_range` |

## Runnable examples

- `examples/use_cases/06_statistical_analysis.pea`
- `examples/use_cases/07_matrix_regression.pea`
- `examples/use_cases/08_segmentation_clustering.pea`
- `examples/use_cases/09_inference_report.pea`
- `examples/use_cases/10_forecasting_pipeline.pea`
- `examples/use_cases/11_glm_survival.pea`
- `examples/use_cases/12_arima_forecasting.pea`
- `examples/use_cases/13_causal_inference.pea`
- `examples/use_cases/14_model_evaluation.pea`

Run them with:

```bash
pea run examples/use_cases/06_statistical_analysis.pea
pea run examples/use_cases/07_matrix_regression.pea
pea run examples/use_cases/08_segmentation_clustering.pea
pea run examples/use_cases/09_inference_report.pea
pea run examples/use_cases/10_forecasting_pipeline.pea
pea run examples/use_cases/11_glm_survival.pea
pea run examples/use_cases/12_arima_forecasting.pea
pea run examples/use_cases/13_causal_inference.pea
pea run examples/use_cases/14_model_evaluation.pea
```

## Choosing the right namespace

- Use `stats` for numbers: vectors, matrices, distributions, tests, models.
- Use `analysis` for tables: cleaning, grouping, pivots, IO, reports.
- Use `analysis.sql` when a query is clearer than a chain of transforms.
- Use `interop` when another runtime already owns the data plane.

## Accuracy notes

- `variance` and `std` are sample statistics by default; pass `false` for the
  population form.
- `normal_ppf` uses Acklam's rational approximation with a Halley refinement
  step.
- `t_cdf`, `f_cdf`, and `chi2_cdf` use regularized incomplete beta/gamma
  functions implemented in the standard library. `t_ppf`, `chi2_ppf`, and
  `f_ppf` invert them by bisection.
- `kmeans` and `pca` are deterministic when a seed is supplied.
- Missing values (`null`) are skipped pairwise by correlation and test helpers;
  `analysis.regression_report` drops incomplete rows.
- `ols` uses normal equations and reports variance inflation factors so
  collinearity can be checked before trusting coefficients.
- `glm` fits by iteratively reweighted least squares; Gaussian models use the
  residual variance and binomial/Poisson models use unit dispersion.
- `cox_proportional_hazards` uses the Breslow approximation for tied event
  times; `arima` uses conditional least squares rather than full maximum
  likelihood.
- Causal estimates rely on design assumptions: no unmeasured confounding for
  propensity methods, parallel trends for DiD, instrument relevance and
  exclusion for IV, and no manipulation at the cutoff for RDD. Inspect overlap
  and balance before trusting an effect.
- `ipw_ate` and `aipw_ate` use a propensity-refitting bootstrap (default 200
  samples, seed `0`); increase `samples` for publication-quality intervals.
- `train_test_split` shuffles rows by default; use `shuffle = false` or split
  by time for ordered data. `stratified_k_fold` raises when a class has fewer
  than `k` samples.
- `roc_auc` is tie-aware and uses mid-ranks. `log_loss` clips probabilities with
  `epsilon` before taking logs.
- Cross-validation is a loop over fold indices; PeaLang functions are not
  passed to native code as callables, so there is no single-call estimator
  protocol.
- Fit feature scalers on training data only, then apply the learned `means` /
  `scales` or `mins` / `ranges` to validation and test rows.
