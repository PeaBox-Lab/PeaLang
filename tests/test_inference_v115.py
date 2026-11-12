import math

from pealang import execute
from pealang import inference as inf


def approx(actual, expected, tol=1e-6):
    assert abs(actual - expected) <= tol


def test_confidence_intervals():
    mean_ci = inf.confidence_interval_mean([1, 2, 3, 4, 5])
    approx(mean_ci["estimate"], 3.0)
    approx(mean_ci["low"], 1.0367568385, 1e-6)
    approx(mean_ci["high"], 4.9632431615, 1e-6)
    assert mean_ci["df"] == 4

    prop = inf.confidence_interval_proportion(30, 100)
    approx(prop["estimate"], 0.3)
    approx(prop["low"], 0.2189488530, 1e-6)
    approx(prop["high"], 0.3958485463, 1e-6)

    diff = inf.confidence_interval_diff_means([1, 2, 3, 4, 5], [2, 3, 4, 5, 6])
    approx(diff["estimate"], -1.0)
    approx(diff["df"], 8.0)

    boot = inf.bootstrap_ci([1, 2, 3, 4, 5], "mean", 200, 0.95, 7)
    assert boot["low"] <= boot["estimate"] <= boot["high"]


def test_effect_sizes_and_power():
    approx(inf.cohens_d([1, 2, 3, 4, 5], [2, 3, 4, 5, 6]), -0.6324555320)
    approx(inf.hedges_g([1, 2, 3, 4, 5], [2, 3, 4, 5, 6]), -0.5712501580, 1e-6)
    approx(inf.eta_squared([1, 2, 3], [4, 5, 6]), 0.7714285714, 1e-6)
    approx(inf.power_t_test(0.5, 64), 0.8074304194, 1e-6)
    assert inf.sample_size_t_test(0.5, 0.8) == 63


def test_multiple_comparisons():
    bh = inf.adjust_p_values([0.01, 0.04, 0.03], "bh")
    assert [round(r["adjusted"], 4) for r in bh["results"]] == [0.03, 0.04, 0.04]
    assert all(r["rejected"] for r in bh["results"])

    bonf = inf.adjust_p_values([0.01, 0.04, 0.03], "bonferroni")
    assert [round(r["adjusted"], 4) for r in bonf["results"]] == [0.03, 0.12, 0.09]

    holm = inf.adjust_p_values([0.01, 0.04, 0.03], "holm")
    assert [round(r["adjusted"], 4) for r in holm["results"]] == [0.03, 0.06, 0.06]


def test_parametric_tests():
    z = inf.z_test_1samp([1, 2, 3, 4, 5], 3, 1)
    approx(z["z"], 0.0)
    approx(z["p_value"], 1.0)

    prop = inf.proportion_test(30, 100, 0.5)
    approx(prop["z"], -4.0)
    assert prop["p_value"] < 1e-4

    zprop = inf.z_test_proportions(30, 100, 40, 100)
    approx(zprop["z"], -1.4824986333, 1e-6)
    approx(zprop["p_value"], 0.1382076670, 1e-6)

    fisher = inf.fisher_exact(10, 20, 20, 10)
    approx(fisher["odds_ratio"], 0.25)
    approx(fisher["p_value"], 0.0193831883, 1e-6)

    gof = inf.chi_square_goodness_of_fit([10, 20, 30])
    approx(gof["chi2"], 10.0)
    assert gof["df"] == 2


def test_nonparametric_tests():
    mw = inf.mann_whitney_u([1, 2, 3, 4, 5], [2, 3, 4, 5, 6])
    approx(mw["u"], 8.0)
    approx(mw["p_value"], 0.3976147520, 1e-6)

    wil = inf.wilcoxon_signed_rank([1, 2, 3, 4, 5], [2, 3, 4, 5, 6])
    approx(wil["statistic"], 0.0)
    approx(wil["p_value"], 0.0253473187, 1e-6)

    kw = inf.kruskal_wallis([1, 2, 3], [4, 5, 6], [7, 8, 9])
    approx(kw["h"], 7.2)
    assert kw["df"] == 2

    fried = inf.friedman_test([1, 2, 3], [2, 4, 5], [3, 5, 7])
    approx(fried["chi2"], 6.0)
    assert fried["df"] == 2

    sign = inf.sign_test([1, 2, 3, 4], [0, 1, 2, 1])
    assert sign["positive"] == 4 and sign["negative"] == 0
    approx(sign["p_value"], 0.125)


def test_normality_and_permutation():
    jb = inf.jarque_bera([1, 2, 3, 4, 5, 6, 7, 8])
    approx(jb["statistic"], 0.5109599395, 1e-6)
    approx(jb["p_value"], 0.7745446507, 1e-6)
    assert inf.normality_test([1, 2, 3, 4, 5, 6, 7, 8])["df"] == 2

    perm = inf.permutation_test([1, 2, 3, 4, 5], [2, 3, 4, 5, 6], "mean", 200, 7)
    approx(perm["statistic"], -1.0)
    approx(perm["p_value"], 0.4427860697, 1e-6)


def test_ols_and_diagnostics():
    features = [[1, 0], [0, 1], [1, 1], [2, 2], [3, 1], [2, 3]]
    target = [2, 3, 5, 9, 10, 11]
    model = inf.ols(features, target, names=["a", "b"])
    approx(model["r_squared"], 0.9828648325, 1e-6)
    assert model["names"] == ["intercept", "a", "b"]
    assert [round(p, 4) for p in model["p_values"]] == [0.5089, 0.0042, 0.0064]
    assert model["df_resid"] == 3
    assert model["f_statistic"] is not None

    vif = inf.variance_inflation_factors(features, ["a", "b"])
    approx(vif[0]["vif"], 1.1578947368, 1e-6)

    prediction = inf.predict_ols(model, [[1, 1], [2, 2]])
    approx(prediction["predicted"][0], 4.8092105263, 1e-6)
    assert prediction["low"][0] < prediction["predicted"][0] < prediction["high"][0]

    diagnostics = inf.residual_diagnostics(model["residuals"])
    approx(diagnostics["mean"], 0.0, 1e-9)
    assert diagnostics["normality_p"] is not None


def test_inference_in_pea_namespace():
    src = r'''
print round(stats.confidence_interval_mean([1, 2, 3, 4, 5])["low"], 4)
print round(stats.cohens_d([1, 2, 3, 4, 5], [2, 3, 4, 5, 6]), 4)
print stats.adjust_p_values([0.01, 0.04, 0.03], "bh")["results"][0]["rejected"]
print stats.mann_whitney_u([1, 2, 3, 4, 5], [2, 3, 4, 5, 6])["p_value"] > 0
let m = stats.ols([[1, 0], [0, 1], [1, 1], [2, 2], [3, 1], [2, 3]], [2, 3, 5, 9, 10, 11], ["a", "b"])
print m["n"]
print m["table"][1]["term"]
print round(stats.t_ppf(0.975, 10), 3)
'''
    out = []
    execute(src, output=out.append, source_name="inference.pea")
    assert out == ["1.0368", "-0.6325", "true", "true", "6", "a", "2.228"]
