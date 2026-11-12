# Causal Inference: Propensity Scores, DiD, IV and RDD

PeaLang's causal layer estimates treatment effects from observational and
quasi-experimental data. It is built on the inferential models in
[`stats`](DATA_SCIENCE.md) and [`modeling`](ADVANCED_MODELING.md), is pure
Python, and has no third-party dependencies.

Everything is exposed through:

- `stats.*` — global namespace, always available.
- `std.stats.*` — stable standard-library module.
- `analysis.*` — record-friendly wrappers for tables.

## What the layer covers

| Task | Python / R equivalent | PeaLang |
|---|---|---|
| Propensity scores | `statsmodels.Logit`, R `glm` | `stats.propensity_scores` |
| Covariate balance | `cobalt`, `MatchIt` summaries | `stats.covariate_balance` |
| IPW average effect | `statsmodels` IPW, R `ipw` | `stats.ipw_ate` |
| Doubly robust effect | `DoWhy`, `EconML`, `AIPW` | `stats.aipw_ate` |
| Propensity matching | `MatchIt`, `psmatching` | `stats.propensity_match` |
| Difference-in-differences | `statsmodels`, R `fixest` | `stats.difference_in_differences` |
| Instrumental variables | `linearmodels.IV2SLS`, R `ivreg` | `stats.instrumental_variables` |
| Regression discontinuity | R `rdrobust`, `rdd` | `stats.regression_discontinuity` |
| Record wrappers | pandas + statsmodels | `analysis.causal_report`, `analysis.did_report`, `analysis.iv_report`, `analysis.rdd_report` |

## Propensity scores and balance

`stats.propensity_scores(features, treatment, names, confidence)` fits a
logistic regression and returns fitted probabilities, logit scores, ATE and ATT
weights, and overlap diagnostics.

```pea
let x = [[1], [2], [3], [4], [5], [6], [7], [8]]
let t = [0, 1, 0, 1, 0, 1, 0, 1]

let ps = stats.propensity_scores(x, t, ["x"])
print ps["scores"]
print ps["weights_ate"]
print ps["overlap"]          // min, max, fraction_in_range
print ps["model"]["table"]   // logistic coefficient table
```

Balance is the first diagnostic to check. Standardized mean differences (SMDs)
below about `0.1` are conventionally treated as balanced.

```pea
let balance = stats.covariate_balance(x, t, ["x"])
print balance["table"]       // mean_treated, mean_control, smd
print balance["max_abs_smd"]

// after weighting
let weighted = stats.covariate_balance(x, t, ["x"], ps["weights_ate"])
print weighted["max_abs_weighted_smd"]
```

`covariate_balance` reports unweighted SMDs and, when weights are supplied,
weighted SMDs. Use the weighted columns to confirm that weighting actually
improved balance before trusting an effect estimate.

## Inverse-probability weighting

`stats.ipw_ate` estimates the population average effect (`ate`) and the effect
on the treated (`att`). Standard errors and intervals come from a
propensity-refitting bootstrap.

```pea
let ipw = stats.ipw_ate(x, t, y, 0.0, 0.95, 200, 0)
print ipw["ate"]
print ipw["att"]
print ipw["se"]
print ipw["ci_low"]
print ipw["ci_high"]
```

Positional arguments are `features`, `treatment`, `outcome`, `trim`,
`confidence`, `samples`, `seed`. `trim` winsorizes propensity scores away from
0 and 1 (for example `0.01` or `0.05`); `0` keeps them on the open interval.

Extreme weights are a warning sign. Check overlap and balance, and consider
trimming or a different design.

## Doubly robust estimation

`stats.aipw_ate` combines the propensity model with separate outcome
regressions for treated and control units. It is consistent when either model
is correctly specified.

```pea
let aipw = stats.aipw_ate(x, t, y, 0.0, 0.95, 200, 0)
print aipw["ate"]
print aipw["att"]
print aipw["ci_low"]
print aipw["ci_high"]
```

AIPW is usually preferred to plain IPW when the outcome is continuous and the
treated and control groups are large enough to fit separate regressions.

## Propensity-score matching

`stats.propensity_match` performs nearest-neighbour matching on the logit
propensity score and estimates the ATT.

```pea
let matched = stats.propensity_match(x, t, y, 0.2, 1, false)
print matched["att"]
print matched["n_matched"]
print matched["n_unmatched"]
for pair in matched["pairs"] {
    print pair["treated"] + " -> " + str(pair["controls"])
}
```

Arguments are `features`, `treatment`, `outcome`, `caliper`, `ratio`,
`replace`, `confidence`.

- `caliper` is in standard deviations of the logit propensity score. `0`
  disables the caliper; `0.2` is a common starting point.
- `ratio` is the number of controls matched to each treated unit.
- `replace` allows a control to be reused.

Matching discards units that cannot be matched, so always report
`n_matched` and `n_unmatched`.

## Difference-in-differences

`stats.difference_in_differences` fits

```text
outcome ~ treated + post + treated:post + covariates
```

and reports the interaction coefficient as the DiD estimate.

```pea
let outcome = [1, 2, 3, 4, 2, 3, 6, 7]
let treated = [0, 0, 0, 0, 1, 1, 1, 1]
let post    = [0, 0, 1, 1, 0, 0, 1, 1]

let did = stats.difference_in_differences(outcome, treated, post)
print did["att"]
print did["table"]
print did["r_squared"]
```

Positional arguments are `outcome`, `treated`, `post`, `covariates`, `names`,
`cluster`, `confidence`. Passing `cluster` switches to cluster-robust standard
errors; the cluster argument is a list of cluster identifiers.

