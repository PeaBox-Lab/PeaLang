"""Causal inference: propensity scores, weighting, matching, DiD, IV and RDD.

This module is the causal layer above :mod:`pealang.modeling`. It provides
propensity-score estimation, inverse-probability weighting, augmented IPW,
nearest-neighbour matching, covariate balance diagnostics, two-period
difference-in-differences, two-stage least squares, and local-polynomial
regression discontinuity. Everything is pure Python and dependency-free.
"""

from __future__ import annotations

import math
import random
from typing import Any, Iterable, Sequence

from .numerics import (
    mean,
    std,
    variance,
    normal_ppf,
    t_cdf,
    t_ppf,
    chi2_cdf,
    f_cdf,
    dot,
    inverse,
    matmul,
    transpose,
)
from .modeling import logistic_regression


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _rows(features: Any) -> list[list[float]]:
    rows = [[float(value) for value in row] for row in (features or [])]
    if not rows:
        raise ValueError("features are required")
    width = len(rows[0])
    if width == 0 or any(len(row) != width for row in rows):
        raise ValueError("feature rows must be non-empty and equal length")
    return rows


def _treatment(values: Iterable[Any]) -> list[int]:
    out: list[int] = []
    for value in values or []:
        if isinstance(value, bool):
            out.append(1 if value else 0)
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError("treatment must be boolean or 0/1") from None
        if number not in (0.0, 1.0):
            raise ValueError("treatment must be boolean or 0/1")
        out.append(int(number))
    return out


def _outcome(values: Iterable[Any]) -> list[float]:
    return [float(value) for value in (values or [])]


def _labels(names: Sequence[str] | None, width: int, prefix: str = "x") -> list[str]:
    if names is None:
        return [prefix + str(i + 1) for i in range(width)]
    labels = list(names)
    if len(labels) != width:
        raise ValueError("names length must match the number of features")
    return labels


def _ols(design: list[list[float]], target: list[float]):
    """Return coefficients, inverse Gram matrix, fitted values and residuals."""
    width = len(design[0])
    xtx = matmul(transpose(design), design)
    try:
        gram_inv = inverse(xtx)
    except ValueError as exc:
        raise ValueError("design matrix is singular or collinear: " + str(exc)) from exc
    xty = [dot(column, target) for column in transpose(design)]
    beta = [dot(row, xty) for row in gram_inv]
    fitted = [dot(row, beta) for row in design]
    residuals = [actual - predicted for actual, predicted in zip(target, fitted)]
    return beta, gram_inv, fitted, residuals


def _covariance(gram_inv: list[list[float]], residuals: list[float],
                df: int) -> list[list[float]]:
    rss = sum(value * value for value in residuals)
    sigma2 = rss / df if df > 0 else 0.0
    return [[sigma2 * value for value in row] for row in gram_inv]


def _matrix_product(a: list[list[float]], b: list[list[float]],
                    c: list[list[float]]) -> list[list[float]]:
    return matmul(matmul(a, b), c)


def _critical(confidence: float, df: int | None = None) -> float:
    confidence = float(confidence)
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if df is None:
        return normal_ppf(1.0 - (1.0 - confidence) / 2.0)
    return t_ppf(1.0 - (1.0 - confidence) / 2.0, max(1, int(df)))


def _quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("quantile requires at least one value")
    ordered = sorted(values)
    position = (len(ordered) - 1) * min(max(float(q), 0.0), 1.0)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _interval(estimate: float, se: float | None, confidence: float,
              df: int | None = None) -> dict[str, Any]:
    if se is None:
        return {"se": None, "ci_low": None, "ci_high": None}
    critical = _critical(confidence, df)
    return {
        "se": se,
        "ci_low": estimate - critical * se,
        "ci_high": estimate + critical * se,
    }


# ---------------------------------------------------------------------------
# Propensity scores
# ---------------------------------------------------------------------------

