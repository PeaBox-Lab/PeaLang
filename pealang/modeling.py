"""Generalized linear models, regularized regression, survival analysis and ARIMA.

This module is the predictive-modeling layer above :mod:`pealang.inference`. It
provides inferential generalized linear models (Gaussian, binomial and Poisson),
ridge/lasso/elastic-net regression, Kaplan-Meier and Cox survival models, and
ARIMA forecasting. Everything is pure Python and dependency-free.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Sequence

from .numerics import (
    _nums,
    mean,
    normal_cdf,
    normal_ppf,
    chi2_cdf,
    dot,
    solve,
    inverse,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _design(features: Any) -> list[list[float]]:
    rows = [[float(value) for value in row] for row in (features or [])]
    if not rows:
        raise ValueError("features are required")
    width = len(rows[0])
    if width == 0 or any(len(row) != width for row in rows):
        raise ValueError("feature rows must be non-empty and equal length")
    return [[1.0] + row for row in rows]


def _labels(names: Sequence[str] | None, width: int, prefix: str = "x") -> list[str]:
    if names is None:
        return [prefix + str(i + 1) for i in range(width)]
    labels = list(names)
    if len(labels) != width:
        raise ValueError("names length must match the number of features")
    return labels


def _normal_p_value(z: float) -> float:
    return 2.0 * (1.0 - normal_cdf(abs(z)))


def _lstsq(design: list[list[float]], target: list[float],
           penalty: float = 0.0, penalize_intercept: bool = False) -> list[float]:
    """Least squares via normal equations, with optional ridge penalty."""
    width = len(design[0])
    xtx = [[0.0] * width for _ in range(width)]
    xty = [0.0] * width
    for row, value in zip(design, target):
        for i in range(width):
            xty[i] += row[i] * value
            for j in range(width):
                xtx[i][j] += row[i] * row[j]
    if penalty:
        for i in range(width):
            if i == 0 and not penalize_intercept:
                continue
            xtx[i][i] += penalty
    try:
        return [float(value) for value in solve(xtx, xty)]
    except ValueError as exc:
        raise ValueError("design matrix is singular or collinear: " + str(exc)) from exc


# ---------------------------------------------------------------------------
# Generalized linear models
# ---------------------------------------------------------------------------

def _glm_family(family: str):
    key = str(family).lower()
    if key in ("gaussian", "normal", "identity"):
        return {
            "name": "gaussian",
            "inverse": lambda eta: eta,
            "derivative": lambda mu: 1.0,
            "variance": lambda mu: 1.0,
        }
    if key in ("binomial", "logit", "logistic"):
        return {
            "name": "binomial",
            "inverse": lambda eta: 1.0 / (1.0 + math.exp(-max(-35.0, min(35.0, eta)))),
            "derivative": lambda mu: 1.0 / max(mu * (1.0 - mu), 1e-12),
            "variance": lambda mu: max(mu * (1.0 - mu), 1e-12),
        }
    if key in ("poisson", "log"):
        return {
            "name": "poisson",
            "inverse": lambda eta: math.exp(max(-35.0, min(35.0, eta))),
            "derivative": lambda mu: 1.0 / max(mu, 1e-12),
            "variance": lambda mu: max(mu, 1e-12),
        }
    raise ValueError("Unsupported GLM family: " + str(family))


def _deviance(family: str, target: list[float], mu: list[float]) -> float:
    total = 0.0
    if family == "gaussian":
        return sum((y - m) ** 2 for y, m in zip(target, mu))
    if family == "binomial":
        for y, m in zip(target, mu):
            m = min(max(m, 1e-12), 1.0 - 1e-12)
            if y > 0:
                total += y * math.log(y / m)
            if y < 1:
                total += (1.0 - y) * math.log((1.0 - y) / (1.0 - m))
        return 2.0 * total
    if family == "poisson":
        for y, m in zip(target, mu):
            m = max(m, 1e-12)
            if y > 0:
                total += y * math.log(y / m)
            total += m - y
        return 2.0 * total
    raise ValueError("Unsupported GLM family: " + str(family))


def _log_likelihood(family: str, target: list[float], mu: list[float],
                    sigma2: float = 1.0) -> float:
    n = len(target)
    if family == "gaussian":
        return -0.5 * n * (math.log(2.0 * math.pi * max(sigma2, 1e-12)) + 1.0)
    if family == "binomial":
        total = 0.0
        for y, m in zip(target, mu):
            m = min(max(m, 1e-12), 1.0 - 1e-12)
            total += y * math.log(m) + (1.0 - y) * math.log(1.0 - m)
        return total
    if family == "poisson":
        total = 0.0
        for y, m in zip(target, mu):
            m = max(m, 1e-12)
            total += y * math.log(m) - m - math.lgamma(y + 1.0)
        return total
    raise ValueError("Unsupported GLM family: " + str(family))


def glm(features: Any, target: Iterable[Any], family: str = "gaussian",
        names: Sequence[str] | None = None, confidence: float = 0.95,
        max_iter: int = 100, tol: float = 1e-8) -> dict[str, Any]:
    """Fit a generalized linear model by iteratively reweighted least squares.

    Supported families: ``"gaussian"`` (identity), ``"binomial"`` (logit) and
    ``"poisson"`` (log). The result includes a coefficient table with standard
    errors, z-statistics, p-values and confidence intervals, plus deviance,
    AIC/BIC and fitted values.
    """
    design = _design(features)
    y = [float(value) for value in (target or [])]
    n = len(design)
    if n != len(y):
        raise ValueError("features and target lengths must match")
    spec = _glm_family(family)
    key = spec["name"]
    if key == "binomial" and any(value < 0.0 or value > 1.0 for value in y):
        raise ValueError("binomial targets must be between 0 and 1")
    if key == "poisson" and any(value < 0.0 for value in y):
        raise ValueError("poisson targets must be non-negative")
    k = len(design[0])
    if n <= k:
        raise ValueError("glm requires more observations than parameters")

    beta = [0.0] * k
    if key == "binomial":
        base = min(max(mean(y), 1e-3), 1.0 - 1e-3)
        beta[0] = math.log(base / (1.0 - base))
    elif key == "poisson":
        beta[0] = math.log(max(mean(y), 1e-3))

    converged = False
    iterations = 0
    mu = [0.0] * n
    weights = [1.0] * n
    for iterations in range(1, max(1, int(max_iter)) + 1):
        eta = [dot(row, beta) for row in design]
        mu = [spec["inverse"](value) for value in eta]
        weights = [
            1.0 / max(spec["variance"](m) * spec["derivative"](m) ** 2, 1e-12)
            for m in mu
        ]
        z = [
            eta[i] + (y[i] - mu[i]) * spec["derivative"](mu[i])
            for i in range(n)
        ]
        xtwx = [[0.0] * k for _ in range(k)]
        xtwz = [0.0] * k
        for i, row in enumerate(design):
            w = weights[i]
            for a in range(k):
                xtwz[a] += w * row[a] * z[i]
                for b in range(k):
                    xtwx[a][b] += w * row[a] * row[b]
        try:
            updated = [float(value) for value in solve(xtwx, xtwz)]
        except ValueError as exc:
            raise ValueError("glm failed: design is singular or collinear: " + str(exc)) from exc
        change = max(abs(updated[i] - beta[i]) for i in range(k))
        beta = updated
        if change < float(tol):
            converged = True
            break

    eta = [dot(row, beta) for row in design]
    mu = [spec["inverse"](value) for value in eta]
    weights = [
        1.0 / max(spec["variance"](m) * spec["derivative"](m) ** 2, 1e-12)
        for m in mu
    ]
    deviance = _deviance(key, y, mu)
    null_mu = [mean(y)] * n
    null_deviance = _deviance(key, y, null_mu)
    if key == "gaussian":
        df_resid = n - k
        sigma2 = deviance / df_resid if df_resid > 0 else 0.0
        dispersion = sigma2
    else:
        df_resid = n - k
        sigma2 = 1.0
        dispersion = 1.0
    loglik = _log_likelihood(key, y, mu, sigma2)
    aic = -2.0 * loglik + 2.0 * k
    bic = -2.0 * loglik + k * math.log(n)

    xtwx = [[0.0] * k for _ in range(k)]
    for i, row in enumerate(design):
        w = weights[i]
        for a in range(k):
            for b in range(k):
                xtwx[a][b] += w * row[a] * row[b]
    try:
        covariance = [[dispersion * value for value in row] for row in inverse(xtwx)]
    except ValueError as exc:
        raise ValueError("glm covariance is singular: " + str(exc)) from exc
    se = [math.sqrt(max(covariance[i][i], 0.0)) for i in range(k)]
    z_values = [beta[i] / se[i] if se[i] else 0.0 for i in range(k)]
    p_values = [_normal_p_value(value) for value in z_values]
    critical = normal_ppf(1.0 - (1.0 - float(confidence)) / 2.0)
    ci_low = [beta[i] - critical * se[i] for i in range(k)]
    ci_high = [beta[i] + critical * se[i] for i in range(k)]

    labels = ["intercept"] + _labels(names, k - 1)
    table = [
        {
            "term": labels[i],
            "coefficient": beta[i],
            "std_error": se[i],
            "z": z_values[i],
            "p_value": p_values[i],
            "ci_low": ci_low[i],
            "ci_high": ci_high[i],
        }
        for i in range(k)
    ]
    fitted = mu
    residuals = [a - b for a, b in zip(y, fitted)]
    pseudo_r2 = 1.0 - deviance / null_deviance if null_deviance else 0.0
    return {
        "family": key,
        "coefficients": beta,
        "intercept": beta[0],
        "slopes": beta[1:],
        "std_errors": se,
        "z_values": z_values,
        "p_values": p_values,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "table": table,
        "fitted": fitted,
        "residuals": residuals,
        "deviance": deviance,
        "null_deviance": null_deviance,
        "pseudo_r_squared": pseudo_r2,
        "aic": aic,
        "bic": bic,
        "sigma2": sigma2,
        "dispersion": dispersion,
        "df_resid": df_resid,
        "n": n,
        "names": labels,
        "covariance": covariance,
        "confidence": float(confidence),
        "iterations": iterations,
        "converged": converged,
    }


def logistic_regression(features: Any, target: Iterable[Any],
                        names: Sequence[str] | None = None,
                        confidence: float = 0.95, **options: Any) -> dict[str, Any]:
    """Inferential logistic regression (binomial GLM with a logit link)."""
    return glm(features, target, "binomial", names, confidence, **options)


def poisson_regression(features: Any, target: Iterable[Any],
                       names: Sequence[str] | None = None,
                       confidence: float = 0.95, **options: Any) -> dict[str, Any]:
    """Inferential Poisson regression (log link)."""
    return glm(features, target, "poisson", names, confidence, **options)


def predict_glm(model: dict[str, Any], features: Any,
                type: str = "response") -> dict[str, Any]:
    """Predict from a fitted GLM, returning response and linear predictors."""
    rows = [[float(value) for value in row] for row in (features or [])]
    beta = model["coefficients"]
    spec = _glm_family(model["family"])
    linear = [dot([1.0] + row, beta) for row in rows]
    response = [spec["inverse"](value) for value in linear]
    return {
        "predicted": response if str(type).lower() in ("response", "mu") else linear,
        "response": response,
        "linear": linear,
        "family": model["family"],
    }


# ---------------------------------------------------------------------------
# Regularized regression
# ---------------------------------------------------------------------------

def _center(rows: list[list[float]], target: list[float]):
    n, p = len(rows), len(rows[0])
    xbar = [sum(row[j] for row in rows) / n for j in range(p)]
    ybar = sum(target) / n
    centered = [[row[j] - xbar[j] for j in range(p)] for row in rows]
    centered_y = [value - ybar for value in target]
    return centered, centered_y, xbar, ybar


def _regression_result(beta, intercept, rows, y, names, **extra):
    fitted = [intercept + dot(row, beta) for row in rows]
    residuals = [a - b for a, b in zip(y, fitted)]
    ybar = mean(y)
    tss = sum((value - ybar) ** 2 for value in y)
    rss = sum(value * value for value in residuals)
    r2 = 1.0 - rss / tss if tss else 1.0
    return {
        "coefficients": beta,
        "intercept": intercept,
        "slopes": beta,
        "names": ["intercept"] + list(names),
        "fitted": fitted,
        "residuals": residuals,
        "r_squared": r2,
        "rss": rss,
        "n": len(y),
        **extra,
    }


def ridge_regression(features: Any, target: Iterable[Any], alpha: float = 1.0,
                     names: Sequence[str] | None = None) -> dict[str, Any]:
    """Ridge regression with a closed-form penalized least-squares solution."""
    rows = [[float(value) for value in row] for row in (features or [])]
    y = [float(value) for value in (target or [])]
    if not rows or len(rows) != len(y):
        raise ValueError("features and target are required and must match")
    p = len(rows[0])
    labels = _labels(names, p)
    alpha = float(alpha)
    if alpha < 0:
        raise ValueError("alpha must be non-negative")
    centered, centered_y, xbar, ybar = _center(rows, y)
    xtx = [[0.0] * p for _ in range(p)]
    xty = [0.0] * p
    for row, value in zip(centered, centered_y):
        for i in range(p):
            xty[i] += row[i] * value
            for j in range(p):
                xtx[i][j] += row[i] * row[j]
    for i in range(p):
        xtx[i][i] += alpha
    beta = [float(value) for value in solve(xtx, xty)]
    intercept = ybar - sum(xbar[j] * beta[j] for j in range(p))
    return _regression_result(beta, intercept, rows, y, labels, alpha=alpha)


def _coordinate_descent(rows: list[list[float]], y: list[float], alpha: float,
                        l1_ratio: float, max_iter: int, tol: float):
    n, p = len(rows), len(rows[0])
    centered, centered_y, xbar, ybar = _center(rows, y)
    norms = [sum(row[j] * row[j] for row in centered) for j in range(p)]
    beta = [0.0] * p
    iterations = 0
    for iterations in range(1, max(1, int(max_iter)) + 1):
        maximum = 0.0
        for j in range(p):
            if norms[j] <= 0.0:
                beta[j] = 0.0
                continue
            residual = [
                centered_y[i] - sum(centered[i][k] * beta[k] for k in range(p))
                for i in range(n)
            ]
            rho = sum(centered[i][j] * (residual[i] + centered[i][j] * beta[j])
                      for i in range(n))
            threshold = alpha * l1_ratio
            if rho > threshold:
                value = (rho - threshold) / (norms[j] + alpha * (1.0 - l1_ratio))
            elif rho < -threshold:
                value = (rho + threshold) / (norms[j] + alpha * (1.0 - l1_ratio))
            else:
                value = 0.0
            maximum = max(maximum, abs(value - beta[j]))
            beta[j] = value
        if maximum < float(tol):
            break
    intercept = ybar - sum(xbar[j] * beta[j] for j in range(p))
    return beta, intercept, iterations


def lasso_regression(features: Any, target: Iterable[Any], alpha: float = 0.1,
                     names: Sequence[str] | None = None, max_iter: int = 10000,
                     tol: float = 1e-8) -> dict[str, Any]:
    """Lasso regression fitted by cyclic coordinate descent."""
    rows = [[float(value) for value in row] for row in (features or [])]
    y = [float(value) for value in (target or [])]
    if not rows or len(rows) != len(y):
        raise ValueError("features and target are required and must match")
    p = len(rows[0])
    labels = _labels(names, p)
    alpha = float(alpha)
    if alpha < 0:
        raise ValueError("alpha must be non-negative")
    beta, intercept, iterations = _coordinate_descent(rows, y, alpha, 1.0, max_iter, tol)
    return _regression_result(beta, intercept, rows, y, labels, alpha=alpha,
                              l1_ratio=1.0, iterations=iterations)


def elastic_net(features: Any, target: Iterable[Any], alpha: float = 0.1,
                l1_ratio: float = 0.5, names: Sequence[str] | None = None,
                max_iter: int = 10000, tol: float = 1e-8) -> dict[str, Any]:
    """Elastic-net regression (a blend of L1 and L2 penalties)."""
    rows = [[float(value) for value in row] for row in (features or [])]
    y = [float(value) for value in (target or [])]
    if not rows or len(rows) != len(y):
        raise ValueError("features and target are required and must match")
    p = len(rows[0])
    labels = _labels(names, p)
    alpha, l1_ratio = float(alpha), float(l1_ratio)
    if alpha < 0:
        raise ValueError("alpha must be non-negative")
    if not 0.0 <= l1_ratio <= 1.0:
        raise ValueError("l1_ratio must be between 0 and 1")
    beta, intercept, iterations = _coordinate_descent(rows, y, alpha, l1_ratio,
                                                      max_iter, tol)
    return _regression_result(beta, intercept, rows, y, labels, alpha=alpha,
                              l1_ratio=l1_ratio, iterations=iterations)


# ---------------------------------------------------------------------------
# Survival analysis
# ---------------------------------------------------------------------------

def _survival_inputs(times: Iterable[Any], events: Iterable[Any] | None):
    t = [float(value) for value in (times or [])]
    if events is None:
        e = [1] * len(t)
    else:
        e = [1 if value else 0 for value in events]
        if len(e) != len(t):
            raise ValueError("times and events lengths must match")
    if not t:
        raise ValueError("times are required")
    return t, e


def kaplan_meier(times: Iterable[Any], events: Iterable[Any] | None = None,
                 confidence: float = 0.95) -> dict[str, Any]:
    """Kaplan-Meier survival curve with Greenwood confidence bands."""
    t, e = _survival_inputs(times, events)
    unique = sorted(set(t))
    survival = 1.0
    greenwood = 0.0
    timeline = []
    critical = normal_ppf(1.0 - (1.0 - float(confidence)) / 2.0)
    for moment in unique:
        at_risk = sum(1 for value in t if value >= moment)
        deaths = sum(1 for value, flag in zip(t, e) if value == moment and flag)
        censored = sum(1 for value, flag in zip(t, e) if value == moment and not flag)
        if at_risk <= 0:
            continue
        if deaths:
            survival *= 1.0 - deaths / at_risk
            if at_risk - deaths > 0:
                greenwood += deaths / (at_risk * (at_risk - deaths))
        standard_error = survival * math.sqrt(greenwood) if greenwood > 0 else 0.0
        timeline.append({
            "time": moment,
            "at_risk": at_risk,
            "events": deaths,
            "censored": censored,
            "survival": survival,
            "std_error": standard_error,
            "ci_low": max(0.0, survival - critical * standard_error),
            "ci_high": min(1.0, survival + critical * standard_error),
        })
    median = next((row["time"] for row in timeline if row["survival"] <= 0.5), None)
    return {
        "timeline": timeline,
        "median_survival": median,
        "n": len(t),
        "events": sum(e),
        "censored": len(e) - sum(e),
        "confidence": float(confidence),
    }


def log_rank_test(times_a: Iterable[Any], events_a: Iterable[Any] | None,
                  times_b: Iterable[Any], events_b: Iterable[Any] | None) -> dict[str, Any]:
    """Two-sample log-rank test for equality of survival curves."""
    ta, ea = _survival_inputs(times_a, events_a)
    tb, eb = _survival_inputs(times_b, events_b)
    observed = sum(ea)
    expected = 0.0
    variance_total = 0.0
    for moment in sorted(set(ta + tb)):
        n_a = sum(1 for value in ta if value >= moment)
        n_b = sum(1 for value in tb if value >= moment)
        d_a = sum(1 for value, flag in zip(ta, ea) if value == moment and flag)
        d_b = sum(1 for value, flag in zip(tb, eb) if value == moment and flag)
        n, d = n_a + n_b, d_a + d_b
        if n < 2 or d == 0:
            continue
        expected += d * n_a / n
        variance_total += n_a * n_b * d * (n - d) / (n * n * (n - 1))
    if variance_total <= 0:
        statistic = 0.0
        p_value = 1.0
    else:
        statistic = (observed - expected) ** 2 / variance_total
        p_value = 1.0 - chi2_cdf(statistic, 1)
    return {
        "chi2": statistic,
        "df": 1,
        "p_value": p_value,
        "observed": observed,
        "expected": expected,
        "variance": variance_total,
    }


def concordance_index(times: Iterable[Any], events: Iterable[Any],
                      scores: Iterable[Any]) -> float | None:
    """Harrell's concordance index for a risk score."""
    t, e = _survival_inputs(times, events)
    s = [float(value) for value in (scores or [])]
    if len(s) != len(t):
        raise ValueError("scores length must match times")
    concordant = ties = comparable = 0
    for i in range(len(t)):
        if not e[i]:
            continue
        for j in range(len(t)):
            if t[j] <= t[i]:
                continue
            comparable += 1
            if s[i] > s[j]:
                concordant += 1
            elif s[i] == s[j]:
                ties += 1
    if comparable == 0:
        return None
    return (concordant + 0.5 * ties) / comparable


