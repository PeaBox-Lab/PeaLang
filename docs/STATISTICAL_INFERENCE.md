# Statistical Inference and Time Series

PeaLang's inference layer sits on top of [`stats`](DATA_SCIENCE.md) and answers
the questions that follow descriptive statistics: *how precise is this estimate,
how large is the effect, is it significant after multiple comparisons, and what
will happen next?*

Everything is pure Python, dependency-free, and exposed through the same two
surfaces:

- `stats.*` — global namespace, always available.
- `std.stats.*` — stable standard-library module.

Results are ordinary records, so they flow into `analysis`, JSON, reports, and
the polyglot bridges without conversion.

## What the layer covers

| Question | Python / Go equivalent | PeaLang |
|---|---|---|
| How precise is the mean? | `scipy.stats.t.interval` | `stats.confidence_interval_mean` |
| How precise is a proportion? | `statsmodels.proportion_confint` | `stats.confidence_interval_proportion` |
| Difference of two means | `scipy.stats.ttest_ind` + CI | `stats.confidence_interval_diff_means` |
| Effect size | `scipy` / manual | `stats.cohens_d`, `stats.hedges_g`, `stats.eta_squared` |
| Power and sample size | `statsmodels.stats.power` | `stats.power_t_test`, `stats.sample_size_t_test` |
| Multiple comparisons | `statsmodels.multipletests` | `stats.adjust_p_values` |
| Nonparametric tests | `scipy.stats.mannwhitneyu` | `stats.mann_whitney_u`, `stats.wilcoxon_signed_rank`, `stats.kruskal_wallis`, `stats.friedman_test`, `stats.sign_test` |
| Regression table | `statsmodels.OLS` | `stats.ols`, `analysis.regression_report` |
| Regression diagnostics | `statsmodels` | `stats.predict_ols`, `stats.variance_inflation_factors`, `stats.residual_diagnostics` |
| ACF / PACF / Ljung-Box | `statsmodels.tsa` | `stats.acf`, `stats.pacf`, `stats.ljung_box` |
| Smoothing and forecasts | `statsmodels` / `prophet` | `stats.holt_linear`, `stats.holt_winters`, `stats.simple_exponential_smoothing` |
| Seasonal decomposition | `statsmodels.tsa.seasonal` | `stats.seasonal_decompose` |
| Change points | `ruptures` | `stats.changepoint_cusum` |
| Stationarity | `statsmodels.tsa.stattools.adfuller` | `stats.adf_test` |

## Estimation and confidence intervals

```pea
let treatment = [72, 84, 91, 88, 79, 95, 67, 81]

let mean_ci = stats.confidence_interval_mean(treatment)
print mean_ci["estimate"]
print mean_ci["low"]
print mean_ci["high"]
print mean_ci["df"]

print stats.confidence_interval_proportion(30, 100)
print stats.confidence_interval_diff_means(treatment, [65, 70, 72, 68, 75, 71])
print stats.margin_of_error(treatment)
print stats.standard_error(treatment)
print stats.bootstrap_ci(treatment, "median", 1000, 0.95, 42)
```

`confidence_interval_mean` uses the Student-t distribution, so small samples are
handled correctly. `confidence_interval_proportion` uses the Wilson score
interval, which stays inside `[0, 1]` and behaves well near 0% and 100%.
`bootstrap_ci` is a percentile bootstrap and accepts `"mean"`, `"median"`, or
`"std"` as the statistic.

## Effect size and power

Significance answers "is there an effect"; effect size answers "does it
matter".

```pea
print stats.cohens_d(treatment, control)     // pooled standard deviation
print stats.hedges_g(treatment, control)     // small-sample correction
print stats.eta_squared(group_a, group_b)    // variance explained

print stats.power_t_test(0.5, 64)            // power for n = 64 per group
print stats.sample_size_t_test(0.5, 0.8)     // n needed for 80% power
```

`power_t_test` and `sample_size_t_test` use the normal approximation, which is
accurate for planning at moderate-to-large samples.

