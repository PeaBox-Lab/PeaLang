# Advanced Modeling: GLMs, Survival Analysis and ARIMA

PeaLang's modeling layer turns the inference primitives into predictive models:
generalized linear models, regularized regression, survival analysis, and ARIMA
forecasting. It is built on [`stats`](DATA_SCIENCE.md) and
[`inference`](STATISTICAL_INFERENCE.md), is pure Python, and has no third-party
dependencies.

Everything is exposed through:

- `stats.*` — global namespace, always available.
- `std.stats.*` — stable standard-library module.
- `analysis.*` — record-friendly wrappers for tables.

## What the layer covers

| Task | Python / Go equivalent | PeaLang |
|---|---|---|
| Logistic regression with inference | `statsmodels.Logit`, sklearn | `stats.logistic_regression` |
| Poisson regression | `statsmodels.GLM` | `stats.poisson_regression` |
| Gaussian GLM | `statsmodels.GLM` | `stats.glm(..., "gaussian")` |
| Predict from a GLM | `model.predict` | `stats.predict_glm` |
| Ridge regression | sklearn `Ridge` | `stats.ridge_regression` |
| Lasso regression | sklearn `Lasso` | `stats.lasso_regression` |
| Elastic net | sklearn `ElasticNet` | `stats.elastic_net` |
| Kaplan-Meier curve | lifelines, R `survfit` | `stats.kaplan_meier` |
| Log-rank test | lifelines, R `survdiff` | `stats.log_rank_test` |
| Cox proportional hazards | lifelines, R `coxph` | `stats.cox_proportional_hazards` |
| Concordance index | lifelines | `stats.concordance_index` |
| ARIMA | statsmodels, R `arima` | `stats.arima` |
| Order selection | `auto.arima`, `pmdarima` | `stats.auto_arima` |
| Record wrappers | pandas + statsmodels | `analysis.glm_report`, `analysis.survival_report`, `analysis.arima_report` |

## Generalized linear models

`stats.glm` fits a Gaussian, binomial, or Poisson model by iteratively
reweighted least squares. The result is an inferential table, not just
coefficients.

```pea
let x = [[1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12]]
let y = [0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1]

let model = stats.logistic_regression(x, y, ["x"])
print model["family"]              // "binomial"
print model["coefficients"]        // intercept, slope
print model["table"]               // term, coefficient, std_error, z, p_value, ci_low, ci_high
print model["pseudo_r_squared"]
print model["aic"]

let scored = stats.predict_glm(model, [[3], [9]])
print scored["predicted"]          // probabilities
print scored["linear"]             // log-odds
```

Poisson regression uses a log link:

```pea
let counts = [1, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10]
let poisson = stats.poisson_regression(x, counts, ["x"])
print poisson["coefficients"]
print poisson["p_values"]
print poisson["pseudo_r_squared"]
```

`stats.glm(features, target, "gaussian")` is available when you want the same
report shape for a continuous response. For binomial targets, `true`/`false`
records are accepted by `analysis.glm_report` and converted to `1`/`0`.

### Reading the table

- `coefficient` is on the link scale (log-odds for logistic, log-rate for
  Poisson).
- `z` and `p_value` test whether each coefficient differs from zero.
- `ci_low` / `ci_high` are confidence intervals on the link scale.
- `pseudo_r_squared` is `1 - deviance / null_deviance`.
- `aic` / `bic` compare models on the same response.
- `converged` reports whether IRLS reached tolerance.

Perfect separation in logistic regression produces very large coefficients and
standard errors; that is a property of maximum likelihood, not a bug. Add
regularization or collect overlapping data.

## Regularized regression

Ridge, lasso, and elastic net are fitted directly by penalized least squares and
coordinate descent.

```pea
let features = [[1, 0], [0, 1], [1, 1], [2, 2], [3, 1], [2, 3]]
let target = [2, 3, 5, 9, 10, 11]

let ridge = stats.ridge_regression(features, target, 0.5, ["a", "b"])
print ridge["coefficients"]
print ridge["r_squared"]

let lasso = stats.lasso_regression(features, target, 0.5, ["a", "b"])
print lasso["coefficients"]

let enet = stats.elastic_net(features, target, 0.5, 0.5, ["a", "b"])
print enet["coefficients"]
```

Larger `alpha` increases shrinkage. Lasso and elastic net can set coefficients
exactly to zero, which makes them useful for feature selection. The intercept is
not penalized.

## Survival analysis

### Kaplan-Meier

```pea
let times = [1, 2, 3, 4, 5]
let events = [1, 1, 0, 1, 0]       // 1 = event, 0 = censored

let km = stats.kaplan_meier(times, events)
print km["median_survival"]
print km["events"]
print km["censored"]
for row in km["timeline"] {
    print row["time"] + ": " + str(round(row["survival"], 3))
}
```