def propensity_scores(features: Any, treatment: Iterable[Any],
                      names: Sequence[str] | None = None,
                      confidence: float = 0.95) -> dict[str, Any]:
    """Estimate propensity scores with a logistic regression.

    ``features`` is a list of covariate rows and ``treatment`` is a 0/1 (or
    boolean) vector. The result includes fitted probabilities, logit scores,
    inverse-probability weights for the ATE and ATT, and overlap diagnostics.
    """
    rows = _rows(features)
    treated = _treatment(treatment)
    if len(rows) != len(treated):
        raise ValueError("features and treatment lengths must match")
    if len(set(treated)) < 2:
        raise ValueError("treatment must contain both treated and control units")
    labels = _labels(names, len(rows[0]))
    model = logistic_regression(rows, treated, labels, confidence)
    scores = [min(max(value, 1e-9), 1.0 - 1e-9) for value in model["fitted"]]
    linear = [dot([1.0] + row, model["coefficients"]) for row in rows]
    weights_ate = [
        1.0 / scores[i] if treated[i] else 1.0 / (1.0 - scores[i])
        for i in range(len(rows))
    ]
    weights_att = [
        1.0 if treated[i] else scores[i] / (1.0 - scores[i])
        for i in range(len(rows))
    ]
    inside = sum(1 for value in scores if 0.1 <= value <= 0.9)
    return {
        "scores": scores,
        "logit_scores": linear,
        "weights_ate": weights_ate,
        "weights_att": weights_att,
        "treated": treated,
        "n": len(rows),
        "treated_count": sum(treated),
        "control_count": len(treated) - sum(treated),
        "overlap": {
            "min": min(scores),
            "max": max(scores),
            "fraction_in_range": inside / len(scores),
        },
        "model": model,
        "names": model["names"],
        "confidence": float(confidence),
    }


def covariate_balance(features: Any, treatment: Iterable[Any],
                      names: Sequence[str] | None = None,
                      weights: Iterable[Any] | None = None) -> dict[str, Any]:
    """Standardized mean differences before and after weighting.

    ``smd`` is the unweighted standardized mean difference for each covariate.
    When ``weights`` is supplied, ``weighted_smd`` is the same quantity after
    weighting. Values below about 0.1 are conventionally treated as balanced.
    """
    rows = _rows(features)
    treated = _treatment(treatment)
    if len(rows) != len(treated):
        raise ValueError("features and treatment lengths must match")
    labels = _labels(names, len(rows[0]))
    weight_values = None
    if weights is not None:
        weight_values = [float(value) for value in weights]
        if len(weight_values) != len(rows):
            raise ValueError("weights length must match features")
        if any(value < 0.0 for value in weight_values):
            raise ValueError("weights must be non-negative")

    def _weighted(values: list[float], w: list[float]) -> tuple[float, float]:
        total = sum(w)
        if total <= 0.0:
            return 0.0, 0.0
        center = sum(v * x for v, x in zip(values, w)) / total
        spread = sum(x * (v - center) ** 2 for v, x in zip(values, w)) / total
        return center, spread

    table = []
    for column in range(len(rows[0])):
        values = [row[column] for row in rows]
        treated_values = [values[i] for i in range(len(values)) if treated[i]]
        control_values = [values[i] for i in range(len(values)) if not treated[i]]
        if not treated_values or not control_values:
            raise ValueError("both treatment groups are required for balance")
        mean_t = mean(treated_values)
        mean_c = mean(control_values)
        pooled = math.sqrt((variance(treated_values) + variance(control_values)) / 2.0)
        smd = (mean_t - mean_c) / pooled if pooled else 0.0
        entry: dict[str, Any] = {
            "term": labels[column],
            "mean_treated": mean_t,
            "mean_control": mean_c,
            "smd": smd,
        }
        if weight_values is not None:
            treated_w = [weight_values[i] for i in range(len(values)) if treated[i]]
            control_w = [weight_values[i] for i in range(len(values)) if not treated[i]]
            w_mean_t, w_var_t = _weighted(treated_values, treated_w)
            w_mean_c, w_var_c = _weighted(control_values, control_w)
            w_pooled = math.sqrt((w_var_t + w_var_c) / 2.0)
            entry["weighted_mean_treated"] = w_mean_t
            entry["weighted_mean_control"] = w_mean_c
            entry["weighted_smd"] = (w_mean_t - w_mean_c) / w_pooled if w_pooled else 0.0
        table.append(entry)
    result: dict[str, Any] = {
        "table": table,
        "max_abs_smd": max(abs(entry["smd"]) for entry in table),
        "mean_abs_smd": mean([abs(entry["smd"]) for entry in table]),
        "n": len(rows),
        "weighted": weight_values is not None,
    }
    if weight_values is not None:
        result["max_abs_weighted_smd"] = max(
            abs(entry["weighted_smd"]) for entry in table
        )
        result["mean_abs_weighted_smd"] = mean(
            [abs(entry["weighted_smd"]) for entry in table]
        )
    return result


