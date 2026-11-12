from pealang import execute
from pealang import modeling as m
from pealang import inference as inf


def approx(actual, expected, tol=1e-6):
    assert abs(actual - expected) <= tol


def test_logistic_glm():
    x = [[v] for v in range(1, 13)]
    y = [0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1]
    model = m.logistic_regression(x, y, ["x"])
    approx(model["coefficients"][0], -1.1472742681, 1e-8)
    approx(model["coefficients"][1], 0.2365506117, 1e-8)
    approx(model["std_errors"][1], 0.1948265309, 1e-8)
    approx(model["p_values"][1], 0.2246865712, 1e-8)
    approx(model["deviance"], 14.6081681193, 1e-8)
    approx(model["aic"], 18.6081681193, 1e-8)
    approx(model["pseudo_r_squared"], 0.1038284652, 1e-8)
    assert model["converged"] is True
    prediction = m.predict_glm(model, [[3], [9]])
    approx(prediction["predicted"][0], 0.3923076415, 1e-8)
    approx(prediction["predicted"][1], 0.7274416832, 1e-8)


def test_poisson_glm():
    x = [[v] for v in range(1, 13)]
    counts = [1, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    model = m.poisson_regression(x, counts, ["x"])
    approx(model["coefficients"][0], 0.0880388112, 1e-8)
    approx(model["coefficients"][1], 0.1953497750, 1e-8)
    approx(model["std_errors"][1], 0.0432400677, 1e-8)
    approx(model["p_values"][1], 6.2486846604e-06, 1e-12)
    approx(model["aic"], 43.5647332090, 1e-8)
    assert model["pseudo_r_squared"] > 0.95


def test_gaussian_glm_matches_ols():
    features = [[1], [2], [3], [4], [5], [6]]
    target = [2.1, 3.9, 6.2, 7.8, 10.1, 12.2]
    model = m.glm(features, target, "gaussian", ["x"])
    reference = inf.ols(features, target, ["x"])
    for actual, expected in zip(model["coefficients"], reference["coefficients"]):
        approx(actual, expected, 1e-9)
    approx(model["pseudo_r_squared"], reference["r_squared"], 1e-9)


def test_regularized_regression():
    features = [[1, 0], [0, 1], [1, 1], [2, 2], [3, 1], [2, 3]]
    target = [2, 3, 5, 9, 10, 11]
    ridge = m.ridge_regression(features, target, 0.5, ["a", "b"])
    approx(ridge["coefficients"][0], 2.1881720430, 1e-8)
    approx(ridge["coefficients"][1], 1.9354838710, 1e-8)
    approx(ridge["intercept"], 0.8037634409, 1e-8)
    approx(ridge["r_squared"], 0.9789354918, 1e-8)

    lasso = m.lasso_regression(features, target, 0.5, ["a", "b"])
    approx(lasso["coefficients"][0], 2.2763157897, 1e-8)
    approx(lasso["coefficients"][1], 1.9901315789, 1e-8)

    enet = m.elastic_net(features, target, 0.5, 0.5, ["a", "b"])
    approx(enet["coefficients"][0], 2.2305411422, 1e-8)
    approx(enet["coefficients"][1], 1.9621942177, 1e-8)

    sparse = m.lasso_regression(features, target, 20.0, ["a", "b"])
    assert abs(sparse["coefficients"][1]) < 1e-9


def test_arima_linear_series():
    fit = m.arima([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 1, 1, 0, 2)
    assert fit["order"] == (1, 1, 0)
    approx(fit["ar"][0], 0.0, 1e-9)
    approx(fit["intercept"], 1.0, 1e-9)
    approx(fit["forecast"][0], 11.0, 1e-9)
    approx(fit["forecast"][1], 12.0, 1e-9)


def test_arima_matches_conditional_ols():
    noise = [0.1, -0.2, 0.3, -0.1, 0.2, -0.3, 0.15, -0.05, 0.25, -0.15] * 6
    series = [0.0]
    for value in noise:
        series.append(0.6 * series[-1] + value)
    fit = m.arima(series, 1, 0, 0, 3)

    xs, ys = series[:-1], series[1:]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    intercept = my - slope * mx
    approx(fit["ar"][0], slope, 1e-7)
    approx(fit["intercept"], intercept, 1e-7)
    approx(fit["forecast"][0], intercept + slope * series[-1], 1e-7)
    approx(fit["forecast"][1], intercept + slope * (intercept + slope * series[-1]), 1e-7)


def test_auto_arima_selects_by_aic():
    seasonal = [10, 20, 30, 11, 21, 31, 12, 22, 32, 13, 23, 33, 14, 24, 34, 15, 25, 35]
    model = m.auto_arima(seasonal, 2, 2, 1, 2)
    assert model["order"] == (2, 1, 0)
    approx(model["forecast"][0], 16.0, 1e-6)
    approx(model["forecast"][1], 26.0, 1e-6)
    assert model["candidates"][0]["order"] == (2, 1, 0)
    assert model["selection"] == "aic"


def test_modeling_in_pea_namespace():
    src = r'''
print round(stats.logistic_regression([[1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12]], [0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1], ["x"])["coefficients"][1], 4)
print round(stats.poisson_regression([[1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12]], [1, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10], ["x"])["coefficients"][1], 4)
print round(stats.ridge_regression([[1, 0], [0, 1], [1, 1], [2, 2], [3, 1], [2, 3]], [2, 3, 5, 9, 10, 11], 0.5, ["a", "b"])["coefficients"][0], 4)
print stats.lasso_regression([[1, 0], [0, 1], [1, 1], [2, 2], [3, 1], [2, 3]], [2, 3, 5, 9, 10, 11], 20.0, ["a", "b"])["coefficients"][1]
print stats.kaplan_meier([1, 2, 3, 4, 5], [1, 1, 0, 1, 0])["median_survival"]
print round(stats.log_rank_test([1, 2, 3, 4, 5], [1, 1, 1, 1, 1], [2, 3, 4, 5, 6], [1, 1, 1, 1, 1])["p_value"], 4)
let cox = stats.cox_proportional_hazards([[0.1], [0.5], [1.0], [1.5], [2.0], [0.2], [0.7], [1.2], [1.7], [2.2]], [1, 2, 2, 3, 4, 5, 5, 6, 7, 8], [1, 1, 1, 1, 0, 1, 1, 0, 1, 1], ["x"])
print round(cox["concordance"], 4)
let fit = stats.arima([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 1, 1, 0, 2)
print round(fit["forecast"][0], 3)
let auto = stats.auto_arima([10, 20, 30, 11, 21, 31, 12, 22, 32, 13, 23, 33, 14, 24, 34, 15, 25, 35], 2, 2, 1, 2)
print auto["order"][0]
print round(auto["forecast"][0], 3)
'''
    out = []
    execute(src, output=out.append, source_name="modeling.pea")
    assert out == ["0.2366", "0.1953", "2.1882", "0", "4", "0.3195", "0.8333", "11", "2", "16"]