def cox_proportional_hazards(features: Any, times: Iterable[Any],
                             events: Iterable[Any], names: Sequence[str] | None = None,
                             confidence: float = 0.95, max_iter: int = 50,
                             tol: float = 1e-8) -> dict[str, Any]:
    """Cox proportional-hazards model fitted by Newton-Raphson.

    Ties are handled with the Breslow approximation. The result includes
    coefficients, standard errors, hazard ratios, z-statistics, p-values,
    confidence intervals, the partial log-likelihood and Harrell's C.
    """
    rows = [[float(value) for value in row] for row in (features or [])]
    t, e = _survival_inputs(times, events)
    if len(rows) != len(t):
        raise ValueError("features and times lengths must match")
    n = len(rows)
    p = len(rows[0])
    labels = _labels(names, p)
    beta = [0.0] * p
    converged = False
    iterations = 0
    information = [[0.0] * p for _ in range(p)]
    log_likelihood = 0.0
    for iterations in range(1, max(1, int(max_iter)) + 1):
        eta = [dot(row, beta) for row in rows]
        exp_eta = [math.exp(max(-35.0, min(35.0, value))) for value in eta]
        score = [0.0] * p
        information = [[0.0] * p for _ in range(p)]
        log_likelihood = 0.0
        for i in range(n):
            if not e[i]:
                continue
            risk = [j for j in range(n) if t[j] >= t[i]]
            s0 = sum(exp_eta[j] for j in risk)
            if s0 <= 0:
                continue
            s1 = [sum(exp_eta[j] * rows[j][a] for j in risk) for a in range(p)]
            s2 = [
                [sum(exp_eta[j] * rows[j][a] * rows[j][b] for j in risk) for b in range(p)]
                for a in range(p)
            ]
            log_likelihood += eta[i] - math.log(s0)
            for a in range(p):
                score[a] += rows[i][a] - s1[a] / s0
                for b in range(p):
                    information[a][b] += s2[a][b] / s0 - (s1[a] / s0) * (s1[b] / s0)
        try:
            step = [float(value) for value in solve(information, score)]
        except ValueError as exc:
            raise ValueError("cox model is singular or collinear: " + str(exc)) from exc
        updated = [beta[a] + step[a] for a in range(p)]
        change = max(abs(updated[a] - beta[a]) for a in range(p))
        beta = updated
        if change < float(tol):
            converged = True
            break

    covariance = inverse(information)
    se = [math.sqrt(max(covariance[a][a], 0.0)) for a in range(p)]
    z_values = [beta[a] / se[a] if se[a] else 0.0 for a in range(p)]
    p_values = [_normal_p_value(value) for value in z_values]
    critical = normal_ppf(1.0 - (1.0 - float(confidence)) / 2.0)
    ci_low = [beta[a] - critical * se[a] for a in range(p)]
    ci_high = [beta[a] + critical * se[a] for a in range(p)]
    hazard_ratios = [math.exp(max(-35.0, min(35.0, value))) for value in beta]
    scores = [dot(row, beta) for row in rows]
    table = [
        {
            "term": labels[a],
            "coefficient": beta[a],
            "hazard_ratio": hazard_ratios[a],
            "std_error": se[a],
            "z": z_values[a],
            "p_value": p_values[a],
            "ci_low": ci_low[a],
            "ci_high": ci_high[a],
        }
        for a in range(p)
    ]
    return {
        "coefficients": beta,
        "hazard_ratios": hazard_ratios,
        "std_errors": se,
        "z_values": z_values,
        "p_values": p_values,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "table": table,
        "log_likelihood": log_likelihood,
        "concordance": concordance_index(t, e, scores),
        "n": n,
        "events": sum(e),
        "names": labels,
        "covariance": covariance,
        "confidence": float(confidence),
        "iterations": iterations,
        "converged": converged,
    }


