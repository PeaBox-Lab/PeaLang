"""Regression coverage for v138 advanced time series and anomaly detection."""

from pealang.timeseries_advanced import (
    build_timeseries_namespace,
    zscore_anomalies,
    iqr_anomalies,
    moving_average_anomalies,
    seasonal_decompose_simple,
    holt_winters_forecast,
    exponential_smoothing_forecast,
    detect_change_points,
    polynomial_features_2d,
    interaction_features,
)


def test_zscore_anomalies():
    vals = [1, 2, 3, 4, 5, 100]
    result = zscore_anomalies(vals, threshold=2.0)
    assert len(result) >= 1
    assert result[0]["anomaly"] is True


def test_iqr_anomalies():
    vals = [1, 2, 3, 4, 5, 100]
    result = iqr_anomalies(vals)
    assert len(result) >= 1


def test_moving_average_anomalies():
    vals = [1, 2, 3, 4, 5, 2, 3, 4, 5, 50]
    result = moving_average_anomalies(vals, window=3, threshold=2.0)
    assert isinstance(result, list)


def test_seasonal_decompose():
    vals = list(range(1, 31))
    result = seasonal_decompose_simple(vals, period=7)
    assert "trend" in result
    assert "seasonal" in result
    assert "residual" in result
    assert len(result["trend"]) == 30


def test_holt_winters_forecast():
    vals = [10, 12, 13, 12, 10, 12, 13, 12, 10, 12, 13, 12]
    fc = holt_winters_forecast(vals, horizon=3, period=4)
    assert len(fc) == 3
    assert all(isinstance(v, float) for v in fc)


def test_exponential_smoothing_forecast():
    vals = [10, 12, 13, 12, 10]
    fc = exponential_smoothing_forecast(vals, horizon=3)
    assert len(fc) == 3


def test_detect_change_points():
    vals = [1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
    result = detect_change_points(vals, window=5, threshold=1.5)
    assert isinstance(result, list)


def test_polynomial_features_2d():
    x = [1, 2, 3]
    y = [4, 5, 6]
    result = polynomial_features_2d(x, y)
    assert len(result) == 3
    assert "x2" in result[0]
    assert "xy" in result[0]
    assert result[0]["xy"] == 4


def test_interaction_features():
    data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    result = interaction_features(data, ["a", "b"])
    assert "a_x_b" in result[0]
    assert result[0]["a_x_b"] == 2


def test_build_timeseries_namespace():
    ns = build_timeseries_namespace()
    assert "zscore_anomalies" in ns
    assert "seasonal_decompose_simple" in ns
    assert "holt_winters_forecast" in ns
    assert len(ns) == 9