```pea
let clustered = stats.difference_in_differences(
    outcome, treated, post, null, null, ["a", "a", "b", "b", "a", "a", "b", "b"]
)
print clustered["se"]
print clustered["n_clusters"]
```

The design assumes parallel trends: absent treatment, the treated and control
groups would have followed the same outcome path. Covariates can absorb
remaining differences, but they do not fix a violated parallel-trends
assumption.

## Instrumental variables

`stats.instrumental_variables` estimates a structural coefficient by two-stage
least squares with one endogenous regressor.

```pea
let z = [[1], [2], [3], [4], [5], [6], [7], [8], [9], [10]]
let x_end = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
let y = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21]

let iv = stats.instrumental_variables(z, x_end, y)
print iv["endogenous_coefficient"]
print iv["se"]
print iv["first_stage"]["f_statistic"]
print iv["first_stage"]["r_squared"]
```

Arguments are `instruments`, `endogenous`, `outcome`, `controls`, `names`,
`instrument_names`, `confidence`.

- `instruments` is a list of rows of excluded instruments.
- `endogenous` is a single endogenous regressor vector.
- `controls` is an optional list of rows of exogenous covariates.
- `first_stage.f_statistic` measures instrument relevance; a common rule of
  thumb is `F > 10`.
- When there is more than one instrument, `sargan` and `sargan_p_value` report
  an overidentification test. A small p-value suggests the instruments may not
  all be valid.

```pea
let iv2 = stats.instrumental_variables(
    [[z1, z2], ...], x_end, y, null, null, ["z1", "z2"]
)
print iv2["sargan"]
print iv2["sargan_p_value"]
```

The exclusion restriction cannot be tested with exactly one instrument. Argue
for it from the design, not from the fit.

## Regression discontinuity

`stats.regression_discontinuity` estimates a sharp jump at a cutoff using
separate local polynomials on each side.

```pea
let running = [-2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2]
let outcome = [0.1, 0.2, 0.3, 0.4, 1.6, 1.7, 1.8, 1.9]

let rdd = stats.regression_discontinuity(running, outcome, 0.0, null, 1)
print rdd["estimate"]
print rdd["ci_low"]
print rdd["ci_high"]
print rdd["n_left"]
print rdd["n_right"]
```

Arguments are `running`, `outcome`, `cutoff`, `bandwidth`, `degree`,
`confidence`.

- `bandwidth` restricts the estimation window in running-variable units;
  `null` uses the full range.
- `degree` is the polynomial order on each side.
- The estimate is the difference in fitted intercepts at the cutoff.

A sharp design assumes that units cannot precisely manipulate the running
variable around the cutoff. Check for bunching and covariate discontinuities
before interpreting the jump as causal.

## Record-friendly wrappers

```pea
let rows = [
    {"x": 1, "t": 0, "y": 1},
    {"x": 2, "t": 1, "y": 2},
    {"x": 3, "t": 0, "y": 3},
    {"x": 4, "t": 1, "y": 4}
]

let effect = analysis.causal_report(rows, "t", "y", ["x"])
print effect["method"]
print effect["ate"]
print effect["balance"]["max_abs_smd"]
print effect["weighted_balance"]["max_abs_weighted_smd"]
```

`analysis.causal_report(data, treatment, outcome, covariates, method, trim,
confidence, caliper, ratio)` supports `"ipw"`, `"aipw"`, and `"matching"`.
It drops incomplete rows, accepts boolean treatment columns, and returns both
unweighted and weighted balance.

```pea
let did = analysis.did_report(panel, "y", "treated", "post")
let iv = analysis.iv_report(rows, "y", "x", "z")
let rdd = analysis.rdd_report(rows, "y", "running", 0.0, 0.8, 1)
```

- `did_report(data, outcome, treated, post, covariates, cluster, confidence)`
- `iv_report(data, outcome, endogenous, instruments, controls, confidence)`
- `rdd_report(data, outcome, running, cutoff, bandwidth, degree, confidence)`

## Runnable example

- [`examples/use_cases/13_causal_inference.pea`](../examples/use_cases/13_causal_inference.pea)

```bash
pea run examples/use_cases/13_causal_inference.pea
```

The example builds a confounded observational sample, a two-period panel, an
instrumental-variables sample, and a regression-discontinuity sample, then
prints effects, intervals, balance, and diagnostics.

## Assumptions and limitations

- Causal estimates are only as credible as the identifying assumptions:
  no unmeasured confounding for propensity methods, parallel trends for DiD,
  instrument relevance and exclusion for IV, and no manipulation at the cutoff
  for RDD.
- Propensity methods require overlap. Inspect `overlap` and the score
  distribution; trim extreme weights when necessary.
- `ipw_ate` and `aipw_ate` use a bootstrap that refits the propensity model on
  each resample. The default is 200 samples and seed `0`; increase `samples`
  for publication-quality intervals.
- `aipw_ate` fits separate linear outcome models for treated and control units.
  With very small groups, the bootstrap may skip resamples that cannot be fit.
- Matching is nearest-neighbour on the logit propensity score. It is not a
  replacement for a full matching or weighting analysis when balance remains
  poor.
- DiD uses a linear two-period specification. For staggered adoption or many
  periods, use a dedicated panel estimator.
- IV standard errors assume homoskedasticity; the Sargan test assumes valid,
  homoskedastic errors. Cluster-robust IV is not yet exposed.
- RDD is a sharp design with local polynomials. It does not implement fuzzy
  designs, bias-corrected robust intervals, or automatic bandwidth selection.
- Missing values (`null`) are dropped by the record wrappers; the list-based
  functions expect clean numeric inputs.
