from pealang import execute
from pealang.numerics import build_stats_namespace
from pealang.stdlib import MODULES, build_standard_library


def run(src):
    out = []
    execute(src, output=out.append, source_name="stats.pea")
    return out


def test_stats_registered():
    assert "std.stats" in MODULES
    assert MODULES["std.stats"].stability == "Stable"


def test_stats_namespace_shape():
    ns = build_stats_namespace()
    for name in ["mean", "median", "pearson", "linear_regression", "kmeans", "pca", "t_test_ind", "normal_cdf"]:
        assert name in ns and callable(ns[name])


def test_stats_global_namespace():
    src = r'''
let d = [1, 2, 3, 4, 5]
print stats.mean(d)
print stats.median(d)
print stats.std(d) > 0
print stats.linear_regression([1, 2], [2, 4])["slope"]
print stats.solve([[2, 1], [1, 3]], [1, 2])[0]
'''
    assert run(src) == ["3", "3", "true", "2", "0.2"]


def test_std_stats_namespace():
    src = r'''
print std.stats.mean([1, 2, 3])
print std.stats.pearson([1, 2, 3], [2, 4, 6])
print std.stats.normal_cdf(0)
'''
    assert run(src) == ["2", "1", "0.5"]


def test_stats_distributions_and_tests():
    src = r'''
print round(stats.normal_ppf(0.975), 3)
print stats.chi2_cdf(3.84, 1) > 0.9
let t = stats.t_test_1samp([1, 2, 3, 4, 5], 3)
print t["df"]
let an = stats.anova_oneway([1, 2, 3], [4, 5, 6])
print an["df_between"]
'''
    assert run(src) == ["1.96", "true", "4", "1"]


def test_stats_models_in_pea():
    src = r'''
let km = stats.kmeans([[1, 1], [1.2, 1.1], [5, 5], [5.2, 5.1]], 2, 50, 7)
print km["k"]
print len(km["labels"])
let pc = stats.pca([[1, 2], [2, 4], [3, 6], [4, 8]], 1)
print len(pc["projected"])
let fit = stats.polyfit([1, 2, 3], [1, 4, 9], 2)
print round(fit[2], 3)
'''
    assert run(src) == ["2", "4", "4", "1"]


def test_std_stats_library_values():
    std = build_standard_library()["std"]["stats"]
    assert std["mean"]([1, 2, 3]) == 2
    assert std["pearson"]([1, 2, 3], [2, 4, 6]) == 1.0
