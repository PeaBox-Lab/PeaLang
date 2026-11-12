import math

from pealang import execute
from pealang import numerics as n


def approx(actual, expected, tol=1e-9):
    assert abs(actual - expected) <= tol


def test_descriptive_statistics():
    vals = [1, 2, 3, 4, 5]
    approx(n.mean(vals), 3)
    approx(n.median(vals), 3)
    approx(n.variance(vals), 2.5)
    approx(n.std(vals), math.sqrt(2.5))
    approx(n.quantile(vals, 0.5), 3)
    approx(n.percentile(vals, 50), 3)
    approx(n.iqr(vals), 2)
    assert n.mode([1, 2, 2, 3]) == 2
    assert n.entropy([1, 1, 2, 2]) == 1.0
    approx(n.gini([1, 1, 1, 1]), 0.0)
    approx(n.pearson([1, 2, 3], [2, 4, 6]), 1.0)
    approx(n.spearman([1, 2, 3], [3, 2, 1]), -1.0)
    assert n.kendall([1, 2, 3], [1, 2, 3]) == 1.0


def test_scaling_and_transforms():
    assert n.zscore([1, 2, 3]) == [-1.0, 0.0, 1.0]
    approx(n.minmax_scale([0, 5, 10])[1], 0.5)
    approx(n.robust_scale([1, 2, 3, 4, 5])[2], 0.0)
    assert n.cumsum([1, 2, 3]) == [1.0, 3.0, 6.0]
    assert n.cumprod([1, 2, 3]) == [1.0, 2.0, 6.0]
    assert n.cummax([3, 1, 4]) == [3.0, 3.0, 4.0]
    assert n.cummin([3, 1, 4]) == [3.0, 1.0, 1.0]
    assert n.diff([1, 4, 9], 1) == [None, 3.0, 5.0]
    buckets = n.histogram([1, 2, 3, 4], 2)
    assert buckets[0]["count"] == 2.0 and buckets[1]["count"] == 2.0
    assert n.outliers_z([1] * 20 + [1000]) == [1000.0]
    approx(n.percentile_rank([1, 2, 3, 4], 2), 37.5)


def test_linear_algebra():
    a = [[2, 1], [1, 3]]
    solved = n.solve(a, [1, 2])
    approx(solved[0], 0.2)
    approx(solved[1], 0.6)
    approx(n.determinant(a), 5.0)
    inverse = n.inverse(a)
    approx(inverse[0][0], 0.6)
    assert n.matmul([[1, 2], [3, 4]], [[5, 6], [7, 8]])[0][1] == 22.0
    approx(n.dot([1, 2, 3], [4, 5, 6]), 32.0)
    approx(n.norm([3, 4]), 5.0)
    approx(n.distance([0, 0], [3, 4]), 5.0)
    assert n.identity(2) == [[1.0, 0.0], [0.0, 1.0]]
    approx(n.trace([[1, 2], [3, 4]]), 5.0)
    assert n.transpose([[1, 2], [3, 4]]) == [[1.0, 3.0], [2.0, 4.0]]


def test_distributions():
    approx(n.normal_cdf(0), 0.5)
    approx(n.normal_pdf(0), 1.0 / math.sqrt(2 * math.pi), 1e-12)
    approx(n.normal_ppf(0.975), 1.959963984540054, 1e-6)
    interval = n.normal_interval(0.95)
    assert interval["low"] < 0 < interval["high"]
    approx(n.uniform_cdf(0.5), 0.5)
    approx(n.exponential_cdf(0), 0.0)
    approx(n.t_cdf(0, 10), 0.5)
    assert n.chi2_cdf(3.84, 1) > 0.9
    approx(n.binomial_pmf(2, 4, 0.5), 0.375)
    approx(n.poisson_pmf(0, 0), 1.0)


def test_hypothesis_tests():
    one = n.t_test_1samp([1, 2, 3, 4, 5], 3)
    assert one["df"] == 4 and one["p_value"] > 0.99
    ind = n.t_test_ind([1, 2, 3, 4, 5], [2, 3, 4, 5, 6])
    assert ind["n_a"] == 5 and ind["df"] == 8
    welch = n.welch_t_test([1, 2, 3, 4, 5], [2, 3, 4, 5, 6])
    assert welch["n_b"] == 5
    paired = n.t_test_paired([1, 2, 3], [2, 3, 4])
    assert paired["n"] == 3
    chi = n.chi_square_test([[10, 20], [20, 10]])
    assert chi["df"] == 1
    anova = n.anova_oneway([1, 2, 3], [4, 5, 6])
    assert anova["df_between"] == 1


def test_regression_and_models():
    fit = n.linear_regression([1, 2, 3, 4], [2, 4, 6, 8])
    approx(fit["slope"], 2.0)
    approx(fit["intercept"], 0.0)
    approx(fit["r_squared"], 1.0)
    multi = n.multiple_regression([[1, 0], [0, 1], [1, 1], [2, 2]], [1, 2, 3, 6])
    assert len(multi["coefficients"]) == 3
    coeffs = n.polyfit([1, 2, 3], [1, 4, 9], 2)
    approx(coeffs[2], 1.0)
    approx(n.polyval(coeffs, 4), 16.0)
    approx(n.r_squared([1, 2, 3], [1, 2, 3]), 1.0)
    km = n.kmeans([[1, 1], [1.2, 1.1], [5, 5], [5.2, 5.1]], 2, 50, 7)
    assert km["k"] == 2 and len(km["labels"]) == 4
    pc = n.pca([[1, 2], [2, 4], [3, 6], [4, 8]], 1)
    assert len(pc["components"]) == 1 and len(pc["projected"]) == 4
    cm = n.confusion_matrix(["a", "b", "a"], ["a", "a", "a"])
    assert cm["labels"] == ["a", "b"] and cm["matrix"][0][0] == 2


def test_interpolation_and_random():
    assert n.interpolate([1, None, 3]) == [1, 2.0, 3]
    assert n.interpolate([1, None, None, 4], "nearest") == [1, 1, 4, 4]
    assert n.linspace(0, 1, 3) == [0.0, 0.5, 1.0]
    assert n.arange(0, 3) == [0.0, 1.0, 2.0]
    assert n.random_uniform(5, seed=1) == n.random_uniform(5, seed=1)
    assert len(n.random_normal(4, seed=2)) == 4
    assert len(n.random_binomial(4, 10, 0.5, seed=3)) == 4
    assert len(n.random_poisson(4, 2.0, seed=4)) == 4
    boot = n.bootstrap([1, 2, 3, 4, 5], "mean", 100, 5)
    assert boot["samples"] == 100 and boot["ci_low"] <= boot["ci_high"]


def test_stats_namespace_in_pea():
    src = r'''
let d = [1, 2, 3, 4, 5]
print stats.mean(d)
print stats.median(d)
print round(stats.normal_cdf(0), 4)
print stats.linear_regression([1, 2], [2, 4])["slope"]
'''
    out = []
    execute(src, output=out.append, source_name="stats.pea")
    assert out == ["3", "3", "0.5", "2"]