Each timeline row includes the number at risk, events, censored count, survival
probability, Greenwood standard error, and confidence bounds.

### Log-rank test

```pea
let result = stats.log_rank_test(
    [1, 2, 3, 4, 5], [1, 1, 1, 1, 1],
    [2, 3, 4, 5, 6], [1, 1, 1, 1, 1]
)
print result["chi2"]
print result["p_value"]
```

### Cox proportional hazards

```pea
let ages = [[0.1], [0.5], [1.0], [1.5], [2.0], [0.2], [0.7], [1.2], [1.7], [2.2]]
let times = [1, 2, 2, 3, 4, 5, 5, 6, 7, 8]
let events = [1, 1, 1, 1, 0, 1, 1, 0, 1, 1]

let cox = stats.cox_proportional_hazards(ages, times, events, ["age"])
print cox["coefficients"]
print cox["hazard_ratios"]
print cox["table"]
print cox["concordance"]
```

- `hazard_ratios` are `exp(coefficient)`: above 1 means higher hazard.
- `concordance` is Harrell's C; 0.5 is chance and 1.0 is perfect ranking.
- Ties are handled with the Breslow approximation.
- `stats.concordance_index(times, events, scores)` evaluates any risk score.

## ARIMA forecasting

`stats.arima` fits an ARIMA(p, d, q) model by iterative conditional least
squares on the differenced series, then integrates forecasts back to the
original scale.

```pea
let demand = [10, 20, 30, 11, 21, 31, 12, 22, 32, 13, 23, 33, 14, 24, 34, 15, 25, 35]

let fit = stats.arima(demand, 1, 1, 0, 2)   // p=1, d=1, q=0, 2 forecasts
print fit["order"]
print fit["ar"]
print fit["ma"]
print fit["intercept"]
print fit["aic"]
print fit["forecast"]
```

`stats.auto_arima` searches a small grid and selects by AIC. When `d` is `null`,
it differences until an ADF test is stationary (up to two differences).

```pea
let auto = stats.auto_arima(demand, 2, 2, 1, 2)   // max_p, max_q, d, periods
print auto["order"]
print auto["forecast"]
print auto["candidates"]                          // ranked by AIC
```

Pass `d` explicitly when the series is short or the ADF screen is ambiguous.
Seasonality can be handled by seasonal differencing before fitting, or by
including enough AR/MA terms.

## Record-friendly wrappers

```pea
let rows = [
    {"x": 1, "y": 0},
    {"x": 2, "y": 0},
    {"x": 3, "y": 1},
    {"x": 4, "y": 0},
    {"x": 5, "y": 1},
    {"x": 6, "y": 1}
]

let model = analysis.glm_report(rows, "y", ["x"])
print model["table"]

let patients = [
    {"time": 1, "event": 1, "age": 0.1},
    {"time": 2, "event": 1, "age": 0.5},
    {"time": 3, "event": 0, "age": 1.0},
    {"time": 4, "event": 1, "age": 1.5}
]

let survival = analysis.survival_report(patients, "time", "event", ["age"])
print survival["kaplan_meier"]["median_survival"]
print survival["cox"]["hazard_ratios"]

let forecast = analysis.arima_report(rows, "x", [1, 1, 0], 3, 3, null, 2)
print forecast["forecast"]
```

`analysis.glm_report` auto-selects numeric predictors when the feature list is
omitted, drops incomplete rows, and accepts boolean binomial targets.
`analysis.survival_report` always returns the Kaplan-Meier fit and adds Cox when
features are supplied. `analysis.arima_report` selects the order by AIC when
`order` is `null`.

## Runnable examples

- [`examples/use_cases/11_glm_survival.pea`](../examples/use_cases/11_glm_survival.pea)
- [`examples/use_cases/12_arima_forecasting.pea`](../examples/use_cases/12_arima_forecasting.pea)

```bash
pea run examples/use_cases/11_glm_survival.pea
pea run examples/use_cases/12_arima_forecasting.pea
```

## Accuracy and limitations

- GLM standard errors come from the observed information matrix; Gaussian models
  use the residual variance, binomial and Poisson models use unit dispersion.
- Logistic and Cox models can diverge under separation. Check `converged` and
  the size of the standard errors.
- Cox ties use the Breslow approximation, which is accurate when ties are few.
- ARIMA is fitted by conditional least squares, not full maximum likelihood.
  It is fast and dependency-free, and AIC/BIC comparisons remain useful within
  the same data.
- `auto_arima` searches `p` and `q` up to the supplied maxima; it is a practical
  model-selection helper, not an exhaustive search.
- Ridge/lasso/elastic net use raw feature scales. Standardize features first when
  they are on very different units and you want comparable penalties.
- Missing values (`null`) are dropped by the record wrappers; the list-based
  functions expect clean numeric inputs.