# ---------------------------------------------------------------------------
# Inverse-probability weighting
# ---------------------------------------------------------------------------

def _clip_scores(scores: list[float], trim: float) -> list[float]:
    trim = float(trim)
    if trim < 0.0 or trim >= 0.5:
        raise ValueError("trim must be between 0 and 0.5")
    low = trim if trim > 0.0 else 1e-9
    high = 1.0 - low
    return [min(max(value, low), high) for value in scores]


def _ipw_estimates(scores: list[float], treated: list[int],
                   outcome: list[float], trim: float) -> tuple[float, float]:
    clipped = _clip_scores(scores, trim)
    treated_weight = [
        1.0 / clipped[i] if treated[i] else 0.0 for i in range(len(clipped))
    ]
    control_weight = [
        1.0 / (1.0 - clipped[i]) if not treated[i] else 0.0
        for i in range(len(clipped))
    ]
    treated_total = sum(treated_weight)
    control_total = sum(control_weight)
    ate = (
        sum(treated_weight[i] * outcome[i] for i in range(len(outcome))) / treated_total
        - sum(control_weight[i] * outcome[i] for i in range(len(outcome))) / control_total
    )
    att_weight = [
        1.0 if treated[i] else clipped[i] / (1.0 - clipped[i])
        for i in range(len(clipped))
    ]
    att_treated_total = sum(att_weight[i] for i in range(len(clipped)) if treated[i])
    att_control_total = sum(att_weight[i] for i in range(len(clipped)) if not treated[i])
    att = (
        sum(att_weight[i] * outcome[i] for i in range(len(outcome)) if treated[i])
        / att_treated_total
        - sum(att_weight[i] * outcome[i] for i in range(len(outcome)) if not treated[i])
        / att_control_total
    )
    return ate, att


def _bootstrap_weights(rows: list[list[float]], treated: list[int],
                       outcome: list[float], trim: float, samples: int,
                       seed: Any, augmented: bool) -> list[tuple[float, float]]:
    rng = random.Random(seed)
    n = len(rows)
    estimates = []
    for _ in range(max(1, int(samples))):
        index = [rng.randrange(n) for _ in range(n)]
        draw_rows = [rows[i] for i in index]
        draw_treated = [treated[i] for i in index]
        draw_outcome = [outcome[i] for i in index]
        if len(set(draw_treated)) < 2:
            continue
        try:
            model = logistic_regression(draw_rows, draw_treated)
            scores = [min(max(value, 1e-9), 1.0 - 1e-9) for value in model["fitted"]]
            if augmented:
                ate, att = _aipw_estimates(draw_rows, scores, draw_treated, draw_outcome, trim)
            else:
                ate, att = _ipw_estimates(scores, draw_treated, draw_outcome, trim)
        except (ValueError, ZeroDivisionError):
            continue
        estimates.append((ate, att))
    return estimates


def ipw_ate(features: Any, treatment: Iterable[Any], outcome: Iterable[Any],
            trim: float = 0.0, confidence: float = 0.95,
            samples: int = 200, seed: Any = 0) -> dict[str, Any]:
    """Inverse-probability-weighted average treatment effect.

    ``ate`` is the population average effect and ``att`` is the effect on the
    treated. Standard errors and intervals come from a propensity-refitting
    bootstrap. ``trim`` winsorizes propensity scores away from 0 and 1.
    """
    rows = _rows(features)
    treated = _treatment(treatment)
    y = _outcome(outcome)
    if len(rows) != len(treated) or len(rows) != len(y):
        raise ValueError("features, treatment and outcome lengths must match")
    if len(set(treated)) < 2:
        raise ValueError("treatment must contain both treated and control units")
    model = logistic_regression(rows, treated)
    scores = [min(max(value, 1e-9), 1.0 - 1e-9) for value in model["fitted"]]
    ate, att = _ipw_estimates(scores, treated, y, trim)
    draws = _bootstrap_weights(rows, treated, y, trim, samples, seed, augmented=False)
    ate_se = std([value[0] for value in draws]) if len(draws) >= 2 else None
    att_se = std([value[1] for value in draws]) if len(draws) >= 2 else None
    ate_interval = _interval(ate, ate_se, confidence)
    att_interval = _interval(att, att_se, confidence)
    return {
        "estimator": "ipw",
        "ate": ate,
        "att": att,
        "se": ate_se,
        "ci_low": ate_interval["ci_low"],
        "ci_high": ate_interval["ci_high"],
        "att_se": att_se,
        "att_ci_low": att_interval["ci_low"],
        "att_ci_high": att_interval["ci_high"],
        "scores": scores,
        "weights": [
            1.0 / scores[i] if treated[i] else 1.0 / (1.0 - scores[i])
            for i in range(len(rows))
        ],
        "treated": treated,
        "n": len(rows),
        "treated_count": sum(treated),
        "control_count": len(treated) - sum(treated),
        "trim": float(trim),
        "samples": len(draws),
        "confidence": float(confidence),
        "model": model,
    }


