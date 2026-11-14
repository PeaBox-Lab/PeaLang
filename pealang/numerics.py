"""Dependency-free numerical, statistical and modelling toolkit for PeaLang.

The module intentionally mirrors the pieces data professionals reach for in
NumPy/SciPy/pandas and Go's gonum: descriptive statistics, vector and matrix
algebra, probability distributions, hypothesis tests, regression, clustering and
dimensionality reduction. Everything is implemented in pure Python so PeaLang
programs keep working in constrained and embedded environments.
"""

from __future__ import annotations

import math
import random
from typing import Any, Iterable, Sequence


# ---------------------------------------------------------------------------
# Coercion helpers
# ---------------------------------------------------------------------------

def _nums(values: Iterable[Any]) -> list[float]:
    out: list[float] = []
    for value in values or []:
        if value is None or isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            out.append(float(value))
            continue
        try:
            out.append(float(value))
        except (TypeError, ValueError):
            continue
    return out


def _pairs(x: Iterable[Any], y: Iterable[Any]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for a, b in zip(x or [], y or []):
        if a is None or b is None or isinstance(a, bool) or isinstance(b, bool):
            continue
        try:
            out.append((float(a), float(b)))
        except (TypeError, ValueError):
            continue
    return out


def _matrix(value: Any) -> list[list[float]]:
    rows = [list(map(float, row)) for row in value or []]
    if not rows:
        return rows
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("Matrix rows must have equal length")
    return rows


# ---------------------------------------------------------------------------
# Descriptive statistics
# ---------------------------------------------------------------------------

def mean(values: Iterable[Any]) -> float | None:
    vals = _nums(values)
    return sum(vals) / len(vals) if vals else None


def median(values: Iterable[Any]) -> float | None:
    return quantile(values, 0.5)


def mode(values: Iterable[Any]) -> Any:
    vals = [v for v in (values or []) if v is not None]
    if not vals:
        return None
    counts: dict[Any, int] = {}
    for value in vals:
        counts[value] = counts.get(value, 0) + 1
    best = max(counts.values())
    return next(value for value in vals if counts[value] == best)


def quantile(values: Iterable[Any], q: float) -> float | None:
    vals = sorted(_nums(values))
    if not vals:
        return None
    q = float(q)
    if q <= 0:
        return vals[0]
    if q >= 1:
        return vals[-1]
    position = (len(vals) - 1) * q
    low = int(position)
    high = min(low + 1, len(vals) - 1)
    return vals[low] + (vals[high] - vals[low]) * (position - low)


def percentile(values: Iterable[Any], p: float) -> float | None:
    return quantile(values, float(p) / 100.0)


def iqr(values: Iterable[Any]) -> float | None:
    q1 = quantile(values, 0.25)
    q3 = quantile(values, 0.75)
    return None if q1 is None or q3 is None else q3 - q1


def variance(values: Iterable[Any], sample: bool = True) -> float | None:
    vals = _nums(values)
    n = len(vals)
    if n < (2 if sample else 1):
        return None
    m = sum(vals) / n
    denominator = n - 1 if sample else n
    return sum((x - m) ** 2 for x in vals) / denominator


def std(values: Iterable[Any], sample: bool = True) -> float | None:
    value = variance(values, sample)
    return math.sqrt(value) if value is not None else None


def skew(values: Iterable[Any]) -> float | None:
    vals = _nums(values)
    n = len(vals)
    if n < 3:
        return None
    m = sum(vals) / n
    s2 = sum((x - m) ** 2 for x in vals) / (n - 1)
    sd = math.sqrt(s2)
    if sd == 0:
        return 0.0
    m3 = sum((x - m) ** 3 for x in vals) / n
    return (n ** 2 / ((n - 1) * (n - 2))) * (m3 / sd ** 3)


def kurtosis(values: Iterable[Any], excess: bool = True) -> float | None:
    vals = _nums(values)
    n = len(vals)
    if n < 4:
        return None
    m = sum(vals) / n
    s2 = sum((x - m) ** 2 for x in vals) / n
    if s2 == 0:
        return 0.0
    m4 = sum((x - m) ** 4 for x in vals) / n
    value = m4 / s2 ** 2
    return value - 3.0 if excess else value


def covariance(x: Iterable[Any], y: Iterable[Any], sample: bool = True) -> float | None:
    pairs = _pairs(x, y)
    n = len(pairs)
    if n < (2 if sample else 1):
        return None
    mx = sum(a for a, _ in pairs) / n
    my = sum(b for _, b in pairs) / n
    denominator = n - 1 if sample else n
    return sum((a - mx) * (b - my) for a, b in pairs) / denominator


def pearson(x: Iterable[Any], y: Iterable[Any]) -> float | None:
    pairs = _pairs(x, y)
    if len(pairs) < 2:
        return None
    xs = [a for a, _ in pairs]
    ys = [b for _, b in pairs]
    sx = std(xs)
    sy = std(ys)
    if not sx or not sy:
        return None
    return covariance(xs, ys) / (sx * sy)


def _rank(values: Sequence[float]) -> list[float]:
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        average = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = average
        i = j + 1
    return ranks


def spearman(x: Iterable[Any], y: Iterable[Any]) -> float | None:
    pairs = _pairs(x, y)
    if len(pairs) < 2:
        return None
    return pearson(_rank([a for a, _ in pairs]), _rank([b for _, b in pairs]))


def kendall(x: Iterable[Any], y: Iterable[Any]) -> float | None:
    pairs = _pairs(x, y)
    n = len(pairs)
    if n < 2:
        return None
    concordant = discordant = ties_x = ties_y = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = pairs[i][0] - pairs[j][0]
            dy = pairs[i][1] - pairs[j][1]
            if dx == 0 and dy == 0:
                continue
            if dx == 0:
                ties_x += 1
            elif dy == 0:
                ties_y += 1
            elif (dx > 0) == (dy > 0):
                concordant += 1
            else:
                discordant += 1
    denominator = math.sqrt((concordant + discordant + ties_x) * (concordant + discordant + ties_y))
    return (concordant - discordant) / denominator if denominator else None


def entropy(values: Iterable[Any]) -> float:
    vals = [v for v in (values or []) if v is not None]
    if not vals:
        return 0.0
    counts: dict[Any, int] = {}
    for value in vals:
        counts[value] = counts.get(value, 0) + 1
    total = len(vals)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def gini(values: Iterable[Any]) -> float:
    vals = sorted(_nums(values))
    if not vals:
        return 0.0
    total = sum(vals)
    if total <= 0:
        return 0.0
    n = len(vals)
    weighted = sum((i + 1) * v for i, v in enumerate(vals))
    return (2 * weighted) / (n * total) - (n + 1) / n


# ---------------------------------------------------------------------------
# Scaling and cumulative transforms
# ---------------------------------------------------------------------------

def zscore(values: Iterable[Any]) -> list[float]:
    vals = _nums(values)
    m = mean(vals)
    s = std(vals)
    if m is None:
        return []
    s = s or 1.0
    return [(x - m) / s for x in vals]


def minmax_scale(values: Iterable[Any]) -> list[float]:
    vals = _nums(values)
    if not vals:
        return []
    low, high = min(vals), max(vals)
    span = high - low if high != low else 1.0
    return [(x - low) / span for x in vals]


def robust_scale(values: Iterable[Any]) -> list[float]:
    vals = _nums(values)
    if not vals:
        return []
    center = median(vals)
    spread = iqr(vals) or 1.0
    return [(x - center) / spread for x in vals]


def winsorize(values: Iterable[Any], lower: float = 0.05, upper: float = 0.95) -> list[float]:
    vals = _nums(values)
    if not vals:
        return []
    low = quantile(vals, lower)
    high = quantile(vals, upper)
    return [min(max(x, low), high) for x in vals]


def cumsum(values: Iterable[Any]) -> list[float]:
    total = 0.0
    out = []
    for value in _nums(values):
        total += value
        out.append(total)
    return out


def cumprod(values: Iterable[Any]) -> list[float]:
    total = 1.0
    out = []
    for value in _nums(values):
        total *= value
        out.append(total)
    return out


def cummax(values: Iterable[Any]) -> list[float]:
    out = []
    best = None
    for value in _nums(values):
        best = value if best is None else max(best, value)
        out.append(best)
    return out


def cummin(values: Iterable[Any]) -> list[float]:
    out = []
    best = None
    for value in _nums(values):
        best = value if best is None else min(best, value)
        out.append(best)
    return out


def diff(values: Iterable[Any], periods: int = 1) -> list[float | None]:
    vals = _nums(values)
    n = int(periods)
    if n <= 0:
        raise ValueError("periods must be positive")
    return [None] * n + [vals[i] - vals[i - n] for i in range(n, len(vals))]


def histogram(values: Iterable[Any], bins: int = 10) -> list[dict[str, float]]:
    vals = _nums(values)
    if not vals:
        return []
    low, high = min(vals), max(vals)
    count = max(1, int(bins))
    if high == low:
        return [{"bin_start": low, "bin_end": high, "count": float(len(vals))}]
    width = (high - low) / count
    buckets = [
        {"bin_start": low + i * width, "bin_end": low + (i + 1) * width, "count": 0.0}
        for i in range(count)
    ]
    for value in vals:
        index = min(int((value - low) / width), count - 1)
        buckets[index]["count"] += 1
    return buckets


def outliers_z(values: Iterable[Any], threshold: float = 3.0) -> list[float]:
    vals = _nums(values)
    m = mean(vals)
    s = std(vals)
    if m is None or not s:
        return []
    return [x for x in vals if abs((x - m) / s) > float(threshold)]


def percentile_rank(values: Iterable[Any], value: Any) -> float | None:
    vals = _nums(values)
    if not vals:
        return None
    target = float(value)
    below = sum(1 for x in vals if x < target)
    equal = sum(1 for x in vals if x == target)
    return (below + 0.5 * equal) / len(vals) * 100.0


def describe(values: Iterable[Any]) -> dict[str, Any]:
    vals = _nums(values)
    if not vals:
        return {"count": 0}
    return {
        "count": len(vals),
        "mean": mean(vals),
        "std": std(vals),
        "min": min(vals),
        "q1": quantile(vals, 0.25),
        "median": median(vals),
        "q3": quantile(vals, 0.75),
        "max": max(vals),
        "iqr": iqr(vals),
        "skew": skew(vals),
        "kurtosis": kurtosis(vals),
    }


# ---------------------------------------------------------------------------
# Vector and matrix algebra
# ---------------------------------------------------------------------------

def dot(a: Iterable[Any], b: Iterable[Any]) -> float:
    return sum(x * y for x, y in zip(_nums(a), _nums(b)))


def norm(a: Iterable[Any]) -> float:
    return math.sqrt(dot(a, a))


def distance(a: Iterable[Any], b: Iterable[Any]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(_nums(a), _nums(b))))


