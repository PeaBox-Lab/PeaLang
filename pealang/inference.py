"""Statistical inference, regression diagnostics and time-series analysis.

This module is the decision-making layer that sits on top of
:mod:`pealang.numerics`. It provides confidence intervals, effect sizes, power
analysis, multiple-comparison correction, parametric and nonparametric tests,
ordinary least squares with full diagnostics, and list-based time-series tools
(ACF/PACF, stationarity, Holt-Winters, decomposition and change-point
detection). Everything is pure Python and dependency-free.
"""

from __future__ import annotations

import math
import random
from typing import Any, Iterable, Sequence

from .numerics import (
    _nums,
    _pairs,
    _rank,
    mean,
    median,
    variance,
    std,
    skew,
    kurtosis,
    quantile,
    t_cdf,
    t_ppf,
    f_cdf,
    f_ppf,
    normal_cdf,
    normal_ppf,
    chi2_cdf,
    chi2_ppf,
    binomial_cdf,
    dot,
    inverse,
    matmul,
    transpose,
)


# ---------------------------------------------------------------------------
# Estimation and confidence intervals
# ---------------------------------------------------------------------------

def standard_error(values: Iterable[Any]) -> float | None:
    vals = _nums(values)
    return std(vals) / math.sqrt(len(vals)) if len(vals) > 1 else None


def confidence_interval_mean(values: Iterable[Any], confidence: float = 0.95) -> dict[str, Any]:
    """Student-t confidence interval for a population mean."""
    vals = _nums(values)
    n = len(vals)
    if n < 2:
        raise ValueError("confidence interval requires at least two values")
    confidence = float(confidence)
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    estimate = mean(vals)
    se = std(vals) / math.sqrt(n)
    critical = t_ppf(1.0 - (1.0 - confidence) / 2.0, n - 1)
    return {
        "estimate": estimate,
        "low": estimate - critical * se,
        "high": estimate + critical * se,
        "se": se,
        "df": n - 1,
        "n": n,
        "confidence": confidence,
    }


def confidence_interval_proportion(successes: int, n: int, confidence: float = 0.95) -> dict[str, Any]:
    """Wilson score interval for a binomial proportion."""
    n = int(n)
    successes = int(successes)
    if n <= 0 or not 0 <= successes <= n:
        raise ValueError("successes must be between 0 and n, with n > 0")
    confidence = float(confidence)
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    p = successes / n
    z = normal_ppf(1.0 - (1.0 - confidence) / 2.0)
    denominator = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denominator
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denominator
    return {
        "estimate": p,
        "low": max(0.0, center - half),
        "high": min(1.0, center + half),
        "n": n,
        "confidence": confidence,
    }


def confidence_interval_diff_means(a: Iterable[Any], b: Iterable[Any],
                                   confidence: float = 0.95) -> dict[str, Any]:
    """Welch confidence interval for the difference of two means."""
    x, y = _nums(a), _nums(b)
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        raise ValueError("each sample requires at least two values")
    confidence = float(confidence)
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    vx, vy = variance(x), variance(y)
    estimate = mean(x) - mean(y)
    se = math.sqrt(vx / nx + vy / ny)
    df = (vx / nx + vy / ny) ** 2 / ((vx / nx) ** 2 / (nx - 1) + (vy / ny) ** 2 / (ny - 1))
    critical = t_ppf(1.0 - (1.0 - confidence) / 2.0, df)
    return {
        "estimate": estimate,
        "low": estimate - critical * se,
        "high": estimate + critical * se,
        "se": se,
        "df": df,
        "confidence": confidence,
    }


def margin_of_error(values: Iterable[Any], confidence: float = 0.95) -> float | None:
    interval = confidence_interval_mean(values, confidence)
    return (interval["high"] - interval["low"]) / 2.0