## Multiple comparisons

Running many tests inflates false positives. Adjust p-values before deciding
what is significant.

```pea
let raw = [0.01, 0.04, 0.03]
print stats.adjust_p_values(raw, "bh")           // Benjamini-Hochberg FDR
print stats.adjust_p_values(raw, "bonferroni")   // family-wise error
print stats.adjust_p_values(raw, "holm")         // step-down family-wise
```

Each result record contains the original `p`, the `adjusted` value, and a
`rejected` flag at the chosen `alpha` (default `0.05`).

## Parametric and nonparametric tests

```pea
print stats.z_test_1samp([1, 2, 3, 4, 5], 3, 1)
print stats.proportion_test(30, 100, 0.5)
print stats.z_test_proportions(30, 100, 40, 100)
print stats.fisher_exact(10, 20, 20, 10)
print stats.chi_square_goodness_of_fit([10, 20, 30])

print stats.mann_whitney_u([1, 2, 3, 4, 5], [2, 3, 4, 5, 6])
print stats.wilcoxon_signed_rank([1, 2, 3, 4, 5], [2, 3, 4, 5, 6])
print stats.kruskal_wallis([1, 2, 3], [4, 5, 6], [7, 8, 9])
print stats.friedman_test([1, 2, 3], [2, 4, 5], [3, 5, 7])
print stats.sign_test([1, 2, 3, 4], [0, 1, 2, 1])
```

Use the nonparametric family when data are ordinal, clearly non-normal, or
contain influential outliers. `mann_whitney_u`, `wilcoxon_signed_rank`, and
`kruskal_wallis` include tie corrections.

## Normality and permutation tests

```pea
print stats.jarque_bera([1, 2, 3, 4, 5, 6, 7, 8])
print stats.normality_test([1, 2, 3, 4, 5, 6, 7, 8])

let perm = stats.permutation_test(group_a, group_b, "mean", 2000, 42)
print perm["p_value"]
```

`permutation_test` resamples group labels, so it makes no distributional
assumption. Pass a seed for reproducible p-values.

## Ordinary least squares with diagnostics

`stats.ols` returns a complete regression report: coefficient table, standard
errors, t-statistics, p-values, confidence intervals, R², adjusted R², the
overall F-test, AIC/BIC, Durbin-Watson, residuals, and the covariance matrix.

```pea
let features = [[1, 0], [0, 1], [1, 1], [2, 2], [3, 1], [2, 3]]
let target = [2, 3, 5, 9, 10, 11]

let model = stats.ols(features, target, ["a", "b"])
print model["r_squared"]
print model["adj_r_squared"]
print model["f_statistic"]
print model["durbin_watson"]

for term in model["table"] {
    print term["term"] + ": p=" + str(round(term["p_value"], 4))
}

print stats.variance_inflation_factors(features, ["a", "b"])
print stats.predict_ols(model, [[1, 1], [2, 2]])
print stats.residual_diagnostics(model["residuals"])
```

On records, use the friendlier wrapper. It auto-selects numeric predictors when
the feature list is omitted and skips incomplete rows.

```pea
let rows = [
    {"a": 1, "b": 0, "y": 2},
    {"a": 0, "b": 1, "y": 3},
    {"a": 1, "b": 1, "y": 5},
    {"a": 2, "b": 2, "y": 9}
]

let model = analysis.regression_report(rows, "y", ["a", "b"])
print model["table"]
print model["r_squared"]
```

Diagnostics to check:

- `variance_inflation_factors` above ~5 suggest multicollinearity.
- `residual_diagnostics()["normality_p"]` below `0.05` suggests non-normal errors.
- `durbin_watson` near `2` indicates little autocorrelation; near `0` or `4`
  indicates strong positive or negative autocorrelation.
- `predict_ols` returns prediction intervals, not just point forecasts.

## Time series

### Autocorrelation and stationarity

