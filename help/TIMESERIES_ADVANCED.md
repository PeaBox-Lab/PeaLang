# Advanced time series and anomaly detection (v138)

PeaLang provides dependency-free tools for time series analysis, anomaly detection,
and advanced forecasting.

## Key functions

- `analysis.zscore_anomalies(values, threshold)` — z-score anomalies
- `analysis.iqr_anomalies(values, factor)` — IQR anomalies
- `analysis.moving_average_anomalies(values, window, threshold)` — MA anomalies
- `analysis.seasonal_decompose_simple(values, period)` — seasonal decomposition
- `analysis.holt_winters_forecast(values, horizon, alpha, beta, gamma, period)` — Holt-Winters
- `analysis.exponential_smoothing_forecast(values, horizon, alpha)` — exponential smoothing
- `analysis.detect_change_points(values, window, threshold)` — change points
- `analysis.polynomial_features_2d(x, y)` — polynomial features
- `analysis.interaction_features(data, columns)` — interaction features