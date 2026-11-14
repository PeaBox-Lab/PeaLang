# Advanced time series and anomaly detection (v138)

PeaLang provides dependency-free tools for time series analysis, anomaly detection,
and advanced forecasting.

## Anomaly detection

- `zscore_anomalies(values, threshold)` — z-score based anomaly detection
- `iqr_anomalies(values, factor)` — IQR based anomaly detection
- `moving_average_anomalies(values, window, threshold)` — moving average deviation

## Time series decomposition

- `seasonal_decompose_simple(values, period)` — additive seasonal decomposition

## Forecasting

- `holt_winters_forecast(values, horizon, alpha, beta, gamma, period)` — triple exponential smoothing
- `exponential_smoothing_forecast(values, horizon, alpha)` — simple exponential smoothing

## Change point detection

- `detect_change_points(values, window, threshold)` — CUSUM-like change point detection

## Feature engineering

- `polynomial_features_2d(x, y)` — polynomial features from two columns
- `interaction_features(data, columns)` — interaction features (products of pairs)