def bootstrap_ci(values: Iterable[Any], statistic: str = "mean", samples: int = 1000,
                 confidence: float = 0.95, seed: Any = None) -> dict[str, Any]:
    """Percentile bootstrap confidence interval for a statistic."""
    vals = _nums(values)
    if not vals:
        raise ValueError("values are required")
    confidence = float(confidence)
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    fn = {"mean": mean, "median": median, "std": std}.get(str(statistic), mean)
    rng = random.Random(seed)
    estimates = []
    for _ in range(max(1, int(samples))):
        draw = [rng.choice(vals) for _ in vals]
        value = fn(draw)
        if value is not None:
            estimates.append(value)
    estimates.sort()
    tail = (1.0 - confidence) / 2.0
    return {
        "statistic": str(statistic),
        "estimate": fn(vals),
        "low": quantile(estimates, tail),
        "high": quantile(estimates, 1.0 - tail),
        "samples": len(estimates),
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Effect sizes and power
# ---------------------------------------------------------------------------

def cohens_d(a: Iterable[Any], b: Iterable[Any]) -> float | None:
    """Standardized mean difference using the pooled standard deviation."""
    x, y = _nums(a), _nums(b)
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return None
    pooled = math.sqrt(((nx - 1) * variance(x) + (ny - 1) * variance(y)) / (nx + ny - 2))
    return (mean(x) - mean(y)) / pooled if pooled else 0.0


def hedges_g(a: Iterable[Any], b: Iterable[Any]) -> float | None:
    """Small-sample corrected Cohen's d."""
    d = cohens_d(a, b)
    if d is None:
        return None
    nx, ny = len(_nums(a)), len(_nums(b))
    correction = 1.0 - 3.0 / (4.0 * (nx + ny) - 9.0)
    return d * correction


def eta_squared(*groups: Iterable[Any]) -> float | None:
    """Proportion of variance explained by group membership (one-way)."""
    samples = [_nums(group) for group in groups]
    samples = [sample for sample in samples if sample]
    if len(samples) < 2:
        return None
    combined = [value for sample in samples for value in sample]
    grand = mean(combined)
    ss_between = sum(len(sample) * (mean(sample) - grand) ** 2 for sample in samples)
    ss_total = sum((value - grand) ** 2 for value in combined)
    return ss_between / ss_total if ss_total else 0.0


def power_t_test(effect_size: float, n_per_group: int, alpha: float = 0.05) -> float:
    """Approximate power of a two-sample t-test (normal approximation)."""
    d = abs(float(effect_size))
    n = max(1, int(n_per_group))
    alpha = float(alpha)
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be between 0 and 1")
    if d == 0.0:
        return alpha
    z = d * math.sqrt(n / 2.0)
    critical = normal_ppf(1.0 - alpha / 2.0)
    return normal_cdf(z - critical) + normal_cdf(-z - critical)


def sample_size_t_test(effect_size: float, power: float = 0.8, alpha: float = 0.05,
                       max_n: int = 1_000_000) -> int | None:
    """Smallest per-group sample size reaching the target power."""
    d = abs(float(effect_size))
    if d == 0.0:
        return None
    target = float(power)
    if not 0.0 < target < 1.0:
        raise ValueError("power must be between 0 and 1")
    low, high = 2, max(2, int(max_n))
    if power_t_test(d, high, alpha) < target:
        return None
    while low < high:
        mid = (low + high) // 2
        if power_t_test(d, mid, alpha) >= target:
            high = mid
        else:
            low = mid + 1
    return low


# ---------------------------------------------------------------------------
# Multiple comparisons
# ---------------------------------------------------------------------------

def adjust_p_values(p_values: Sequence[Any], method: str = "bh",
                    alpha: float = 0.05) -> dict[str, Any]:
    """Adjust p-values for multiple comparisons.

    Supported methods: ``bonferroni``, ``holm`` and ``bh`` (Benjamini-Hochberg).
    """
    ps = [float(p) for p in p_values]
    m = len(ps)
    if m == 0:
        return {"method": str(method), "alpha": float(alpha), "results": []}
    key = str(method).lower()
    adjusted = [0.0] * m
    if key in ("bonferroni", "bonf"):
        adjusted = [min(1.0, p * m) for p in ps]
    elif key == "holm":
        order = sorted(range(m), key=lambda i: ps[i])
        previous = 0.0
        for rank, index in enumerate(order):
            value = min(1.0, ps[index] * (m - rank))
            previous = max(previous, value)
            adjusted[index] = previous
    elif key in ("bh", "fdr", "benjamini-hochberg"):
        order = sorted(range(m), key=lambda i: ps[i])
        previous = 1.0
        for rank in range(m - 1, -1, -1):
            index = order[rank]
            value = min(1.0, ps[index] * m / (rank + 1))
            previous = min(previous, value)
            adjusted[index] = previous
    else:
        raise ValueError("Unknown correction method: " + str(method))
    return {
        "method": str(method),
        "alpha": float(alpha),
        "results": [
            {"p": ps[i], "adjusted": adjusted[i], "rejected": adjusted[i] <= float(alpha)}
            for i in range(m)
        ],
    }


def multiple_comparison(p_values: Sequence[Any], method: str = "bh",
                        alpha: float = 0.05) -> dict[str, Any]:
    return adjust_p_values(p_values, method, alpha)


# ---------------------------------------------------------------------------
# Parametric tests
# ---------------------------------------------------------------------------

def z_test_1samp(values: Iterable[Any], popmean: float = 0.0,
                 popstd: float = 1.0) -> dict[str, Any]:
    vals = _nums(values)
    n = len(vals)
    if n < 1:
        raise ValueError("values are required")
    popstd = float(popstd)
    if popstd <= 0:
        raise ValueError("popstd must be positive")
    estimate = mean(vals)
    se = popstd / math.sqrt(n)
    z = (estimate - float(popmean)) / se
    return {
        "z": z,
        "p_value": 2.0 * (1.0 - normal_cdf(abs(z))),
        "mean": estimate,
        "se": se,
        "n": n,
    }


def proportion_test(successes: int, n: int, p0: float = 0.5) -> dict[str, Any]:
    """One-sample z-test for a proportion against a null proportion."""
    n = int(n)
    successes = int(successes)
    if n <= 0 or not 0 <= successes <= n:
        raise ValueError("successes must be between 0 and n, with n > 0")
    p0 = float(p0)
    if not 0.0 < p0 < 1.0:
        raise ValueError("p0 must be between 0 and 1")
    phat = successes / n
    se = math.sqrt(p0 * (1.0 - p0) / n)
    z = (phat - p0) / se if se else 0.0
    return {
        "z": z,
        "p_value": 2.0 * (1.0 - normal_cdf(abs(z))),
        "estimate": phat,
        "null": p0,
        "n": n,
    }


def z_test_proportions(successes_a: int, n_a: int, successes_b: int,
                       n_b: int) -> dict[str, Any]:
    """Two-sample z-test for the difference of proportions (pooled)."""
    n_a, n_b = int(n_a), int(n_b)
    successes_a, successes_b = int(successes_a), int(successes_b)
    if n_a <= 0 or n_b <= 0:
        raise ValueError("sample sizes must be positive")
    if not 0 <= successes_a <= n_a or not 0 <= successes_b <= n_b:
        raise ValueError("successes must be within their sample sizes")
    p_a, p_b = successes_a / n_a, successes_b / n_b
    pooled = (successes_a + successes_b) / (n_a + n_b)
    se = math.sqrt(pooled * (1.0 - pooled) * (1.0 / n_a + 1.0 / n_b))
    z = (p_a - p_b) / se if se else 0.0
    return {
        "z": z,
        "p_value": 2.0 * (1.0 - normal_cdf(abs(z))),
        "p_a": p_a,
        "p_b": p_b,
        "difference": p_a - p_b,
    }


def fisher_exact(a: int, b: int, c: int, d: int) -> dict[str, Any]:
    """Two-sided Fisher exact test for a 2x2 table ``[[a, b], [c, d]]``."""
    a, b, c, d = int(a), int(b), int(c), int(d)
    if min(a, b, c, d) < 0:
        raise ValueError("counts must be non-negative")
    row1, row2 = a + b, c + d
    col1 = a + c
    total = row1 + row2
    if total == 0:
        raise ValueError("table must contain positive counts")

    def probability(x: int) -> float:
        return math.comb(row1, x) * math.comb(row2, col1 - x) / math.comb(total, col1)

    observed = probability(a)
    low = max(0, col1 - row2)
    high = min(row1, col1)
    p_value = 0.0
    for x in range(low, high + 1):
        value = probability(x)
        if value <= observed * (1.0 + 1e-9):
            p_value += value
    odds_ratio = (a * d) / (b * c) if b * c else float("inf")
    return {
        "odds_ratio": odds_ratio,
        "p_value": min(1.0, p_value),
        "table": [[a, b], [c, d]],
    }


def chi_square_goodness_of_fit(observed: Iterable[Any],
                               expected: Iterable[Any] | None = None) -> dict[str, Any]:
    obs = [float(value) for value in observed]
    if not obs:
        raise ValueError("observed values are required")
    if expected is None:
        exp = [sum(obs) / len(obs)] * len(obs)
    else:
        exp = [float(value) for value in expected]
        if len(exp) != len(obs):
            raise ValueError("observed and expected lengths must match")
    if any(value <= 0 for value in exp):
        raise ValueError("expected values must be positive")
    statistic = sum((o - e) ** 2 / e for o, e in zip(obs, exp))
    df = len(obs) - 1
    return {
        "chi2": statistic,
        "df": df,
        "p_value": 1.0 - chi2_cdf(statistic, df),
    }


# ---------------------------------------------------------------------------
# Nonparametric tests
# ---------------------------------------------------------------------------

def mann_whitney_u(a: Iterable[Any], b: Iterable[Any]) -> dict[str, Any]:
    """Mann-Whitney U test with tie correction and normal approximation."""
    x, y = _nums(a), _nums(b)
    n1, n2 = len(x), len(y)
    if n1 < 1 or n2 < 1:
        raise ValueError("each sample requires at least one value")
    combined = x + y
    ranks = _rank(combined)
    r1 = sum(ranks[:n1])
    u1 = r1 - n1 * (n1 + 1) / 2.0
    u2 = n1 * n2 - u1
    u = min(u1, u2)
    n = n1 + n2
    counts: dict[float, int] = {}
    for value in combined:
        counts[value] = counts.get(value, 0) + 1
    tie_sum = sum(t ** 3 - t for t in counts.values() if t > 1)
    variance_u = n1 * n2 / 12.0 * ((n + 1) - tie_sum / (n * (n - 1))) if n > 1 else 0.0
    if variance_u > 0:
        correction = 0.5 if u < n1 * n2 / 2.0 else -0.5
        z = (u - n1 * n2 / 2.0 + correction) / math.sqrt(variance_u)
        p_value = 2.0 * (1.0 - normal_cdf(abs(z)))
    else:
        z = 0.0
        p_value = 1.0
    return {"u": u, "z": z, "p_value": p_value, "n_a": n1, "n_b": n2}


def wilcoxon_signed_rank(a: Iterable[Any], b: Iterable[Any]) -> dict[str, Any]:
    """Wilcoxon signed-rank test for paired samples (normal approximation)."""
    diffs = [x - y for x, y in _pairs(a, b) if x != y]
    n = len(diffs)
    if n < 1:
        raise ValueError("at least one non-zero paired difference is required")
    ranks = _rank([abs(value) for value in diffs])
    positive = sum(rank for rank, diff in zip(ranks, diffs) if diff > 0)
    negative = sum(rank for rank, diff in zip(ranks, diffs) if diff < 0)
    statistic = min(positive, negative)
    counts: dict[float, int] = {}
    for value in diffs:
        counts[abs(value)] = counts.get(abs(value), 0) + 1
    tie_sum = sum(t ** 3 - t for t in counts.values() if t > 1)
    variance_w = n * (n + 1) * (2 * n + 1) / 24.0 - tie_sum / 48.0
    expected = n * (n + 1) / 4.0
    if variance_w > 0:
        z = (statistic - expected) / math.sqrt(variance_w)
        p_value = 2.0 * normal_cdf(z)
    else:
        z = 0.0
        p_value = 1.0
    return {"statistic": statistic, "z": z, "p_value": min(1.0, p_value), "n": n}


def kruskal_wallis(*groups: Iterable[Any]) -> dict[str, Any]:
    """Kruskal-Wallis H test with tie correction."""
    samples = [_nums(group) for group in groups]
    samples = [sample for sample in samples if sample]
    if len(samples) < 2:
        raise ValueError("kruskal-wallis requires at least two groups")
    combined = [value for sample in samples for value in sample]
    n = len(combined)
    ranks = _rank(combined)
    offset = 0
    h = 0.0
    for sample in samples:
        group_ranks = ranks[offset:offset + len(sample)]
        offset += len(sample)
        h += sum(group_ranks) ** 2 / len(sample)
    h = 12.0 / (n * (n + 1)) * h - 3.0 * (n + 1)
    counts: dict[float, int] = {}
    for value in combined:
        counts[value] = counts.get(value, 0) + 1
    tie_sum = sum(t ** 3 - t for t in counts.values() if t > 1)
    correction = 1.0 - tie_sum / (n ** 3 - n) if n > 1 else 1.0
    if correction > 0:
        h /= correction
    df = len(samples) - 1
    return {"h": h, "df": df, "p_value": 1.0 - chi2_cdf(h, df)}


def friedman_test(*groups: Iterable[Any]) -> dict[str, Any]:
    """Friedman test for repeated measures across treatments."""
    samples = [_nums(group) for group in groups]
    if len(samples) < 2:
        raise ValueError("friedman test requires at least two treatments")
    blocks = min(len(sample) for sample in samples)
    if blocks < 2:
        raise ValueError("each treatment requires at least two blocks")
    k = len(samples)
    rank_sums = [0.0] * k
    for i in range(blocks):
        values = [sample[i] for sample in samples]
        ranks = _rank(values)
        for j, rank in enumerate(ranks):
            rank_sums[j] += rank
    statistic = 12.0 / (blocks * k * (k + 1)) * sum(value ** 2 for value in rank_sums) - 3.0 * blocks * (k + 1)
    df = k - 1
    return {"chi2": statistic, "df": df, "p_value": 1.0 - chi2_cdf(statistic, df)}


def sign_test(a: Iterable[Any], b: Iterable[Any]) -> dict[str, Any]:
    """Two-sided sign test for paired samples."""
    positive = negative = 0
    for x, y in _pairs(a, b):
        if x > y:
            positive += 1
        elif x < y:
            negative += 1
    n = positive + negative
    if n == 0:
        return {"positive": 0, "negative": 0, "n": 0, "p_value": 1.0}
    p_value = min(1.0, 2.0 * binomial_cdf(min(positive, negative), n, 0.5))
    return {"positive": positive, "negative": negative, "n": n, "p_value": p_value}


# ---------------------------------------------------------------------------
# Normality
# ---------------------------------------------------------------------------

def jarque_bera(values: Iterable[Any]) -> dict[str, Any]:
    """Jarque-Bera normality test based on skewness and kurtosis."""
    vals = _nums(values)
    n = len(vals)
    if n < 4:
        raise ValueError("jarque-bera requires at least four values")
    s = skew(vals) or 0.0
    k = kurtosis(vals) or 0.0
    statistic = n / 6.0 * (s * s + (k * k) / 4.0)
    return {
        "statistic": statistic,
        "df": 2,
        "p_value": 1.0 - chi2_cdf(statistic, 2),
        "skew": s,
        "kurtosis": k,
    }


def normality_test(values: Iterable[Any]) -> dict[str, Any]:
    return jarque_bera(values)


# ---------------------------------------------------------------------------
# Permutation tests
# ---------------------------------------------------------------------------

def permutation_test(a: Iterable[Any], b: Iterable[Any], statistic: str = "mean",
                     samples: int = 1000, seed: Any = None) -> dict[str, Any]:
    """Two-sample permutation test for a difference statistic."""
    x, y = _nums(a), _nums(b)
    if not x or not y:
        raise ValueError("both samples are required")

    def compute(left, right):
        if statistic == "median":
            return median(left) - median(right)
        if statistic == "std":
            return (std(left) or 0.0) - (std(right) or 0.0)
        return mean(left) - mean(right)

    observed = compute(x, y)
    combined = x + y
    n = len(x)
    rng = random.Random(seed)
    count = 0
    total = max(1, int(samples))
    for _ in range(total):
        rng.shuffle(combined)
        if abs(compute(combined[:n], combined[n:])) >= abs(observed):
            count += 1
    return {
        "statistic": observed,
        "p_value": (count + 1) / (total + 1),
        "samples": total,
    }


# ---------------------------------------------------------------------------
# Ordinary least squares and regression diagnostics
# ---------------------------------------------------------------------------

def ols(features: Any, target: Iterable[Any], names: Sequence[str] | None = None,
        confidence: float = 0.95) -> dict[str, Any]:
    """Ordinary least squares with standard errors, t-tests and diagnostics.

    ``features`` is a list of rows (each a list of numeric predictors) and
    ``target`` is the response vector. An intercept is added automatically.
    """
    rows = [[float(value) for value in row] for row in (features or [])]
    y = [float(value) for value in (target or [])]
    n = len(rows)
    if n != len(y):
        raise ValueError("features and target lengths must match")
    if n == 0:
        raise ValueError("features and target are required")
    p = len(rows[0])
    if p == 0 or any(len(row) != p for row in rows):
        raise ValueError("feature rows must be non-empty and equal length")
    design = [[1.0] + row for row in rows]
    k = p + 1
    if n <= k:
        raise ValueError("ols requires more observations than parameters")
    xtx = matmul(transpose(design), design)
    xtx_inv = inverse(xtx)
    xty = [dot(column, y) for column in transpose(design)]
    beta = [dot(row, xty) for row in xtx_inv]
    fitted = [dot(row, beta) for row in design]
    residuals = [actual - predicted for actual, predicted in zip(y, fitted)]
    rss = sum(value * value for value in residuals)
    ybar = mean(y)
    tss = sum((value - ybar) ** 2 for value in y)
    df_resid = n - k
    sigma2 = rss / df_resid
    sigma = math.sqrt(sigma2)
    covariance = [[sigma2 * xtx_inv[i][j] for j in range(k)] for i in range(k)]
    se = [math.sqrt(max(covariance[i][i], 0.0)) for i in range(k)]
    t_stats = [beta[i] / se[i] if se[i] else 0.0 for i in range(k)]
    p_values = [2.0 * (1.0 - t_cdf(abs(value), df_resid)) for value in t_stats]
    critical = t_ppf(1.0 - (1.0 - float(confidence)) / 2.0, df_resid)
    ci_low = [beta[i] - critical * se[i] for i in range(k)]
    ci_high = [beta[i] + critical * se[i] for i in range(k)]
    r2 = 1.0 - rss / tss if tss else 1.0
    adj_r2 = 1.0 - (1.0 - r2) * (n - 1) / df_resid if df_resid else r2
    df_model = k - 1
    if df_model > 0 and rss > 0:
        f_stat = (tss - rss) / df_model / (rss / df_resid)
        f_p = 1.0 - f_cdf(f_stat, df_model, df_resid)
    else:
        f_stat = None
        f_p = None
    if rss > 0:
        aic = n * math.log(rss / n) + 2 * k
        bic = n * math.log(rss / n) + k * math.log(n)
    else:
        aic = bic = None
    if rss > 0:
        durbin_watson = sum((residuals[i] - residuals[i - 1]) ** 2 for i in range(1, n)) / rss
    else:
        durbin_watson = None
    labels = list(names) if names is not None else ["x" + str(i + 1) for i in range(p)]
    if len(labels) != p:
        raise ValueError("names length must match the number of features")
    labels = ["intercept"] + labels
    table = [
        {
            "term": labels[i],
            "coefficient": beta[i],
            "std_error": se[i],
            "t": t_stats[i],
            "p_value": p_values[i],
            "ci_low": ci_low[i],
            "ci_high": ci_high[i],
        }
        for i in range(k)
    ]
    return {
        "coefficients": beta,
        "intercept": beta[0],
        "slopes": beta[1:],
        "std_errors": se,
        "t_values": t_stats,
        "p_values": p_values,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "table": table,
        "fitted": fitted,
        "residuals": residuals,
        "r_squared": r2,
        "adj_r_squared": adj_r2,
        "f_statistic": f_stat,
        "f_p_value": f_p,
        "aic": aic,
        "bic": bic,
        "durbin_watson": durbin_watson,
        "sigma": sigma,
        "df_resid": df_resid,
        "n": n,
        "names": labels,
        "xtx_inv": xtx_inv,
        "covariance": covariance,
        "confidence": float(confidence),
    }


def predict_ols(model: dict[str, Any], features: Any,
                confidence: float = 0.95) -> dict[str, Any]:
    """Prediction intervals from a fitted OLS model."""
    rows = [[float(value) for value in row] for row in (features or [])]
    beta = model["coefficients"]
    xtx_inv = model["xtx_inv"]
    sigma = model["sigma"]
    df_resid = model["df_resid"]
    critical = t_ppf(1.0 - (1.0 - float(confidence)) / 2.0, df_resid)
    predicted = []
    low = []
    high = []
    se_mean = []
    se_pred = []
    for row in rows:
        design = [1.0] + row
        estimate = dot(design, beta)
        quadratic = sum(
            design[i] * xtx_inv[i][j] * design[j]
            for i in range(len(design))
            for j in range(len(design))
        )
        mean_se = sigma * math.sqrt(max(quadratic, 0.0))
        prediction_se = sigma * math.sqrt(max(1.0 + quadratic, 0.0))
        predicted.append(estimate)
        se_mean.append(mean_se)
        se_pred.append(prediction_se)
        low.append(estimate - critical * prediction_se)
        high.append(estimate + critical * prediction_se)
    return {
        "predicted": predicted,
        "low": low,
        "high": high,
        "se_mean": se_mean,
        "se_prediction": se_pred,
        "confidence": float(confidence),
    }


def variance_inflation_factors(features: Any, names: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """Variance inflation factors for each predictor."""
    rows = [[float(value) for value in row] for row in (features or [])]
    if not rows:
        return []
    p = len(rows[0])
    labels = list(names) if names is not None else ["x" + str(i + 1) for i in range(p)]
    if p == 1:
        return [{"term": labels[0], "vif": 1.0}]
    out = []
    for j in range(p):
        y = [row[j] for row in rows]
        others = [[row[i] for i in range(p) if i != j] for row in rows]
        r2 = ols(others, y)["r_squared"]
        vif = 1.0 / (1.0 - r2) if r2 < 1.0 else float("inf")
        out.append({"term": labels[j], "vif": vif})
    return out


def residual_diagnostics(residuals: Iterable[Any]) -> dict[str, Any]:
    """Summarize residuals, including a Jarque-Bera normality check."""
    vals = _nums(residuals)
    result = {
        "mean": mean(vals),
        "std": std(vals),
        "skew": skew(vals),
        "kurtosis": kurtosis(vals),
        "normality_p": None,
    }
    if len(vals) >= 4:
        result["normality_p"] = jarque_bera(vals)["p_value"]
    return result


# ---------------------------------------------------------------------------
# Time series
# ---------------------------------------------------------------------------

def acf(values: Iterable[Any], nlags: int = 20) -> list[float]:
    """Autocorrelation function (biased estimator, lag 0 = 1)."""
    vals = _nums(values)
    n = len(vals)
    if n < 2:
        return [1.0] if n == 1 else []
    center = mean(vals)
    denominator = sum((value - center) ** 2 for value in vals)
    lags = min(max(0, int(nlags)), n - 1)
    if denominator == 0:
        return [0.0] * (lags + 1)
    return [
        sum((vals[i] - center) * (vals[i + k] - center) for i in range(n - k)) / denominator
        for k in range(lags + 1)
    ]


def pacf(values: Iterable[Any], nlags: int = 20) -> list[float]:
    """Partial autocorrelation function via Durbin-Levinson recursion."""
    correlations = acf(values, nlags)
    if not correlations:
        return []
    order = len(correlations) - 1
    if order == 0:
        return [1.0]
    phi = [[0.0] * (order + 1) for _ in range(order + 1)]
    out = [1.0]
    for k in range(1, order + 1):
        numerator = correlations[k] - sum(phi[k - 1][j] * correlations[k - j] for j in range(1, k))
        denominator = 1.0 - sum(phi[k - 1][j] * correlations[j] for j in range(1, k))
        phi[k][k] = numerator / denominator if denominator else 0.0
        for j in range(1, k):
            phi[k][j] = phi[k - 1][j] - phi[k][k] * phi[k - 1][k - j]
        out.append(phi[k][k])
    return out


def ljung_box(values: Iterable[Any], lags: int = 10) -> dict[str, Any]:
    """Ljung-Box test for autocorrelation in a time series."""
    correlations = acf(values, lags)
    vals = _nums(values)
    n = len(vals)
    h = min(int(lags), len(correlations) - 1)
    if n < 2 or h < 1:
        raise ValueError("not enough observations for the requested lags")
    statistic = n * (n + 2) * sum(correlations[k] ** 2 / (n - k) for k in range(1, h + 1))
    return {
        "statistic": statistic,
        "df": h,
        "p_value": 1.0 - chi2_cdf(statistic, h),
        "acf": correlations,
    }


def difference_series(values: Iterable[Any], order: int = 1,
                      seasonal: int | None = None) -> list[float]:
    """Apply regular or seasonal differencing."""
    out = _nums(values)
    if seasonal:
        m = int(seasonal)
        if m < 1:
            raise ValueError("seasonal period must be positive")
        for _ in range(max(1, int(order))):
            out = [out[i] - out[i - m] for i in range(m, len(out))]
    else:
        for _ in range(max(1, int(order))):
            out = [out[i] - out[i - 1] for i in range(1, len(out))]
    return out


def moving_average(values: Iterable[Any], window: int = 3) -> list[float | None]:
    vals = _nums(values)
    width = max(1, int(window))
    return [mean(vals[max(0, i - width + 1):i + 1]) if vals[max(0, i - width + 1):i + 1] else None
            for i in range(len(vals))]


def simple_exponential_smoothing(values: Iterable[Any], alpha: float = 0.3,
                                 periods: int = 1) -> dict[str, Any]:
    vals = _nums(values)
    alpha = float(alpha)
    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must be in (0, 1]")
    if not vals:
        raise ValueError("values are required")
    level = vals[0]
    fitted = [level]
    for value in vals[1:]:
        level = alpha * value + (1.0 - alpha) * level
        fitted.append(level)
    return {
        "level": level,
        "fitted": fitted,
        "forecast": [level] * max(0, int(periods)),
    }


def holt_linear(values: Iterable[Any], alpha: float = 0.3, beta: float = 0.1,
                periods: int = 1) -> dict[str, Any]:
    """Holt's linear trend exponential smoothing."""
    vals = _nums(values)
    if len(vals) < 2:
        raise ValueError("holt linear requires at least two values")
    alpha, beta = float(alpha), float(beta)
    if not 0.0 < alpha <= 1.0 or not 0.0 < beta <= 1.0:
        raise ValueError("alpha and beta must be in (0, 1]")
    level = vals[0]
    trend = vals[1] - vals[0]
    fitted = [level]
    for value in vals[1:]:
        previous = level
        level = alpha * value + (1.0 - alpha) * (level + trend)
        trend = beta * (level - previous) + (1.0 - beta) * trend
        fitted.append(level + trend)
    forecast = [level + (step + 1) * trend for step in range(max(0, int(periods)))]
    return {"level": level, "trend": trend, "fitted": fitted, "forecast": forecast}


def holt_winters(values: Iterable[Any], season_length: int, alpha: float = 0.3,
                 beta: float = 0.1, gamma: float = 0.3, periods: int = 1) -> dict[str, Any]:
    """Additive Holt-Winters exponential smoothing."""
    vals = _nums(values)
    m = int(season_length)
    if m < 2:
        raise ValueError("season_length must be at least two")
    if len(vals) < 2 * m:
        raise ValueError("at least two seasonal periods are required")
    alpha, beta, gamma = float(alpha), float(beta), float(gamma)
    if not 0.0 < alpha <= 1.0 or not 0.0 < beta <= 1.0 or not 0.0 < gamma <= 1.0:
        raise ValueError("alpha, beta and gamma must be in (0, 1]")
    level = mean(vals[:m])
    trend = (mean(vals[m:2 * m]) - mean(vals[:m])) / m
    seasonals = [vals[i] - level for i in range(m)]
    fitted = []
    for i, value in enumerate(vals):
        seasonal = seasonals[i % m]
        fitted.append(level + trend + seasonal)
        previous = level
        level = alpha * (value - seasonal) + (1.0 - alpha) * (level + trend)
        trend = beta * (level - previous) + (1.0 - beta) * trend
        seasonals[i % m] = gamma * (value - level) + (1.0 - gamma) * seasonal
    forecast = [
        level + step * trend + seasonals[(len(vals) + step - 1) % m]
        for step in range(1, max(0, int(periods)) + 1)
    ]
    return {
        "level": level,
        "trend": trend,
        "seasonal": seasonals,
        "fitted": fitted,
        "forecast": forecast,
    }


def seasonal_decompose(values: Iterable[Any], period: int) -> dict[str, Any]:
    """Additive seasonal decomposition into trend, seasonal and residual."""
    vals = _nums(values)
    p = int(period)
    if p < 2 or len(vals) < 2 * p:
        raise ValueError("at least two seasonal periods are required")
    trend = []
    for i in range(len(vals)):
        low = max(0, i - p // 2)
        high = min(len(vals), i + p // 2 + 1)
        trend.append(mean(vals[low:high]))
    detrended = [value - trend_value for value, trend_value in zip(vals, trend)]
    pattern = [mean(detrended[i::p]) for i in range(p)]
    center = mean(pattern)
    pattern = [value - center for value in pattern]
    seasonal = [pattern[i % p] for i in range(len(vals))]
    residual = [value - trend_value - seasonal_value
                for value, trend_value, seasonal_value in zip(vals, trend, seasonal)]
    return {
        "trend": trend,
        "seasonal": seasonal,
        "residual": residual,
        "pattern": pattern,
    }


def changepoint_cusum(values: Iterable[Any], threshold: float = 1.0) -> dict[str, Any]:
    """Detect a mean shift using a standardized CUSUM statistic."""
    vals = _nums(values)
    if len(vals) < 3:
        raise ValueError("at least three values are required")
    center = mean(vals)
    scale = std(vals) or 1.0
    limit = float(threshold) * math.sqrt(len(vals))
    cusum = []
    total = 0.0
    maximum = 0.0
    changepoint = None
    for i, value in enumerate(vals):
        total += (value - center) / scale
        cusum.append(total)
        if abs(total) > maximum:
            maximum = abs(total)
            changepoint = i
    if maximum <= limit:
        changepoint = None
    return {"changepoint": changepoint, "statistic": maximum, "cusum": cusum}


def adf_test(values: Iterable[Any], max_lag: int = 1) -> dict[str, Any]:
    """Augmented Dickey-Fuller stationarity test (constant, fixed lags).

    Returns the t-statistic for the unit-root coefficient and the usual
    MacKinnon critical values. ``stationary`` is True when the statistic is
    below the 5% critical value.
    """
    vals = _nums(values)
    n = len(vals)
    lag = max(1, int(max_lag))
    if n < lag + 8:
        raise ValueError("at least lag + 8 observations are required")
    rows = []
    targets = []
    for t in range(lag + 1, n):
        rows.append([vals[t - 1]] + [vals[t - i] - vals[t - i - 1] for i in range(1, lag + 1)])
        targets.append(vals[t] - vals[t - 1])
    try:
        model = ols(rows, targets, names=["y_lag"] + ["dy_lag" + str(i) for i in range(1, lag + 1)])
    except ValueError as exc:
        raise ValueError("adf_test requires a non-degenerate series: " + str(exc)) from exc
    statistic = model["table"][1]["t"]
    critical = {"1%": -3.43, "5%": -2.86, "10%": -2.57}
    return {
        "statistic": statistic,
        "critical": critical,
        "stationary": statistic < critical["5%"],
        "df": model["df_resid"],
        "n": len(targets),
    }


# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------

def build_inference_namespace() -> dict[str, Any]:
    return {
        # estimation
        "standard_error": standard_error,
        "confidence_interval_mean": confidence_interval_mean,
        "confidence_interval_proportion": confidence_interval_proportion,
        "confidence_interval_diff_means": confidence_interval_diff_means,
        "margin_of_error": margin_of_error,
        "bootstrap_ci": bootstrap_ci,
        # effect sizes and power
        "cohens_d": cohens_d,
        "hedges_g": hedges_g,
        "eta_squared": eta_squared,
        "power_t_test": power_t_test,
        "sample_size_t_test": sample_size_t_test,
        # multiple comparisons
        "adjust_p_values": adjust_p_values,
        "multiple_comparison": multiple_comparison,
        # parametric tests
        "z_test_1samp": z_test_1samp,
        "proportion_test": proportion_test,
        "z_test_proportions": z_test_proportions,
        "fisher_exact": fisher_exact,
        "chi_square_goodness_of_fit": chi_square_goodness_of_fit,
        # nonparametric tests
        "mann_whitney_u": mann_whitney_u,
        "wilcoxon_signed_rank": wilcoxon_signed_rank,
        "kruskal_wallis": kruskal_wallis,
        "friedman_test": friedman_test,
        "sign_test": sign_test,
        # normality and resampling
        "jarque_bera": jarque_bera,
        "normality_test": normality_test,
        "permutation_test": permutation_test,
        # regression diagnostics
        "ols": ols,
        "predict_ols": predict_ols,
        "variance_inflation_factors": variance_inflation_factors,
        "residual_diagnostics": residual_diagnostics,
        # time series
        "acf": acf,
        "pacf": pacf,
        "ljung_box": ljung_box,
        "difference_series": difference_series,
        "moving_average": moving_average,
        "simple_exponential_smoothing": simple_exponential_smoothing,
        "holt_linear": holt_linear,
        "holt_winters": holt_winters,
        "seasonal_decompose": seasonal_decompose,
        "changepoint_cusum": changepoint_cusum,
        "adf_test": adf_test,
    }