def _aipw_estimates(rows: list[list[float]], scores: list[float],
                    treated: list[int], outcome: list[float],
                    trim: float) -> tuple[float, float]:
    clipped = _clip_scores(scores, trim)
    width = len(rows[0]) + 1
    treated_design = [[1.0] + rows[i] for i in range(len(rows)) if treated[i]]
    control_design = [[1.0] + rows[i] for i in range(len(rows)) if not treated[i]]
    treated_y = [outcome[i] for i in range(len(rows)) if treated[i]]
    control_y = [outcome[i] for i in range(len(rows)) if not treated[i]]
    if len(treated_design) <= width or len(control_design) <= width:
        raise ValueError("each treatment group needs more rows than parameters")
    beta_t = _ols(treated_design, treated_y)[0]
    beta_c = _ols(control_design, control_y)[0]
    design = [[1.0] + row for row in rows]
    mu1 = [dot(row, beta_t) for row in design]
    mu0 = [dot(row, beta_c) for row in design]
    n = len(rows)
    terms = []
    for i in range(n):
        if treated[i]:
            terms.append(mu1[i] - mu0[i] + (outcome[i] - mu1[i]) / clipped[i])
        else:
            terms.append(mu1[i] - mu0[i] - (outcome[i] - mu0[i]) / (1.0 - clipped[i]))
    ate = mean(terms)
    treated_terms = []
    for i in range(n):
        if treated[i]:
            treated_terms.append(outcome[i] - mu0[i])
        else:
            treated_terms.append(
                -(clipped[i] / (1.0 - clipped[i])) * (outcome[i] - mu0[i])
            )
    treated_total = sum(1 for value in treated if value)
    att = sum(treated_terms) / treated_total
    return ate, att


def aipw_ate(features: Any, treatment: Iterable[Any], outcome: Iterable[Any],
             trim: float = 0.0, confidence: float = 0.95,
             samples: int = 200, seed: Any = 0) -> dict[str, Any]:
    """Augmented inverse-probability-weighted (doubly robust) ATE.

    Combines a propensity model with separate outcome regressions for treated
    and control units. The estimator is consistent when either model is
    correctly specified.
    """
    rows = _rows(features)
    treated = _treatment(treatment)
    y = _outcome(outcome)
    if len(rows) != len(treated) or len(rows) != len(y):
        raise ValueError("features, treatment and outcome lengths must match")
    if len(set(treated)) < 2:
        raise ValueError("treatment must contain both treated and control units")
    model = logistic_regression(rows, treated)
    scores = [min(max(value, 1e-9), 1.0 - 1e-9) for value in model["fitted"]]
    ate, att = _aipw_estimates(rows, scores, treated, y, trim)
    draws = _bootstrap_weights(rows, treated, y, trim, samples, seed, augmented=True)
    ate_se = std([value[0] for value in draws]) if len(draws) >= 2 else None
    att_se = std([value[1] for value in draws]) if len(draws) >= 2 else None
    ate_interval = _interval(ate, ate_se, confidence)
    att_interval = _interval(att, att_se, confidence)
    return {
        "estimator": "aipw",
        "ate": ate,
        "att": att,
        "se": ate_se,
        "ci_low": ate_interval["ci_low"],
        "ci_high": ate_interval["ci_high"],
        "att_se": att_se,
        "att_ci_low": att_interval["ci_low"],
        "att_ci_high": att_interval["ci_high"],
        "scores": scores,
        "treated": treated,
        "n": len(rows),
        "treated_count": sum(treated),
        "control_count": len(treated) - sum(treated),
        "trim": float(trim),
        "samples": len(draws),
        "confidence": float(confidence),
        "model": model,
    }