# ---------------------------------------------------------------------------
# ARIMA
# ---------------------------------------------------------------------------

def _difference(values: list[float], order: int) -> list[float]:
    out = list(values)
    for _ in range(max(0, int(order))):
        out = [out[i] - out[i - 1] for i in range(1, len(out))]
    return out


def _integrate(forecast: list[float], original: list[float], order: int) -> list[float]:
    if order <= 0:
        return list(forecast)
    levels = [list(original)]
    for _ in range(int(order)):
        previous = levels[-1]
        levels.append([previous[i] - previous[i - 1] for i in range(1, len(previous))])
    out = list(forecast)
    for level in range(int(order) - 1, -1, -1):
        base = levels[level][-1]
        cumulative = 0.0
        integrated = []
        for value in out:
            cumulative += value
            integrated.append(base + cumulative)
        out = integrated
    return out


def arima(values: Iterable[Any], p: int = 1, d: int = 0, q: int = 0,
          periods: int = 1, include_mean: bool = True, max_iter: int = 50,
          tol: float = 1e-8) -> dict[str, Any]:
    """Fit an ARIMA(p, d, q) model by iterative conditional least squares.

    The model is estimated on the differenced series. Forecasts are integrated
    back to the original scale, so ``forecast`` is directly comparable with the
    input values.
    """
    original = _nums(values)
    p, d, q = max(0, int(p)), max(0, int(d)), max(0, int(q))
    if len(original) <= d + max(p, q) + 1:
        raise ValueError("not enough observations for the requested ARIMA order")
    series = _difference(original, d)
    n = len(series)
    start = max(p, q)
    if n <= start + 1:
        raise ValueError("not enough observations after differencing")
    k = (1 if include_mean else 0) + p + q
    if n <= k:
        raise ValueError("not enough observations for the requested ARIMA order")
    residuals = [0.0] * n
    params = [0.0] * k
    converged = False
    iterations = 0
    for iterations in range(1, max(1, int(max_iter)) + 1):
        design = []
        target = []
        for t in range(start, n):
            row = ([1.0] if include_mean else [])
            row += [series[t - i] for i in range(1, p + 1)]
            row += [residuals[t - j] for j in range(1, q + 1)]
            design.append(row)
            target.append(series[t])
        updated = _lstsq(design, target, penalty=1e-10)
        new_residuals = [0.0] * n
        for index, t in enumerate(range(start, n)):
            new_residuals[t] = target[index] - dot(design[index], updated)
        change = max((abs(updated[i] - params[i]) for i in range(k)), default=0.0)
        params = updated
        residuals = new_residuals
        if change < float(tol):
            converged = True
            break

    fitted = [series[t] - residuals[t] for t in range(n)]
    rss = sum(value * value for value in residuals[start:])
    dof = max(1, n - start - k)
    sigma2 = rss / dof
    loglik = -0.5 * (n - start) * (math.log(2.0 * math.pi * max(sigma2, 1e-12)) + 1.0)
    aic = -2.0 * loglik + 2.0 * k
    bic = -2.0 * loglik + k * math.log(max(n - start, 2))

    offset = 1 if include_mean else 0
    ar = params[offset:offset + p]
    ma = params[offset + p:offset + p + q]
    intercept = params[0] if include_mean else 0.0

    history = list(series)
    noise = list(residuals)
    forecast_differenced = []
    for _ in range(max(0, int(periods))):
        value = intercept if include_mean else 0.0
        for i in range(1, p + 1):
            value += ar[i - 1] * history[-i]
        for j in range(1, q + 1):
            value += ma[j - 1] * noise[-j]
        history.append(value)
        noise.append(0.0)
        forecast_differenced.append(value)
    forecast = _integrate(forecast_differenced, original, d)

    return {
        "order": (p, d, q),
        "ar": ar,
        "ma": ma,
        "intercept": intercept,
        "coefficients": params,
        "sigma2": sigma2,
        "log_likelihood": loglik,
        "aic": aic,
        "bic": bic,
        "fitted": fitted,
        "residuals": residuals,
        "differenced": series,
        "forecast": forecast,
        "forecast_differenced": forecast_differenced,
        "n": len(original),
        "include_mean": bool(include_mean),
        "iterations": iterations,
        "converged": converged,
    }