```pea
let demand = [10, 20, 30, 11, 21, 31, 12, 22, 32, 13, 23, 33]

print stats.acf(demand, 6)
print stats.pacf(demand, 6)
print stats.ljung_box(demand, 6)

print stats.difference_series(demand, 1)        // regular differencing
print stats.difference_series(demand, 1, 3)     // seasonal differencing (m = 3)

let adf = stats.adf_test([1, 2, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11], 1)
print adf["statistic"]
print adf["stationary"]
```

`acf` uses the biased estimator with lag 0 fixed at `1`. `pacf` uses the
Durbin-Levinson recursion. `ljung_box` tests whether any of the first `h`
autocorrelations are non-zero. `adf_test` reports the unit-root t-statistic
against MacKinnon critical values; `stationary` is true when the statistic is
below the 5% critical value.

### Smoothing and forecasting

```pea
print stats.moving_average(demand, 3)
print stats.simple_exponential_smoothing(demand, 0.3, 4)
print stats.holt_linear(demand, 0.3, 0.1, 4)
print stats.holt_winters(demand, 3, 0.3, 0.1, 0.3, 4)
```

- `simple_exponential_smoothing` is level-only, for series without trend.
- `holt_linear` adds a trend component.
- `holt_winters` adds an additive seasonal component and needs at least two
  full seasonal periods.

Each returns the fitted values and a `forecast` list for the requested number of
periods.

### Decomposition and change points

```pea
let parts = stats.seasonal_decompose(demand, 3)
print parts["trend"]
print parts["seasonal"]
print parts["residual"]
print parts["pattern"]

let shift = [1, 1, 1, 1, 10, 10, 10, 10]
print stats.changepoint_cusum(shift, 0.5)
```

`seasonal_decompose` is additive and centers the seasonal pattern to sum to
zero. `changepoint_cusum` standardizes the series, accumulates deviations, and
reports the index of the largest absolute CUSUM value once it crosses the
threshold.

### Record-friendly wrapper

```pea
let rows = [
    {"month": "2026-01", "demand": 10},
    {"month": "2026-02", "demand": 20},
    {"month": "2026-03", "demand": 30},
    {"month": "2026-04", "demand": 11},
    {"month": "2026-05", "demand": 21},
    {"month": "2026-06", "demand": 31}
]

let report = analysis.time_series_report(rows, "demand", 3, 3)
print report["acf"]
print report["ljung_box"]
print report["decomposition"]
```

`analysis.time_series_report` returns the series length, ACF, PACF, Ljung-Box
result (when there are enough observations), and a seasonal decomposition when a
period is supplied and the series is long enough.

## Runnable examples

- [`examples/use_cases/09_inference_report.pea`](../examples/use_cases/09_inference_report.pea)
- [`examples/use_cases/10_forecasting_pipeline.pea`](../examples/use_cases/10_forecasting_pipeline.pea)

```bash
pea run examples/use_cases/09_inference_report.pea
pea run examples/use_cases/10_forecasting_pipeline.pea
```

## Accuracy and limitations

- Inverse t, chi-square, and F distributions use bisection on the regularized
  incomplete beta/gamma CDFs, so they are accurate to well below display
  precision.
- `power_t_test` and `sample_size_t_test` use the normal approximation; they are
  planning tools, not exact small-sample calculations.
- `ols` uses normal equations with a partial-pivoted inverse. It is stable for
  ordinary-sized problems; extremely collinear designs can still lose precision,
  which is why `variance_inflation_factors` is provided.
- `adf_test` uses a constant term and a fixed lag order. It is a fast
  stationarity screen, not a substitute for full model selection.
- `holt_winters` is additive. Multiplicative seasonality should be log-transformed
  first.
- Missing values (`null`) are skipped pairwise by test helpers; `regression_report`
  drops incomplete rows.

For predictive models built on these primitives — GLMs, regularized regression,
survival analysis, and ARIMA — see
[`docs/ADVANCED_MODELING.md`](ADVANCED_MODELING.md).