# ---------------------------------------------------------------------------
# Propensity-score matching
# ---------------------------------------------------------------------------

def propensity_match(features: Any, treatment: Iterable[Any],
                     outcome: Iterable[Any], caliper: float = 0.2,
                     ratio: int = 1, replace: bool = False,
                     confidence: float = 0.95) -> dict[str, Any]:
    """Nearest-neighbour propensity-score matching for the ATT.

    ``caliper`` is expressed in standard deviations of the logit propensity
    score. A value of ``0`` disables the caliper. ``ratio`` controls how many
    controls are matched to each treated unit. Matched differences are averaged
    to estimate the ATT, with a paired standard error.
    """
    rows = _rows(features)
    treated = _treatment(treatment)
    y = _outcome(outcome)
    if len(rows) != len(treated) or len(rows) != len(y):
        raise ValueError("features, treatment and outcome lengths must match")
    if len(set(treated)) < 2:
        raise ValueError("treatment must contain both treated and control units")
    ratio = max(1, int(ratio))
    model = logistic_regression(rows, treated)
    scores = [min(max(value, 1e-9), 1.0 - 1e-9) for value in model["fitted"]]
    logit = [math.log(value / (1.0 - value)) for value in scores]
    spread = std(logit) or 0.0
    limit = None if float(caliper) <= 0.0 or spread <= 1e-12 else float(caliper) * spread
    treated_index = [i for i in range(len(treated)) if treated[i]]
    control_index = [i for i in range(len(treated)) if not treated[i]]
    available = set(control_index)
    pairs = []
    for index in treated_index:
        candidates = [
            j for j in control_index
            if (replace or j in available)
            and (limit is None or abs(logit[j] - logit[index]) <= limit)
        ]
        candidates.sort(key=lambda j: abs(logit[j] - logit[index]))
        chosen = candidates[:ratio]
        if not chosen:
            continue
        if not replace:
            for j in chosen:
                available.discard(j)
        matched_outcome = mean([y[j] for j in chosen])
        pairs.append({
            "treated": index,
            "controls": chosen,
            "treated_outcome": y[index],
            "control_outcome": matched_outcome,
            "difference": y[index] - matched_outcome,
            "propensity_treated": scores[index],
            "propensity_control": mean([scores[j] for j in chosen]),
        })
    if not pairs:
        raise ValueError("no matches were found; increase the caliper or check overlap")
    differences = [pair["difference"] for pair in pairs]
    att = mean(differences)
    se = std(differences) / math.sqrt(len(differences)) if len(differences) > 1 else None
    interval = _interval(att, se, confidence)
    return {
        "estimator": "matching",
        "att": att,
        "se": se,
        "ci_low": interval["ci_low"],
        "ci_high": interval["ci_high"],
        "pairs": pairs,
        "n": len(rows),
        "n_treated": len(treated_index),
        "n_matched": len(pairs),
        "n_unmatched": len(treated_index) - len(pairs),
        "caliper": float(caliper),
        "ratio": ratio,
        "replace": bool(replace),
        "confidence": float(confidence),
        "scores": scores,
        "model": model,
    }


# ---------------------------------------------------------------------------
# Difference-in-differences
# ---------------------------------------------------------------------------

