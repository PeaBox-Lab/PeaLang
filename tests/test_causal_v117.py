from pealang import causal as c
from pealang import execute


def approx(actual, expected, tol=1e-8):
    assert abs(actual - expected) <= tol


def test_propensity_scores_and_balance():
    features = [[1], [1], [2], [2], [3], [3], [4], [4]]
    treatment = [0, 1, 0, 1, 0, 1, 0, 1]
    result = c.propensity_scores(features, treatment, ["x"])
    assert result["n"] == 8
    assert result["treated_count"] == 4
    assert result["control_count"] == 4
    for score in result["scores"]:
        approx(score, 0.5, 1e-9)
    for weight in result["weights_ate"]:
        approx(weight, 2.0, 1e-9)
    assert result["overlap"]["fraction_in_range"] == 1.0

    balance = c.covariate_balance(features, treatment, ["x"])
    approx(balance["table"][0]["smd"], 0.0, 1e-9)
    approx(balance["max_abs_smd"], 0.0, 1e-9)


def test_ipw_matches_manual_estimator():
    features = [[value] for value in range(1, 9)]
    treatment = [0, 1, 0, 1, 0, 1, 0, 1]
    outcome = [1, 2, 3, 4, 5, 6, 7, 8]
    scores = c.propensity_scores(features, treatment)["scores"]

    treated_weight = [
        1.0 / scores[i] if treatment[i] else 0.0 for i in range(8)
    ]
    control_weight = [
        1.0 / (1.0 - scores[i]) if not treatment[i] else 0.0 for i in range(8)
    ]
    manual_ate = (
        sum(treated_weight[i] * outcome[i] for i in range(8)) / sum(treated_weight)
        - sum(control_weight[i] * outcome[i] for i in range(8)) / sum(control_weight)
    )
    att_weight = [
        1.0 if treatment[i] else scores[i] / (1.0 - scores[i]) for i in range(8)
    ]
    manual_att = (
        sum(att_weight[i] * outcome[i] for i in range(8) if treatment[i])
        / sum(att_weight[i] for i in range(8) if treatment[i])
        - sum(att_weight[i] * outcome[i] for i in range(8) if not treatment[i])
        / sum(att_weight[i] for i in range(8) if not treatment[i])
    )

    result = c.ipw_ate(features, treatment, outcome, 0.0, 0.95, 40, 1)
    approx(result["ate"], manual_ate, 1e-9)
    approx(result["att"], manual_att, 1e-9)
    assert result["samples"] >= 2
    assert result["se"] >= 0.0
    assert result["ci_low"] <= result["ate"] <= result["ci_high"]


def test_aipw_zero_conditional_effect():
    features = [[value] for value in range(1, 9)]
    treatment = [0, 1, 0, 1, 0, 1, 0, 1]
    outcome = [1, 2, 3, 4, 5, 6, 7, 8]
    result = c.aipw_ate(features, treatment, outcome, 0.0, 0.95, 40, 1)
    approx(result["ate"], 0.0, 1e-9)
    approx(result["att"], 0.0, 1e-9)
    assert result["samples"] >= 2


def test_propensity_matching():
    features = [[1], [1], [2], [2], [3], [3], [4], [4]]
    treatment = [0, 1, 0, 1, 0, 1, 0, 1]
    outcome = [0, 1, 0, 1, 0, 1, 0, 1]
    result = c.propensity_match(features, treatment, outcome)
    approx(result["att"], 1.0, 1e-9)
    assert result["n_matched"] == 4
    assert result["n_unmatched"] == 0
    for pair in result["pairs"]:
        approx(pair["difference"], 1.0, 1e-9)
        assert len(pair["controls"]) == 1


def test_difference_in_differences():
    outcome = [1, 2, 3, 4, 2, 3, 6, 7]
    treated = [0, 0, 0, 0, 1, 1, 1, 1]
    post = [0, 0, 1, 1, 0, 0, 1, 1]
    result = c.difference_in_differences(outcome, treated, post)
    approx(result["att"], 2.0, 1e-9)
    approx(result["se"], 1.0, 1e-9)
    approx(result["r_squared"], 0.9333333333, 1e-9)
    assert result["names"] == ["intercept", "treated", "post", "treated_x_post"]
    interaction = result["table"][3]
    assert interaction["term"] == "treated_x_post"
    approx(interaction["coefficient"], 2.0, 1e-9)

    clustered = c.difference_in_differences(
        outcome, treated, post, None, None, [0, 1, 2, 3, 0, 1, 2, 3]
    )
    assert clustered["clustered"] is True
    assert clustered["n_clusters"] == 4
    approx(clustered["att"], 2.0, 1e-9)


def test_instrumental_variables():
    instruments = [[value] for value in range(1, 21)]
    noise = [0.1, -0.2, 0.15, -0.05, 0.2, -0.15, 0.05, -0.1, 0.12, -0.08,
             0.1, -0.2, 0.15, -0.05, 0.2, -0.15, 0.05, -0.1, 0.12, -0.08]
    endogenous = [value + noise[value - 1] for value in range(1, 21)]
    outcome = [1 + 2 * endogenous[i] + 0.5 * noise[(i + 5) % 20] for i in range(20)]
    result = c.instrumental_variables(instruments, endogenous, outcome)
    approx(result["endogenous_coefficient"], 2.0021977360, 1e-6)
    assert result["first_stage"]["f_statistic"] > 1000
    assert result["first_stage"]["r_squared"] > 0.99
    assert result["sargan"] is None


