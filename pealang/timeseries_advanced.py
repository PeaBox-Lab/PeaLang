"""Advanced time series and anomaly detection for PeaLang.

Provides dependency-free tools for time series analysis, anomaly detection,
and advanced forecasting.  Complements the existing stats time-series module.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Sequence


def _nums(values):
    out = []
    for v in values or []:
        if v is None or isinstance(v, bool):
            continue
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            continue
    return out


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

def zscore_anomalies(values: Sequence[Any], threshold: float = 3.0) -> list[dict[str, Any]]:
    """Detect anomalies using z-score method."""
    vals = _nums(values)
    if not vals:
        return []
    n = len(vals)
    mean = sum(vals) / n
    var = sum((x - mean) ** 2 for x in vals) / n
    std = math.sqrt(var) if var > 0 else 1.0
    result = []
    for i, v in enumerate(values):
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        z = (fv - mean) / std
        if abs(z) >= threshold:
            result.append({"index": i, "value": fv, "z_score": round(z, 4), "anomaly": True})
    return result


def iqr_anomalies(values: Sequence[Any], factor: float = 1.5) -> list[dict[str, Any]]:
    """Detect anomalies using IQR method."""
    vals = sorted(_nums(values))
    if not vals:
        return []
    n = len(vals)
    q1 = vals[n // 4]
    q3 = vals[3 * n // 4]
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    result = []
    for i, v in enumerate(values):
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if fv < lower or fv > upper:
            result.append({"index": i, "value": fv, "lower_bound": lower, "upper_bound": upper, "anomaly": True})
    return result


def moving_average_anomalies(values: Sequence[Any], window: int = 5, threshold: float = 2.0) -> list[dict[str, Any]]:
    """Detect anomalies using moving average deviation."""
    vals = _nums(values)
    if len(vals) < window:
        return []
    result = []
    for i in range(window, len(vals)):
        window_vals = vals[i - window:i]
        ma = sum(window_vals) / len(window_vals)
        std = (sum((x - ma) ** 2 for x in window_vals) / len(window_vals)) ** 0.5
        if std == 0:
            std = 1.0
        z = (vals[i] - ma) / std
        if abs(z) >= threshold:
            result.append({"index": i, "value": vals[i], "moving_avg": round(ma, 4), "z_score": round(z, 4), "anomaly": True})
    return result


# ---------------------------------------------------------------------------
# Time series decomposition
# ---------------------------------------------------------------------------

def seasonal_decompose_simple(values: Sequence[Any], period: int = 7) -> dict[str, Any]:
    """Simple additive seasonal decomposition."""
    vals = _nums(values)
    n = len(vals)
    if n < 2 * period:
        return {"error": "Not enough data for decomposition"}
    # Trend (moving average)
    trend = [None] * n
    half = period // 2
    for i in range(half, n - half):
        window = vals[i - half:i + half + 1]
        trend[i] = sum(window) / len(window)
    # Detrended
    detrended = [vals[i] - trend[i] if trend[i] is not None else 0 for i in range(n)]
    # Seasonal (average by position in period)
    seasonal = [0.0] * period
    counts = [0] * period
    for i in range(n):
        pos = i % period
        seasonal[pos] += detrended[i]
        counts[pos] += 1
    for i in range(period):
        if counts[i] > 0:
            seasonal[i] /= counts[i]
    # Center seasonal
    s_mean = sum(seasonal) / period
    seasonal = [s - s_mean for s in seasonal]
    # Full seasonal component
    full_seasonal = [seasonal[i % period] for i in range(n)]
    # Residual
    residual = [vals[i] - (trend[i] if trend[i] is not None else 0) - full_seasonal[i] for i in range(n)]
    return {
        "trend": trend,
        "seasonal": full_seasonal,
        "residual": residual,
        "period": period,
    }


# ---------------------------------------------------------------------------
# Advanced forecasting
# ---------------------------------------------------------------------------

def holt_winters_forecast(values: Sequence[Any], horizon: int = 5, alpha: float = 0.3,
                          beta: float = 0.1, gamma: float = 0.1, period: int = 7) -> list[float]:
    """Holt-Winters triple exponential smoothing forecast."""
    vals = _nums(values)
    n = len(vals)
    if n < period:
        return [vals[-1]] * horizon if vals else []
    # Initialize
    level = vals[0]
    trend = (vals[period] - vals[0]) / period if period < n else 0.0
    seasonal = [vals[i] - level for i in range(period)]
    # Fit
    for i in range(n):
        prev_level = level
        level = alpha * (vals[i] - seasonal[i % period]) + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        seasonal[i % period] = gamma * (vals[i] - level) + (1 - gamma) * seasonal[i % period]
    # Forecast
    forecast = []
    for h in range(1, horizon + 1):
        val = level + h * trend + seasonal[(n + h - 1) % period]
        forecast.append(val)
    return forecast


def exponential_smoothing_forecast(values: Sequence[Any], horizon: int = 5, alpha: float = 0.3) -> list[float]:
    """Simple exponential smoothing forecast."""
    vals = _nums(values)
    if not vals:
        return []
    level = vals[0]
    for v in vals[1:]:
        level = alpha * v + (1 - alpha) * level
    return [level] * horizon


# ---------------------------------------------------------------------------
# Change point detection
# ---------------------------------------------------------------------------

def detect_change_points(values: Sequence[Any], window: int = 10, threshold: float = 2.0) -> list[dict[str, Any]]:
    """Detect change points using CUSUM-like approach."""
    vals = _nums(values)
    if len(vals) < 2 * window:
        return []
    result = []
    for i in range(window, len(vals) - window):
        left = vals[i - window:i]
        right = vals[i:i + window]
        left_mean = sum(left) / len(left)
        right_mean = sum(right) / len(right)
        left_var = sum((x - left_mean) ** 2 for x in left) / len(left)
        right_var = sum((x - right_mean) ** 2 for x in right) / len(right)
        pooled_std = ((left_var + right_var) / 2) ** 0.5
        if pooled_std == 0:
            pooled_std = 1.0
        z = abs(right_mean - left_mean) / pooled_std
        if z >= threshold:
            result.append({"index": i, "left_mean": round(left_mean, 4), "right_mean": round(right_mean, 4), "z_score": round(z, 4)})
    return result


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def polynomial_features_2d(x: Sequence[Any], y: Sequence[Any]) -> list[dict[str, float]]:
    """Generate polynomial features (x, y, x^2, y^2, xy) from two columns."""
    xs = _nums(x)
    ys = _nums(y)
    n = min(len(xs), len(ys))
    result = []
    for i in range(n):
        result.append({
            "x": xs[i],
            "y": ys[i],
            "x2": xs[i] ** 2,
            "y2": ys[i] ** 2,
            "xy": xs[i] * ys[i],
        })
    return result


def interaction_features(data: list[dict[str, Any]], columns: list[str]) -> list[dict[str, Any]]:
    """Generate interaction features (products of pairs of columns)."""
    result = []
    for row in (data or []):
        new_row = dict(row)
        for i in range(len(columns)):
            for j in range(i + 1, len(columns)):
                c1, c2 = columns[i], columns[j]
                v1 = row.get(c1)
                v2 = row.get(c2)
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    new_row[f"{c1}_x_{c2}"] = v1 * v2
        result.append(new_row)
    return result


def build_timeseries_namespace() -> dict[str, Any]:
    return {
        "zscore_anomalies": zscore_anomalies,
        "iqr_anomalies": iqr_anomalies,
        "moving_average_anomalies": moving_average_anomalies,
        "seasonal_decompose_simple": seasonal_decompose_simple,
        "holt_winters_forecast": holt_winters_forecast,
        "exponential_smoothing_forecast": exponential_smoothing_forecast,
        "detect_change_points": detect_change_points,
        "polynomial_features_2d": polynomial_features_2d,
        "interaction_features": interaction_features,
    }