def difference_in_differences(outcome: Iterable[Any], treated: Iterable[Any],
                              post: Iterable[Any],
                              covariates: Any = None,
                              names: Sequence[str] | None = None,
                              cluster: Iterable[Any] | None = None,
                              confidence: float = 0.95) -> dict[str, Any]:
    """Two-period difference-in-differences with an interaction term.

    The design is ``outcome ~ treated + post + treated:post + covariates``.
    The coefficient on the interaction is the DiD estimate. Passing ``cluster``
    switches to cluster-robust standard errors.
    """
    y = _outcome(outcome)
    treat = _treatment(treated)
    period = _treatment(post)
    n = len(y)
    if len(treat) != n or len(period) != n:
        raise ValueError("outcome, treated and post lengths must match")
    if covariates is None:
        cov_rows = [[] for _ in range(n)]
        cov_names: list[str] = []
    else:
        cov_rows = _rows(covariates)
        if len(cov_rows) != n:
            raise ValueError("covariates length must match outcome")
        cov_names = _labels(names, len(cov_rows[0]))
    design = [
        [1.0, float(treat[i]), float(period[i]), float(treat[i] * period[i])]
        + cov_rows[i]
        for i in range(n)
    ]
    k = len(design[0])
    if n <= k:
        raise ValueError("difference_in_differences requires more rows than parameters")
    beta, gram_inv, fitted, residuals = _ols(design, y)
    rss = sum(value * value for value in residuals)
    ybar = mean(y)
    tss = sum((value - ybar) ** 2 for value in y)
    r2 = 1.0 - rss / tss if tss else 1.0

    if cluster is None:
        df_test = n - k
        covariance = _covariance(gram_inv, residuals, df_test)
        clustered = False
        clusters = None
    else:
        groups: dict[Any, list[int]] = {}
        for i, key in enumerate(cluster):
            groups.setdefault(key, []).append(i)
        if len(groups) < 2:
            raise ValueError("cluster requires at least two clusters")
        meat = [[0.0] * k for _ in range(k)]
        for indices in groups.values():
            score = [sum(design[i][a] * residuals[i] for i in indices) for a in range(k)]
            for a in range(k):
                for b in range(k):
                    meat[a][b] += score[a] * score[b]
        count = len(groups)
        factor = (count / (count - 1.0)) * ((n - 1.0) / (n - k))
        covariance = [
            [factor * value for value in row]
            for row in _matrix_product(gram_inv, meat, gram_inv)
        ]
        df_test = count - 1
        clustered = True
        clusters = count

    se = [math.sqrt(max(covariance[i][i], 0.0)) for i in range(k)]
    t_values = [beta[i] / se[i] if se[i] else 0.0 for i in range(k)]
    p_values = [2.0 * (1.0 - t_cdf(abs(value), max(1, df_test))) for value in t_values]
    critical = _critical(confidence, df_test)
    labels = ["intercept", "treated", "post", "treated_x_post"] + cov_names
    table = [
        {
            "term": labels[i],
            "coefficient": beta[i],
            "std_error": se[i],
            "t": t_values[i],
            "p_value": p_values[i],
            "ci_low": beta[i] - critical * se[i],
            "ci_high": beta[i] + critical * se[i],
        }
        for i in range(k)
    ]
    return {
        "estimator": "difference_in_differences",
        "att": beta[3],
        "se": se[3],
        "t": t_values[3],
        "p_value": p_values[3],
        "ci_low": beta[3] - critical * se[3],
        "ci_high": beta[3] + critical * se[3],
        "coefficients": beta,
        "std_errors": se,
        "t_values": t_values,
        "p_values": p_values,
        "table": table,
        "fitted": fitted,
        "residuals": residuals,
        "r_squared": r2,
        "n": n,
        "treated_count": sum(treat),
        "control_count": n - sum(treat),
        "names": labels,
        "covariance": covariance,
        "clustered": clustered,
        "n_clusters": clusters,
        "df_resid": df_test,
        "confidence": float(confidence),
    }


# ---------------------------------------------------------------------------
# Instrumental variables
# ---------------------------------------------------------------------------