def test_instrumental_variables_overidentified():
    import random

    rng = random.Random(3)
    instruments = []
    endogenous = []
    outcome = []
    for _ in range(60):
        z1 = rng.gauss(0, 1)
        z2 = rng.gauss(0, 1)
        v = rng.gauss(0, 1)
        u = rng.gauss(0, 1)
        x = 0.7 * z1 + 0.4 * z2 + v
        instruments.append([z1, z2])
        endogenous.append(x)
        outcome.append(1 + 2 * x + u)
    result = c.instrumental_variables(
        instruments, endogenous, outcome, None, None, ["z1", "z2"]
    )
    assert abs(result["endogenous_coefficient"] - 2.0) < 0.2
    assert result["first_stage"]["f_statistic"] > 10
    assert result["sargan_df"] == 1
    assert result["sargan_p_value"] > 0.05


def test_regression_discontinuity():
    running = [-2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2]
    outcome = [0.5 + (1.0 if value >= 0 else 0.0) + 0.2 * value for value in running]
    result = c.regression_discontinuity(running, outcome, 0.0, None, 1)
    approx(result["estimate"], 1.0, 1e-9)
    assert result["n_left"] == 4
    assert result["n_right"] == 4
    approx(result["left_intercept"], 0.5, 1e-9)
    approx(result["right_intercept"], 1.5, 1e-9)

    windowed = c.regression_discontinuity(running, outcome, 0.0, 1.5, 1)
    approx(windowed["estimate"], 1.0, 1e-9)
    assert windowed["n"] == 6


def test_causal_namespace_in_pea():
    src = r'''
let x = [[1], [2], [3], [4], [5], [6], [7], [8]]
let t = [0, 1, 0, 1, 0, 1, 0, 1]
let y = [1, 2, 3, 4, 5, 6, 7, 8]
let ps = stats.propensity_scores(x, t, ["x"])
print ps["treated_count"]
print round(ps["overlap"]["fraction_in_range"], 2)
let ipw = stats.ipw_ate(x, t, y, 0.0, 0.95, 30, 1)
print round(ipw["ate"], 4)
let aipw = stats.aipw_ate(x, t, y, 0.0, 0.95, 30, 1)
print round(aipw["ate"], 4)
let m = stats.propensity_match([[1], [1], [2], [2], [3], [3], [4], [4]], [0, 1, 0, 1, 0, 1, 0, 1], [0, 1, 0, 1, 0, 1, 0, 1])
print round(m["att"], 4)
let did = stats.difference_in_differences([1, 2, 3, 4, 2, 3, 6, 7], [0, 0, 0, 0, 1, 1, 1, 1], [0, 0, 1, 1, 0, 0, 1, 1])
print round(did["att"], 4)
let iv = stats.instrumental_variables([[1], [2], [3], [4], [5], [6], [7], [8], [9], [10]], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [3, 5, 7, 9, 11, 13, 15, 17, 19, 21])
print round(iv["endogenous_coefficient"], 4)
let rdd = stats.regression_discontinuity([-2, -1, 0, 1, 2], [0, 0, 1, 1, 1], 0.0, null, 0)
print round(rdd["estimate"], 4)
'''
    out = []
    execute(src, output=out.append, source_name="causal.pea")
    assert out == ["4", "1", "0.0619", "0", "1", "2", "2", "1"]


def test_causal_record_wrappers():
    src = r'''
let rows = [{"x": 1, "t": 0, "y": 1}, {"x": 2, "t": 1, "y": 2}, {"x": 3, "t": 0, "y": 3}, {"x": 4, "t": 1, "y": 4}, {"x": 5, "t": 0, "y": 5}, {"x": 6, "t": 1, "y": 6}, {"x": 7, "t": 0, "y": 7}, {"x": 8, "t": 1, "y": 8}]
let cr = analysis.causal_report(rows, "t", "y", ["x"])
print cr["method"]
print cr["features"][0]
print round(cr["ate"], 4)

let panel = [{"y": 1, "t": 0, "p": 0}, {"y": 2, "t": 0, "p": 0}, {"y": 3, "t": 0, "p": 1}, {"y": 4, "t": 0, "p": 1}, {"y": 2, "t": 1, "p": 0}, {"y": 3, "t": 1, "p": 0}, {"y": 6, "t": 1, "p": 1}, {"y": 7, "t": 1, "p": 1}]
let dr = analysis.did_report(panel, "y", "t", "p")
print round(dr["att"], 4)

let ivrows = [{"y": 3, "x": 1, "z": 1}, {"y": 5, "x": 2, "z": 2}, {"y": 7, "x": 3, "z": 3}, {"y": 9, "x": 4, "z": 4}, {"y": 11, "x": 5, "z": 5}, {"y": 13, "x": 6, "z": 6}, {"y": 15, "x": 7, "z": 7}, {"y": 17, "x": 8, "z": 8}, {"y": 19, "x": 9, "z": 9}, {"y": 21, "x": 10, "z": 10}]
let ir = analysis.iv_report(ivrows, "y", "x", "z")
print round(ir["endogenous_coefficient"], 4)

let rdrows = [{"x": -2, "y": 0.5}, {"x": -1, "y": 0.5}, {"x": 0, "y": 1.5}, {"x": 1, "y": 1.5}, {"x": 2, "y": 1.5}]
let rr = analysis.rdd_report(rdrows, "y", "x", 0.0, null, 0)
print round(rr["estimate"], 4)
'''
    out = []
    execute(src, output=out.append, source_name="causal_report.pea")
    assert out == ["ipw", "x", "0.0619", "2", "2", "1"]