def angle(a: Iterable[Any], b: Iterable[Any]) -> float | None:
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return None
    cosine = max(-1.0, min(1.0, dot(a, b) / (na * nb)))
    return math.acos(cosine)


def add(a: Iterable[Any], b: Iterable[Any]) -> list[float]:
    return [x + y for x, y in zip(_nums(a), _nums(b))]


def sub(a: Iterable[Any], b: Iterable[Any]) -> list[float]:
    return [x - y for x, y in zip(_nums(a), _nums(b))]


def mul(a: Iterable[Any], b: Iterable[Any]) -> list[float]:
    return [x * y for x, y in zip(_nums(a), _nums(b))]


def div(a: Iterable[Any], b: Iterable[Any]) -> list[float]:
    return [x / y if y else 0.0 for x, y in zip(_nums(a), _nums(b))]


def scale(a: Iterable[Any], factor: float) -> list[float]:
    factor = float(factor)
    return [x * factor for x in _nums(a)]


def outer(a: Iterable[Any], b: Iterable[Any]) -> list[list[float]]:
    left, right = _nums(a), _nums(b)
    return [[x * y for y in right] for x in left]


def transpose(matrix: Any) -> list[list[float]]:
    rows = _matrix(matrix)
    return [list(col) for col in zip(*rows)] if rows else []