def instrumental_variables(instruments: Any, endogenous: Iterable[Any],
                           outcome: Iterable[Any], controls: Any = None,
                           names: Sequence[str] | None = None,
                           instrument_names: Sequence[str] | None = None,
                           confidence: float = 0.95) -> dict[str, Any]:
    """Two-stage least squares with one endogenous regressor.

    ``instruments`` is a list of rows of excluded instruments, ``endogenous`` is
    the endogenous regressor, and ``outcome`` is the response. ``controls`` is an
    optional list of rows of exogenous covariates. The result includes the
    structural estimate, first-stage F statistic, and a Sargan test when the
    model is over-identified.
    """
    z_rows = _rows(instruments)
    x_end = [float(value) for value in (endogenous or [])]
    y = _outcome(outcome)
    n = len(z_rows)
    if len(x_end) != n or len(y) != n:
        raise ValueError("instruments, endogenous and outcome lengths must match")
    if controls is None:
        control_rows = [[] for _ in range(n)]
        control_names: list[str] = []
    else:
        control_rows = _rows(controls)
        if len(control_rows) != n:
            raise ValueError("controls length must match outcome")
        control_names = _labels(names, len(control_rows[0]))
    instrument_count = len(z_rows[0])
    z_names = _labels(instrument_names, instrument_count, prefix="z")
    design_z = [[1.0] + z_rows[i] + control_rows[i] for i in range(n)]
    design_x = [[1.0, x_end[i]] + control_rows[i] for i in range(n)]
    if n <= len(design_z[0]):
        raise ValueError("instrumental_variables requires more rows than instruments")
    first_beta, first_inv, first_fitted, first_residuals = _ols(design_z, x_end)
    restricted = [[1.0] + control_rows[i] for i in range(n)]
    restricted_beta, _, _, restricted_residuals = _ols(restricted, x_end)
    rss_first = sum(value * value for value in first_residuals)
    rss_restricted = sum(value * value for value in restricted_residuals)
    df_first = n - len(design_z[0])
    if df_first <= 0:
        raise ValueError("not enough residual degrees of freedom in the first stage")
    if rss_first <= 0.0:
        first_f = None
        first_p = None
    else:
        first_f = ((rss_restricted - rss_first) / instrument_count) / (rss_first / df_first)
        first_p = 1.0 - f_cdf(first_f, instrument_count, df_first)
    first_r2 = 1.0 - rss_first / sum(
        (value - mean(x_end)) ** 2 for value in x_end
    )
    first_cov = _covariance(first_inv, first_residuals, df_first)

    design_hat = [[1.0, first_fitted[i]] + control_rows[i] for i in range(n)]
    beta, gram_inv, _, _ = _ols(design_hat, y)
    structural = [y[i] - dot(design_x[i], beta) for i in range(n)]
    k = len(design_hat[0])
    df_resid = n - k
    if df_resid <= 0:
        raise ValueError("not enough residual degrees of freedom in the second stage")
    covariance = _covariance(gram_inv, structural, df_resid)
    se = [math.sqrt(max(covariance[i][i], 0.0)) for i in range(k)]
    t_values = [beta[i] / se[i] if se[i] else 0.0 for i in range(k)]
    p_values = [2.0 * (1.0 - t_cdf(abs(value), df_resid)) for value in t_values]
    critical = _critical(confidence, df_resid)
    labels = ["intercept", "endogenous"] + control_names
    table = [
        {
            "term": labels[i],
            "coefficient": beta[i],
            "std_error": se[i],
            "t": t_values[i],
            "p_value": p_values[i],
            "ci_low": beta[i] - critical * se[i],
            "ci_high": beta[i] + critical * se[i],
        }
        for i in range(k)
    ]

    sargan = None
    sargan_df = None
    sargan_p = None
    if instrument_count > 1:
        aux_beta, _, _, aux_residuals = _ols(design_z, structural)
        rss_aux = sum(value * value for value in aux_residuals)
        tss_aux = sum((value - mean(structural)) ** 2 for value in structural)
        aux_r2 = 1.0 - rss_aux / tss_aux if tss_aux else 0.0
        sargan = n * aux_r2
        sargan_df = instrument_count - 1
        sargan_p = 1.0 - chi2_cdf(sargan, sargan_df)

    return {
        "estimator": "2sls",
        "endogenous_coefficient": beta[1],
        "se": se[1],
        "t": t_values[1],
        "p_value": p_values[1],
        "ci_low": beta[1] - critical * se[1],
        "ci_high": beta[1] + critical * se[1],
        "coefficients": beta,
        "std_errors": se,
        "t_values": t_values,
        "p_values": p_values,
        "table": table,
        "first_stage": {
            "coefficients": first_beta,
            "std_errors": [
                math.sqrt(max(first_cov[i][i], 0.0))
                for i in range(len(first_beta))
            ],
            "f_statistic": first_f,
            "p_value": first_p,
            "r_squared": first_r2,
            "names": ["intercept"] + z_names + control_names,
        },
        "sargan": sargan,
        "sargan_df": sargan_df,
        "sargan_p_value": sargan_p,
        "fitted": [dot(design_x[i], beta) for i in range(n)],
        "residuals": structural,
        "n": n,
        "instruments": instrument_count,
        "names": labels,
        "covariance": covariance,
        "df_resid": df_resid,
        "confidence": float(confidence),
    }