def auto_arima(values: Iterable[Any], max_p: int = 3, max_q: int = 3,
               d: int | None = None, periods: int = 1,
               include_mean: bool = True, max_iter: int = 50) -> dict[str, Any]:
    """Select a small ARIMA order by AIC, choosing ``d`` by ADF when omitted."""
    original = _nums(values)
    if len(original) < 8:
        raise ValueError("auto_arima requires at least eight observations")
    if d is None:
        from .inference import adf_test

        chosen_d = 0
        work = list(original)
        while chosen_d < 2:
            try:
                if adf_test(work, 1)["stationary"]:
                    break
            except ValueError:
                break
            work = _difference(work, 1)
            chosen_d += 1
        d = chosen_d
    d = max(0, int(d))
    candidates = []
    for p in range(max(0, int(max_p)) + 1):
        for q in range(max(0, int(max_q)) + 1):
            try:
                model = arima(original, p, d, q, periods, include_mean, max_iter)
            except ValueError:
                continue
            candidates.append({
                "order": (p, d, q),
                "aic": model["aic"],
                "bic": model["bic"],
            })
    if not candidates:
        raise ValueError("no ARIMA order could be fitted")
    best = min(candidates, key=lambda item: item["aic"])
    model = arima(original, *best["order"], periods, include_mean, max_iter)
    model["candidates"] = sorted(candidates, key=lambda item: item["aic"])
    model["selection"] = "aic"
    return model


# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------

def build_modeling_namespace() -> dict[str, Any]:
    return {
        "glm": glm,
        "logistic_regression": logistic_regression,
        "poisson_regression": poisson_regression,
        "predict_glm": predict_glm,
        "ridge_regression": ridge_regression,
        "lasso_regression": lasso_regression,
        "elastic_net": elastic_net,
        "kaplan_meier": kaplan_meier,
        "log_rank_test": log_rank_test,
        "cox_proportional_hazards": cox_proportional_hazards,
        "concordance_index": concordance_index,
        "arima": arima,
        "auto_arima": auto_arima,
    }