def identity(n: int) -> list[list[float]]:
    n = int(n)
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def matmul(a: Any, b: Any) -> list[list[float]]:
    left, right = _matrix(a), _matrix(b)
    if not left or not right:
        return []
    if len(left[0]) != len(right):
        raise ValueError("Matrix dimensions are incompatible for multiplication")
    bt = transpose(right)
    return [[dot(row, col) for col in bt] for row in left]


def trace(matrix: Any) -> float:
    rows = _matrix(matrix)
    return sum(rows[i][i] for i in range(min(len(rows), len(rows[0]) if rows else 0)))


def solve(a: Any, b: Any) -> list[Any]:
    """Solve the linear system ``A x = b`` with partial-pivoted Gauss-Jordan."""
    matrix = _matrix(a)
    n = len(matrix)
    if n == 0 or len(matrix[0]) != n:
        raise ValueError("solve requires a square matrix")
    matrix_rhs = bool(b) and isinstance(b[0], (list, tuple))
    if matrix_rhs:
        right = _matrix(b)
        if len(right) != n:
            raise ValueError("Right-hand side row count mismatch")
        augmented = [matrix[i] + right[i] for i in range(n)]
        extra = len(right[0])
    else:
        vector = [float(x) for x in (b or [])]
        if len(vector) != n:
            raise ValueError("Right-hand side length mismatch")
        augmented = [matrix[i] + [vector[i]] for i in range(n)]
        extra = 1
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(augmented[r][col]))
        if abs(augmented[pivot][col]) < 1e-12:
            raise ValueError("Matrix is singular")
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        divisor = augmented[col][col]
        augmented[col] = [value / divisor for value in augmented[col]]
        for row in range(n):
            if row == col:
                continue
            factor = augmented[row][col]
            if factor:
                augmented[row] = [x - factor * y for x, y in zip(augmented[row], augmented[col])]
    if matrix_rhs:
        return [augmented[i][n:n + extra] for i in range(n)]
    return [augmented[i][n] for i in range(n)]


def determinant(matrix: Any) -> float:
    rows = _matrix(matrix)
    n = len(rows)
    if n == 0 or len(rows[0]) != n:
        raise ValueError("determinant requires a square matrix")
    work = [row[:] for row in rows]
    result = 1.0
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(work[r][col]))
        if abs(work[pivot][col]) < 1e-12:
            return 0.0
        if pivot != col:
            work[col], work[pivot] = work[pivot], work[col]
            result = -result
        result *= work[col][col]
        divisor = work[col][col]
        for row in range(col + 1, n):
            factor = work[row][col] / divisor
            if factor:
                work[row] = [x - factor * y for x, y in zip(work[row], work[col])]
    return result


def inverse(matrix: Any) -> list[list[float]]:
    rows = _matrix(matrix)
    return solve(rows, identity(len(rows)))


# ---------------------------------------------------------------------------
# Probability distributions
# ---------------------------------------------------------------------------

_SQRT2 = math.sqrt(2.0)
_SQRT2PI = math.sqrt(2.0 * math.pi)


def normal_pdf(x: Any, mu: float = 0.0, sigma: float = 1.0) -> float:
    sigma = float(sigma)
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    z = (float(x) - float(mu)) / sigma
    return math.exp(-0.5 * z * z) / (sigma * _SQRT2PI)


def normal_cdf(x: Any, mu: float = 0.0, sigma: float = 1.0) -> float:
    sigma = float(sigma)
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    z = (float(x) - float(mu)) / sigma
    return 0.5 * (1.0 + math.erf(z / _SQRT2))


