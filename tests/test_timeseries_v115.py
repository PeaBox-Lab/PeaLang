import math

from pealang import execute
from pealang import inference as inf


def approx(actual, expected, tol=1e-6):
    assert abs(actual - expected) <= tol


def test_acf_pacf_and_ljung_box():
    series = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    acf = inf.acf(series, 3)
    approx(acf[0], 1.0)
    approx(acf[1], 0.7)
    approx(acf[2], 0.4121212121)
    approx(acf[3], 0.1484848485)

    pacf = inf.pacf(series, 3)
    approx(pacf[0], 1.0)
    approx(pacf[1], 0.7)

    lb = inf.ljung_box(series, 3)
    approx(lb["statistic"], 9.4589531680, 1e-6)
    assert lb["df"] == 3
    approx(lb["p_value"], 0.0237720630, 1e-6)


def test_differencing_and_moving_average():
    series = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert inf.difference_series(series, 1) == [1.0] * 9
    assert inf.difference_series([1, 2, 4, 8], 2) == [1.0, 2.0]
    assert inf.moving_average(series, 3)[:3] == [1.0, 1.5, 2.0]


def test_exponential_smoothing():
    series = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    ses = inf.simple_exponential_smoothing(series, 0.3, 2)
    approx(ses["level"], 7.7608250830, 1e-6)
    assert len(ses["forecast"]) == 2

    holt = inf.holt_linear(series, 0.3, 0.1, 2)
    approx(holt["forecast"][0], 11.0, 1e-6)
    approx(holt["forecast"][1], 12.0, 1e-6)


def test_holt_winters_and_decomposition():
    seasonal = [10, 20, 30, 11, 21, 31, 12, 22, 32, 13, 23, 33]
    hw = inf.holt_winters(seasonal, 3, 0.3, 0.1, 0.3, 2)
    approx(hw["forecast"][0], 13.7542896307, 1e-6)
    approx(hw["forecast"][1], 23.8324984703, 1e-6)

    decomp = inf.seasonal_decompose(seasonal, 3)
    approx(decomp["pattern"][0], -8.5)
    approx(decomp["pattern"][1], 0.0)
    approx(decomp["pattern"][2], 8.5)
    assert len(decomp["trend"]) == len(seasonal)


def test_changepoint_and_stationarity():
    shift = [1, 1, 1, 1, 10, 10, 10, 10]
    cusum = inf.changepoint_cusum(shift, 0.5)
    assert cusum["changepoint"] == 3
    assert inf.changepoint_cusum([1, 2, 1, 2, 1, 2], 2.0)["changepoint"] is None

    adf = inf.adf_test([1, 2, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11], 1)
    approx(adf["statistic"], -0.2888950374, 1e-6)
    assert adf["stationary"] is False
    assert adf["critical"]["5%"] == -2.86


def test_analysis_wrappers_in_pea():
    src = r'''
let rows = [{"a": 1, "b": 0, "y": 2}, {"a": 0, "b": 1, "y": 3}, {"a": 1, "b": 1, "y": 5}, {"a": 2, "b": 2, "y": 9}, {"a": 3, "b": 1, "y": 10}, {"a": 2, "b": 3, "y": 11}]
let m = analysis.regression_report(rows, "y", ["a", "b"])
print round(m["r_squared"], 4)
print m["table"][1]["term"]
let ts = analysis.time_series_report([{"v": 10}, {"v": 20}, {"v": 30}, {"v": 11}, {"v": 21}, {"v": 31}, {"v": 12}, {"v": 22}, {"v": 32}], "v", 3, 3)
print ts["n"]
print round(ts["acf"][1], 3)
print ts["decomposition"]["pattern"][0] != null
'''
    out = []
    execute(src, output=out.append, source_name="ts.pea")
    assert out == ["0.9829", "a", "9", "-0.29", "true"]


def test_time_series_in_stats_namespace():
    src = r'''
print stats.acf([1, 2, 3, 4, 5], 2)[0]
print round(stats.pacf([1, 2, 3, 4, 5], 2)[1], 3)
print round(stats.holt_linear([1, 2, 3, 4, 5], 0.3, 0.1, 2)["forecast"][0], 3)
print stats.changepoint_cusum([1, 1, 1, 1, 10, 10, 10, 10], 0.5)["changepoint"]
'''
    out = []
    execute(src, output=out.append, source_name="ts.pea")
    assert out == ["1", "0.4", "6", "3"]
