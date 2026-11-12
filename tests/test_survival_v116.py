from pealang import modeling as m


def approx(actual, expected, tol=1e-8):
    assert abs(actual - expected) <= tol


def test_kaplan_meier_curve():
    result = m.kaplan_meier([1, 2, 3, 4, 5], [1, 1, 0, 1, 0])
    assert result["median_survival"] == 4.0
    assert result["n"] == 5
    assert result["events"] == 3
    assert result["censored"] == 2
    timeline = result["timeline"]
    assert [row["time"] for row in timeline] == [1.0, 2.0, 3.0, 4.0, 5.0]
    assert [round(row["survival"], 4) for row in timeline] == [0.8, 0.6, 0.6, 0.3, 0.3]
    approx(timeline[0]["ci_low"], 0.4494, 1e-4)
    approx(timeline[0]["ci_high"], 1.0, 1e-9)
    approx(timeline[3]["ci_high"], 0.7679, 1e-4)


def test_log_rank_test():
    result = m.log_rank_test([1, 2, 3, 4, 5], [1, 1, 1, 1, 1],
                             [2, 3, 4, 5, 6], [1, 1, 1, 1, 1])
    approx(result["chi2"], 0.9908286872, 1e-8)
    approx(result["p_value"], 0.3195399204, 1e-8)
    approx(result["observed"], 5.0)
    approx(result["expected"], 3.7126984127, 1e-8)
    assert result["df"] == 1


def test_cox_proportional_hazards():
    result = m.cox_proportional_hazards(
        [[0.1], [0.5], [1.0], [1.5], [2.0], [0.2], [0.7], [1.2], [1.7], [2.2]],
        [1, 2, 2, 3, 4, 5, 5, 6, 7, 8],
        [1, 1, 1, 1, 0, 1, 1, 0, 1, 1],
        ["x"],
    )
    approx(result["coefficients"][0], -1.4565015388, 1e-8)
    approx(result["hazard_ratios"][0], 0.2330501672, 1e-8)
    approx(result["std_errors"][0], 0.7516220014, 1e-8)
    approx(result["p_values"][0], 0.0526462598, 1e-8)
    approx(result["log_likelihood"], -10.1613650689, 1e-8)
    approx(result["concordance"], 0.8333333333, 1e-8)
    assert result["n"] == 10
    assert result["events"] == 8
    assert result["converged"] is True


def test_concordance_index():
    approx(m.concordance_index([1, 2, 3], [1, 1, 1], [3, 2, 1]), 1.0)
    approx(m.concordance_index([1, 2, 3], [1, 1, 1], [1, 2, 3]), 0.0)
    assert m.concordance_index([1], [0], [1]) is None


def test_survival_analysis_in_pea():
    from pealang import execute

    src = r'''
let km = stats.kaplan_meier([1, 2, 3, 4, 5], [1, 1, 0, 1, 0])
print km["median_survival"]
print round(km["timeline"][0]["survival"], 2)
print km["censored"]
let report = analysis.survival_report([{"t": 1, "e": true}, {"t": 2, "e": true}, {"t": 3, "e": false}, {"t": 4, "e": true}], "t", "e")
print report["n"]
print report["kaplan_meier"]["median_survival"]
'''
    out = []
    execute(src, output=out.append, source_name="survival.pea")
    assert out == ["4", "0.8", "2", "4", "2"]