def normal_ppf(p: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    """Inverse normal CDF (Acklam's rational approximation)."""
    p = float(p)
    if not 0.0 < p < 1.0:
        raise ValueError("p must be between 0 and 1")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    low, high = 0.02425, 1.0 - 0.02425
    if p < low:
        q = math.sqrt(-2.0 * math.log(p))
        z = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    elif p > high:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        z = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    else:
        q = p - 0.5
        r = q * q
        z = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
            (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)
    # One Halley refinement step.
    error = normal_cdf(z) - p
    return float(mu) + float(sigma) * (z - error / normal_pdf(z))


def normal_interval(confidence: float = 0.95, mu: float = 0.0, sigma: float = 1.0) -> dict[str, float]:
    confidence = float(confidence)
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    tail = (1.0 - confidence) / 2.0
    return {
        "low": normal_ppf(tail, mu, sigma),
        "high": normal_ppf(1.0 - tail, mu, sigma),
    }


def uniform_pdf(x: Any, low: float = 0.0, high: float = 1.0) -> float:
    low, high = float(low), float(high)
    if high <= low:
        raise ValueError("high must be greater than low")
    return 1.0 / (high - low) if low <= float(x) <= high else 0.0


def uniform_cdf(x: Any, low: float = 0.0, high: float = 1.0) -> float:
    low, high = float(low), float(high)
    if high <= low:
        raise ValueError("high must be greater than low")
    return max(0.0, min(1.0, (float(x) - low) / (high - low)))


def exponential_pdf(x: Any, rate: float = 1.0) -> float:
    rate = float(rate)
    if rate <= 0:
        raise ValueError("rate must be positive")
    return rate * math.exp(-rate * float(x)) if float(x) >= 0 else 0.0


def exponential_cdf(x: Any, rate: float = 1.0) -> float:
    rate = float(rate)
    if rate <= 0:
        raise ValueError("rate must be positive")
    return 1.0 - math.exp(-rate * float(x)) if float(x) >= 0 else 0.0


def binomial_pmf(k: int, n: int, p: float) -> float:
    k, n, p = int(k), int(n), float(p)
    if k < 0 or k > n:
        return 0.0
    return math.comb(n, k) * p ** k * (1.0 - p) ** (n - k)


def binomial_cdf(k: int, n: int, p: float) -> float:
    return sum(binomial_pmf(i, n, p) for i in range(0, int(k) + 1))


def poisson_pmf(k: int, lam: float) -> float:
    lam = float(lam)
    if lam < 0:
        raise ValueError("lambda must be non-negative")
    return math.exp(-lam) * lam ** int(k) / math.factorial(int(k))


def poisson_cdf(k: int, lam: float) -> float:
    return sum(poisson_pmf(i, lam) for i in range(0, int(k) + 1))


def _betacf(a: float, b: float, x: float) -> float:
    max_iterations, epsilon, tiny = 200, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, max_iterations + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < epsilon:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_beta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(log_beta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_pdf(t: Any, df: float) -> float:
    df = float(df)
    if df <= 0:
        raise ValueError("df must be positive")
    coefficient = math.exp(math.lgamma((df + 1.0) / 2.0) - math.lgamma(df / 2.0)) / math.sqrt(df * math.pi)
    return coefficient * (1.0 + float(t) ** 2 / df) ** (-(df + 1.0) / 2.0)


def t_cdf(t: Any, df: float) -> float:
    df = float(df)
    if df <= 0:
        raise ValueError("df must be positive")
    value = float(t)
    x = df / (df + value * value)
    probability = 0.5 * _betai(df / 2.0, 0.5, x)
    return 1.0 - probability if value > 0 else probability


def f_cdf(x: Any, df1: float, df2: float) -> float:
    df1, df2 = float(df1), float(df2)
    if df1 <= 0 or df2 <= 0:
        raise ValueError("degrees of freedom must be positive")
    value = float(x)
    if value <= 0:
        return 0.0
    return _betai(df1 / 2.0, df2 / 2.0, df1 * value / (df1 * value + df2))


def _gammainc_lower(s: float, x: float) -> float:
    """Regularized lower incomplete gamma P(s, x)."""
    if x <= 0:
        return 0.0
    if x < s + 1.0:
        term = 1.0 / s
        total = term
        n = 1
        while True:
            term *= x / (s + n)
            total += term
            n += 1
            if abs(term) < abs(total) * 1e-15 or n > 1000:
                break
        return total * math.exp(-x + s * math.log(x) - math.lgamma(s))
    # Continued fraction for the upper incomplete gamma, then complement.
    tiny = 1e-300
    b = x + 1.0 - s
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - s)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    upper = math.exp(-x + s * math.log(x) - math.lgamma(s)) * h
    return 1.0 - upper


def chi2_cdf(x: Any, df: float) -> float:
    df = float(df)
    if df <= 0:
        raise ValueError("df must be positive")
    return _gammainc_lower(df / 2.0, float(x) / 2.0)


def _bisect_inverse(fn, target: float, low: float, high: float, iterations: int = 200) -> float:
    for _ in range(iterations):
        mid = (low + high) / 2.0
        if fn(mid) < target:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def t_ppf(p: float, df: float) -> float:
    """Inverse Student's t CDF, computed by bisection on ``t_cdf``."""
    p, df = float(p), float(df)
    if df <= 0:
        raise ValueError("df must be positive")
    if not 0.0 < p < 1.0:
        raise ValueError("p must be between 0 and 1")
    if p == 0.5:
        return 0.0
    if p < 0.5:
        return -t_ppf(1.0 - p, df)
    high = 1.0
    while t_cdf(high, df) < p and high < 1e6:
        high *= 2.0
    return _bisect_inverse(lambda x: t_cdf(x, df), p, 0.0, high)


def chi2_ppf(p: float, df: float) -> float:
    """Inverse chi-square CDF, computed by bisection on ``chi2_cdf``."""
    p, df = float(p), float(df)
    if df <= 0:
        raise ValueError("df must be positive")
    if not 0.0 < p < 1.0:
        raise ValueError("p must be between 0 and 1")
    high = 1.0
    while chi2_cdf(high, df) < p and high < 1e12:
        high *= 2.0
    return _bisect_inverse(lambda x: chi2_cdf(x, df), p, 0.0, high)


def f_ppf(p: float, df1: float, df2: float) -> float:
    """Inverse F CDF, computed by bisection on ``f_cdf``."""
    p, df1, df2 = float(p), float(df1), float(df2)
    if df1 <= 0 or df2 <= 0:
        raise ValueError("degrees of freedom must be positive")
    if not 0.0 < p < 1.0:
        raise ValueError("p must be between 0 and 1")
    high = 1.0
    while f_cdf(high, df1, df2) < p and high < 1e12:
        high *= 2.0
    return _bisect_inverse(lambda x: f_cdf(x, df1, df2), p, 0.0, high)


# ---------------------------------------------------------------------------
# Random sampling
# ---------------------------------------------------------------------------

def _rng(seed: Any = None) -> random.Random:
    return random.Random(seed)


def random_uniform(n: int = 1, low: float = 0.0, high: float = 1.0, seed: Any = None) -> list[float]:
    rng = _rng(seed)
    return [rng.uniform(float(low), float(high)) for _ in range(int(n))]


def random_normal(n: int = 1, mu: float = 0.0, sigma: float = 1.0, seed: Any = None) -> list[float]:
    rng = _rng(seed)
    return [rng.gauss(float(mu), float(sigma)) for _ in range(int(n))]


def random_binomial(n: int = 1, trials: int = 1, p: float = 0.5, seed: Any = None) -> list[int]:
    rng = _rng(seed)
    return [sum(1 for _ in range(int(trials)) if rng.random() < float(p)) for _ in range(int(n))]


def random_poisson(n: int = 1, lam: float = 1.0, seed: Any = None) -> list[int]:
    rng = _rng(seed)
    lam = float(lam)
    out = []
    for _ in range(int(n)):
        if lam <= 0:
            out.append(0)
            continue
        limit = math.exp(-lam)
        count, product = 0, 1.0
        while True:
            product *= rng.random()
            if product <= limit:
                break
            count += 1
        out.append(count)
    return out


def bootstrap(values: Iterable[Any], statistic: str = "mean", samples: int = 1000,
              seed: Any = None) -> dict[str, Any]:
    vals = _nums(values)
    if not vals:
        raise ValueError("values are required")
    rng = _rng(seed)
    fn = {"mean": mean, "median": median, "std": std}.get(str(statistic), mean)
    estimates = []
    for _ in range(int(samples)):
        draw = [rng.choice(vals) for _ in vals]
        value = fn(draw)
        if value is not None:
            estimates.append(value)
    estimates.sort()
    return {
        "statistic": str(statistic),
        "samples": len(estimates),
        "estimate": fn(vals),
        "std_error": std(estimates),
        "ci_low": quantile(estimates, 0.025),
        "ci_high": quantile(estimates, 0.975),
    }


# ---------------------------------------------------------------------------
# Hypothesis tests
# ---------------------------------------------------------------------------

def t_test_1samp(values: Iterable[Any], popmean: float = 0.0) -> dict[str, Any]:
    vals = _nums(values)
    n = len(vals)
    if n < 2:
        raise ValueError("t-test requires at least two values")
    m = mean(vals)
    s = std(vals)
    se = (s or 0.0) / math.sqrt(n)
    t = (m - float(popmean)) / se if se else 0.0
    return {
        "t": t,
        "df": n - 1,
        "p_value": 2.0 * (1.0 - t_cdf(abs(t), n - 1)),
        "mean": m,
        "std": s,
        "n": n,
    }


def t_test_ind(a: Iterable[Any], b: Iterable[Any], equal_var: bool = True) -> dict[str, Any]:
    x, y = _nums(a), _nums(b)
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        raise ValueError("each sample requires at least two values")
    mx, my = mean(x), mean(y)
    vx, vy = variance(x), variance(y)
    if equal_var:
        df = nx + ny - 2
        pooled = ((nx - 1) * vx + (ny - 1) * vy) / df
        se = math.sqrt(pooled * (1.0 / nx + 1.0 / ny))
    else:
        df = (vx / nx + vy / ny) ** 2 / ((vx / nx) ** 2 / (nx - 1) + (vy / ny) ** 2 / (ny - 1))
        se = math.sqrt(vx / nx + vy / ny)
    t = (mx - my) / se if se else 0.0
    return {
        "t": t,
        "df": df,
        "p_value": 2.0 * (1.0 - t_cdf(abs(t), df)),
        "mean_a": mx,
        "mean_b": my,
        "n_a": nx,
        "n_b": ny,
    }


def welch_t_test(a: Iterable[Any], b: Iterable[Any]) -> dict[str, Any]:
    return t_test_ind(a, b, equal_var=False)


def t_test_paired(a: Iterable[Any], b: Iterable[Any]) -> dict[str, Any]:
    pairs = _pairs(a, b)
    return t_test_1samp([x - y for x, y in pairs], 0.0)


def chi_square_test(table: Sequence[Sequence[Any]]) -> dict[str, Any]:
    rows = [[float(value) for value in row] for row in table]
    if not rows or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("table must be rectangular")
    row_totals = [sum(row) for row in rows]
    col_totals = [sum(rows[i][j] for i in range(len(rows))) for j in range(len(rows[0]))]
    total = sum(row_totals)
    if total <= 0:
        raise ValueError("table must contain positive counts")
    chi = 0.0
    for i, row in enumerate(rows):
        for j, observed in enumerate(row):
            expected = row_totals[i] * col_totals[j] / total
            if expected:
                chi += (observed - expected) ** 2 / expected
    df = (len(rows) - 1) * (len(rows[0]) - 1)
    return {"chi2": chi, "df": df, "p_value": 1.0 - chi2_cdf(chi, df)}


def anova_oneway(*groups: Iterable[Any]) -> dict[str, Any]:
    samples = [_nums(group) for group in groups]
    samples = [sample for sample in samples if sample]
    if len(samples) < 2:
        raise ValueError("anova requires at least two groups")
    combined = [value for sample in samples for value in sample]
    grand = mean(combined)
    ss_between = sum(len(sample) * (mean(sample) - grand) ** 2 for sample in samples)
    ss_within = sum(sum((value - mean(sample)) ** 2 for value in sample) for sample in samples)
    df_between = len(samples) - 1
    df_within = len(combined) - len(samples)
    ms_between = ss_between / df_between
    ms_within = ss_within / df_within if df_within else 0.0
    f = ms_between / ms_within if ms_within else 0.0
    return {
        "f": f,
        "df_between": df_between,
        "df_within": df_within,
        "p_value": 1.0 - f_cdf(f, df_between, df_within),
    }


# ---------------------------------------------------------------------------
# Regression, interpolation and modelling
# ---------------------------------------------------------------------------

def linear_regression(x: Iterable[Any], y: Iterable[Any]) -> dict[str, Any]:
    pairs = _pairs(x, y)
    n = len(pairs)
    if n < 2:
        raise ValueError("linear regression requires at least two points")
    xs = [a for a, _ in pairs]
    ys = [b for _, b in pairs]
    mx, my = mean(xs), mean(ys)
    sxx = sum((a - mx) ** 2 for a in xs)
    sxy = sum((a - mx) * (b - my) for a, b in pairs)
    slope = sxy / sxx if sxx else 0.0
    intercept = my - slope * mx
    fitted = [intercept + slope * a for a in xs]
    residuals = [b - f for b, f in zip(ys, fitted)]
    ss_res = sum(r * r for r in residuals)
    ss_tot = sum((b - my) ** 2 for b in ys)
    return {
        "slope": slope,
        "intercept": intercept,
        "r_squared": 1.0 - ss_res / ss_tot if ss_tot else 1.0,
        "fitted": fitted,
        "residuals": residuals,
        "n": n,
    }


def multiple_regression(features: Any, target: Iterable[Any]) -> dict[str, Any]:
    rows = _matrix(features)
    values = [float(v) for v in (target or [])]
    if len(rows) != len(values):
        raise ValueError("features and target lengths must match")
    design = [[1.0] + row for row in rows]
    gram = matmul(transpose(design), design)
    rhs = [dot(row, values) for row in transpose(design)]
    coefficients = solve(gram, rhs)
    fitted = [dot(row, coefficients) for row in design]
    residuals = [b - f for b, f in zip(values, fitted)]
    ybar = mean(values)
    ss_res = sum(r * r for r in residuals)
    ss_tot = sum((b - ybar) ** 2 for b in values)
    return {
        "coefficients": coefficients,
        "intercept": coefficients[0],
        "slopes": coefficients[1:],
        "r_squared": 1.0 - ss_res / ss_tot if ss_tot else 1.0,
        "fitted": fitted,
        "residuals": residuals,
        "n": len(values),
    }


def polyfit(x: Iterable[Any], y: Iterable[Any], degree: int = 1) -> list[float]:
    pairs = _pairs(x, y)
    if len(pairs) < int(degree) + 1:
        raise ValueError("not enough points for the requested degree")
    xs = [a for a, _ in pairs]
    ys = [b for _, b in pairs]
    design = [[a ** k for k in range(int(degree) + 1)] for a in xs]
    gram = matmul(transpose(design), design)
    rhs = [dot(row, ys) for row in transpose(design)]
    return solve(gram, rhs)


def polyval(coefficients: Iterable[Any], x: Any) -> Any:
    coeffs = [float(c) for c in coefficients]
    if isinstance(x, (list, tuple)):
        return [polyval(coeffs, value) for value in x]
    return sum(c * float(x) ** i for i, c in enumerate(coeffs))


def r_squared(actual: Iterable[Any], predicted: Iterable[Any]) -> float | None:
    pairs = _pairs(actual, predicted)
    if len(pairs) < 2:
        return None
    ys = [b for _, b in pairs]
    ybar = mean(ys)
    ss_res = sum((b - f) ** 2 for b, f in pairs)
    ss_tot = sum((b - ybar) ** 2 for b in ys)
    return 1.0 - ss_res / ss_tot if ss_tot else 1.0


def interpolate(values: Iterable[Any], method: str = "linear") -> list[Any]:
    vals = list(values or [])
    result = list(vals)
    n = len(vals)
    if method == "linear":
        for i, value in enumerate(vals):
            if value is not None:
                continue
            left = next((j for j in range(i - 1, -1, -1) if vals[j] is not None), None)
            right = next((j for j in range(i + 1, n) if vals[j] is not None), None)
            if left is not None and right is not None:
                result[i] = vals[left] + (vals[right] - vals[left]) * (i - left) / (right - left)
            elif left is not None:
                result[i] = vals[left]
            elif right is not None:
                result[i] = vals[right]
        return result
    if method == "nearest":
        for i, value in enumerate(vals):
            if value is not None:
                continue
            distance_left = next((i - j for j in range(i - 1, -1, -1) if vals[j] is not None), None)
            distance_right = next((j - i for j in range(i + 1, n) if vals[j] is not None), None)
            if distance_left is None and distance_right is None:
                continue
            if distance_right is None or (distance_left is not None and distance_left <= distance_right):
                result[i] = vals[i - distance_left]
            else:
                result[i] = vals[i + distance_right]
        return result
    raise ValueError("Unknown interpolation method: " + str(method))


def linspace(start: float, stop: float, num: int = 50) -> list[float]:
    count = int(num)
    if count <= 0:
        return []
    if count == 1:
        return [float(start)]
    step = (float(stop) - float(start)) / (count - 1)
    return [float(start) + i * step for i in range(count)]


def arange(start: float, stop: float | None = None, step: float = 1.0) -> list[float]:
    if stop is None:
        start, stop = 0.0, start
    step = float(step)
    if step == 0:
        raise ValueError("step must be non-zero")
    values = []
    current = float(start)
    if step > 0:
        while current < float(stop) - 1e-12:
            values.append(current)
            current += step
    else:
        while current > float(stop) + 1e-12:
            values.append(current)
            current += step
    return values


def _points(data: Any) -> tuple[list[list[float]], list[str]]:
    if not data:
        return [], []
    first = data[0]
    if isinstance(first, dict):
        keys = [k for k in first.keys() if isinstance(first[k], (int, float)) and not isinstance(first[k], bool)]
        return [[float(row.get(k, 0.0) or 0.0) for k in keys] for row in data], keys
    return [[float(x) for x in row] for row in data], [str(i) for i in range(len(first))]


def _sqdist(a: Sequence[float], b: Sequence[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def kmeans(data: Any, k: int, max_iter: int = 100, seed: Any = None) -> dict[str, Any]:
    points, features = _points(data)
    n = len(points)
    k = int(k)
    if n == 0:
        raise ValueError("data is required")
    if k < 1 or k > n:
        raise ValueError("k must be between 1 and the number of points")
    rng = _rng(seed)
    centers = [points[rng.randrange(n)][:]]
    while len(centers) < k:
        distances = [min(_sqdist(point, center) for center in centers) for point in points]
        total = sum(distances)
        if total <= 0:
            centers.append(points[rng.randrange(n)][:])
            continue
        target = rng.random() * total
        cumulative = 0.0
        chosen = n - 1
        for index, distance in enumerate(distances):
            cumulative += distance
            if cumulative >= target:
                chosen = index
                break
        centers.append(points[chosen][:])
    labels = [0] * n
    for _ in range(int(max_iter)):
        changed = False
        for index, point in enumerate(points):
            best = min(range(k), key=lambda c: _sqdist(point, centers[c]))
            if labels[index] != best:
                labels[index] = best
                changed = True
        for cluster in range(k):
            members = [points[i] for i in range(n) if labels[i] == cluster]
            if members:
                centers[cluster] = [sum(column) / len(members) for column in zip(*members)]
        if not changed:
            break
    inertia = sum(_sqdist(points[i], centers[labels[i]]) for i in range(n))
    return {"labels": labels, "centers": centers, "inertia": inertia, "k": k, "features": features}


def pca(data: Any, components: int = 2) -> dict[str, Any]:
    points, features = _points(data)
    n = len(points)
    if n < 2 or not points:
        raise ValueError("pca requires at least two rows")
    dimension = len(points[0])
    means = [sum(column) / n for column in zip(*points)]
    centered = [[point[j] - means[j] for j in range(dimension)] for point in points]
    covariance = [
        [sum(centered[i][a] * centered[i][b] for i in range(n)) / (n - 1) for b in range(dimension)]
        for a in range(dimension)
    ]
    work = [row[:] for row in covariance]
    vectors: list[list[float]] = []
    eigenvalues: list[float] = []
    for _ in range(min(int(components), dimension)):
        vector = [1.0 / math.sqrt(dimension)] * dimension
        for _ in range(200):
            product = [sum(work[i][j] * vector[j] for j in range(dimension)) for i in range(dimension)]
            length = math.sqrt(sum(value * value for value in product))
            if length == 0:
                break
            vector = [value / length for value in product]
        eigenvalue = sum(
            vector[i] * sum(work[i][j] * vector[j] for j in range(dimension))
            for i in range(dimension)
        )
        vectors.append(vector)
        eigenvalues.append(eigenvalue)
        work = [
            [work[i][j] - eigenvalue * vector[i] * vector[j] for j in range(dimension)]
            for i in range(dimension)
        ]
    total_variance = sum(covariance[i][i] for i in range(dimension))
    ratios = [value / total_variance if total_variance else 0.0 for value in eigenvalues]
    projected = [
        [sum(point[j] * vector[j] for j in range(dimension)) for vector in vectors]
        for point in centered
    ]
    return {
        "components": vectors,
        "eigenvalues": eigenvalues,
        "explained_variance_ratio": ratios,
        "projected": projected,
        "means": means,
        "features": features,
    }


def confusion_matrix(actual: Iterable[Any], predicted: Iterable[Any]) -> dict[str, Any]:
    labels: list[Any] = []
    for value in list(actual) + list(predicted):
        if value not in labels:
            labels.append(value)
    index = {label: i for i, label in enumerate(labels)}
    matrix = [[0] * len(labels) for _ in labels]
    for a, p in zip(actual, predicted):
        matrix[index[a]][index[p]] += 1
    return {"labels": labels, "matrix": matrix}


# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------

def build_stats_namespace() -> dict[str, Any]:
    namespace = {
        # descriptive
        "mean": mean,
        "median": median,
        "mode": mode,
        "quantile": quantile,
        "percentile": percentile,
        "iqr": iqr,
        "variance": variance,
        "std": std,
        "skew": skew,
        "kurtosis": kurtosis,
        "covariance": covariance,
        "pearson": pearson,
        "correlation": pearson,
        "spearman": spearman,
        "kendall": kendall,
        "entropy": entropy,
        "gini": gini,
        "describe": describe,
        # scaling / transforms
        "zscore": zscore,
        "minmax_scale": minmax_scale,
        "robust_scale": robust_scale,
        "winsorize": winsorize,
        "cumsum": cumsum,
        "cumprod": cumprod,
        "cummax": cummax,
        "cummin": cummin,
        "diff": diff,
        "histogram": histogram,
        "outliers_z": outliers_z,
        "percentile_rank": percentile_rank,
        # linear algebra
        "dot": dot,
        "norm": norm,
        "distance": distance,
        "angle": angle,
        "add": add,
        "sub": sub,
        "mul": mul,
        "div": div,
        "scale": scale,
        "outer": outer,
        "transpose": transpose,
        "identity": identity,
        "matmul": matmul,
        "trace": trace,
        "solve": solve,
        "determinant": determinant,
        "inverse": inverse,
        # distributions
        "normal_pdf": normal_pdf,
        "normal_cdf": normal_cdf,
        "normal_ppf": normal_ppf,
        "normal_interval": normal_interval,
        "uniform_pdf": uniform_pdf,
        "uniform_cdf": uniform_cdf,
        "exponential_pdf": exponential_pdf,
        "exponential_cdf": exponential_cdf,
        "binomial_pmf": binomial_pmf,
        "binomial_cdf": binomial_cdf,
        "poisson_pmf": poisson_pmf,
        "poisson_cdf": poisson_cdf,
        "t_pdf": t_pdf,
        "t_cdf": t_cdf,
        "t_ppf": t_ppf,
        "f_cdf": f_cdf,
        "f_ppf": f_ppf,
        "chi2_cdf": chi2_cdf,
        "chi2_ppf": chi2_ppf,
        # random
        "random_uniform": random_uniform,
        "random_normal": random_normal,
        "random_binomial": random_binomial,
        "random_poisson": random_poisson,
        "bootstrap": bootstrap,
        # tests
        "t_test_1samp": t_test_1samp,
        "t_test_ind": t_test_ind,
        "welch_t_test": welch_t_test,
        "t_test_paired": t_test_paired,
        "chi_square_test": chi_square_test,
        "anova_oneway": anova_oneway,
        # modelling
        "linear_regression": linear_regression,
        "multiple_regression": multiple_regression,
        "polyfit": polyfit,
        "polyval": polyval,
        "r_squared": r_squared,
        "interpolate": interpolate,
        "linspace": linspace,
        "arange": arange,
        "kmeans": kmeans,
        "pca": pca,
        "confusion_matrix": confusion_matrix,
    }
    from .inference import build_inference_namespace
    from .modeling import build_modeling_namespace
    from .causal import build_causal_namespace
    from .evaluation import build_evaluation_namespace
    from .trees import build_tree_namespace
    from .boosting import build_boosting_namespace
    from .selection import build_selection_namespace
    from .interpret import build_interpret_namespace
    from .imbalance import build_imbalance_namespace
    from .pipeline import build_pipeline_namespace
    from .persistence import build_persistence_namespace
    from .dates import build_dates_namespace
    from .target_encoding import build_target_namespace
    from .notebook import build_notebook_namespace
    from .documents import build_document_namespace
    from .visualization import build_visualization_namespace
    from .validation import build_validation_namespace
    from .conformance_quality import build_conformance_namespace
    from .advanced_ml import build_ml_namespace
    from .sql_interop import build_sql_interop_namespace
    from .robustness import build_robustness_namespace
    from .devx import build_devx_namespace
    from .timeseries_advanced import build_timeseries_namespace
    from .clustering import build_clustering_namespace
    from .lsp import build_lsp_namespace
    from .formatter import build_formatter_namespace
    from .wasm_runtime import build_wasm_runtime_namespace
    from .react_sdk import build_react_sdk_namespace
    from .web_sdk import build_web_sdk_namespace
    from .arrow_backend import build_arrow_backend_namespace
    from .vector_rag import build_vector_rag_namespace

    namespace.update(build_inference_namespace())
    namespace.update(build_modeling_namespace())
    namespace.update(build_causal_namespace())
    namespace.update(build_evaluation_namespace())
    namespace.update(build_tree_namespace())
    namespace.update(build_boosting_namespace())
    namespace.update(build_selection_namespace())
    namespace.update(build_interpret_namespace())
    namespace.update(build_imbalance_namespace())
    namespace.update(build_pipeline_namespace())
    namespace.update(build_persistence_namespace())
    namespace.update(build_dates_namespace())
    namespace.update(build_target_namespace())
    namespace.update(build_notebook_namespace())
    namespace.update(build_document_namespace())
    namespace.update(build_visualization_namespace())
    namespace.update(build_validation_namespace())
    namespace.update(build_conformance_namespace())
    namespace.update(build_ml_namespace())
    namespace.update(build_sql_interop_namespace())
    namespace.update(build_robustness_namespace())
    namespace.update(build_devx_namespace())
    namespace.update(build_timeseries_namespace())
    namespace.update(build_clustering_namespace())
    namespace.update(build_lsp_namespace())
    namespace.update(build_formatter_namespace())
    namespace.update(build_wasm_runtime_namespace())
    namespace.update(build_react_sdk_namespace())
    namespace.update(build_web_sdk_namespace())
    namespace.update(build_arrow_backend_namespace())
    namespace.update(build_vector_rag_namespace())
    return namespace