# ---------------------------------------------------------------------------
# Regression discontinuity
# ---------------------------------------------------------------------------

def _poly_design(values: list[float], degree: int) -> list[list[float]]:
    return [[value ** power for power in range(degree + 1)] for value in values]


def regression_discontinuity(running: Iterable[Any], outcome: Iterable[Any],
                             cutoff: float = 0.0, bandwidth: float | None = None,
                             degree: int = 1, confidence: float = 0.95) -> dict[str, Any]:
    """Sharp regression-discontinuity estimate at ``cutoff``.

    Fits separate polynomials of order ``degree`` on each side of the cutoff and
    reports the difference in intercepts as the jump. ``bandwidth`` restricts
    the estimation window; ``None`` uses the full range.
    """
    x = [float(value) for value in (running or [])]
    y = _outcome(outcome)
    if len(x) != len(y):
        raise ValueError("running and outcome lengths must match")
    if not x:
        raise ValueError("running and outcome are required")
    degree = max(0, int(degree))
    cutoff = float(cutoff)
    if bandwidth is not None:
        bandwidth = float(bandwidth)
        if bandwidth <= 0.0:
            raise ValueError("bandwidth must be positive")
        keep = [i for i in range(len(x)) if abs(x[i] - cutoff) <= bandwidth]
        x = [x[i] for i in keep]
        y = [y[i] for i in keep]
    left = [i for i in range(len(x)) if x[i] < cutoff]
    right = [i for i in range(len(x)) if x[i] >= cutoff]
    needed = degree + 2
    if len(left) < needed or len(right) < needed:
        raise ValueError("not enough observations on each side of the cutoff")
    left_x = [x[i] - cutoff for i in left]
    right_x = [x[i] - cutoff for i in right]
    left_y = [y[i] for i in left]
    right_y = [y[i] for i in right]
    left_design = _poly_design(left_x, degree)
    right_design = _poly_design(right_x, degree)
    left_beta, left_inv, left_fitted, left_residuals = _ols(left_design, left_y)
    right_beta, right_inv, right_fitted, right_residuals = _ols(right_design, right_y)
    left_df = len(left) - len(left_design[0])
    right_df = len(right) - len(right_design[0])
    if left_df <= 0 or right_df <= 0:
        raise ValueError("not enough residual degrees of freedom on each side")
    left_cov = _covariance(left_inv, left_residuals, left_df)
    right_cov = _covariance(right_inv, right_residuals, right_df)
    estimate = right_beta[0] - left_beta[0]
    variance_estimate = left_cov[0][0] + right_cov[0][0]
    se = math.sqrt(max(variance_estimate, 0.0))
    df = left_df + right_df
    t_value = estimate / se if se else 0.0
    p_value = 2.0 * (1.0 - t_cdf(abs(t_value), max(1, df)))
    critical = _critical(confidence, df)
    return {
        "estimator": "regression_discontinuity",
        "estimate": estimate,
        "se": se,
        "t": t_value,
        "p_value": p_value,
        "ci_low": estimate - critical * se,
        "ci_high": estimate + critical * se,
        "cutoff": cutoff,
        "bandwidth": bandwidth,
        "degree": degree,
        "left_intercept": left_beta[0],
        "right_intercept": right_beta[0],
        "left": {
            "coefficients": left_beta,
            "std_errors": [math.sqrt(max(left_cov[i][i], 0.0)) for i in range(len(left_beta))],
            "n": len(left),
            "fitted": left_fitted,
            "residuals": left_residuals,
        },
        "right": {
            "coefficients": right_beta,
            "std_errors": [math.sqrt(max(right_cov[i][i], 0.0)) for i in range(len(right_beta))],
            "n": len(right),
            "fitted": right_fitted,
            "residuals": right_residuals,
        },
        "n": len(x),
        "n_left": len(left),
        "n_right": len(right),
        "df_resid": df,
        "confidence": float(confidence),
    }


# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------

def build_causal_namespace() -> dict[str, Any]:
    return {
        "propensity_scores": propensity_scores,
        "covariate_balance": covariate_balance,
        "ipw_ate": ipw_ate,
        "aipw_ate": aipw_ate,
        "propensity_match": propensity_match,
        "difference_in_differences": difference_in_differences,
        "instrumental_variables": instrumental_variables,
        "regression_discontinuity": regression_discontinuity,
    }
