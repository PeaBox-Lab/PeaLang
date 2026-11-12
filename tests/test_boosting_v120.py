import math

from pealang import boosting as b
from pealang import execute
from pealang import evaluation as e


def approx(actual, expected, tol=1e-9):
    assert abs(actual - expected) <= tol, (actual, expected)


X = [[index] for index in range(20)]
Y = [2 * index + 1 for index in range(20)]
LABELS = [0 if index < 10 else 1 for index in range(20)]


def test_regression_boosting():
    model = b.gradient_boosting(X, Y, "regression", 30, 0.2, 3, seed=1)
    assert model["estimator"] == "gradient_boosting"
    assert model["task"] == "regression"
    assert model["n_estimators"] == 30
    assert len(model["stages"]) == 30
    assert all(len(stage) == 1 for stage in model["stages"])
    assert model["base"] == 20.0
    assert model["feature_importances"] == [1.0]

    predicted = b.predict_boosting(model, X)["predicted"]
    assert e.r2_score(Y, predicted) > 0.999
    assert predicted == sorted(predicted)
    approx(predicted[0], 1.0, 0.1)
    approx(predicted[-1], 39.0, 0.1)


def test_binary_boosting():
    model = b.gradient_boosting(X, LABELS, "classification", 30, 0.3, 3, seed=1)
    assert model["task"] == "classification"
    assert model["classes"] == [0, 1]
    assert model["base"] == 0.0

    result = b.predict_boosting(model, X)
    assert result["predicted"] == LABELS
    assert result["classes"] == [0, 1]
    for probabilities in result["probabilities"]:
        approx(sum(probabilities), 1.0)
    assert result["probabilities"][0][1] < 1e-3
    assert result["probabilities"][-1][1] > 1.0 - 1e-3


def test_multiclass_boosting():
    labels = [0 if index < 7 else (1 if index < 14 else 2) for index in range(20)]
    model = b.gradient_boosting(X, labels, "classification", 30, 0.3, 3, seed=1)
    assert model["classes"] == [0, 1, 2]
    assert len(model["base"]) == 3
    assert len(model["stages"]) == 30
    assert all(len(stage) == 3 for stage in model["stages"])

    result = b.predict_boosting(model, X)
    assert result["predicted"] == labels
    assert result["classes"] == [0, 1, 2]
    for probabilities in result["probabilities"]:
        approx(sum(probabilities), 1.0)
        assert len(probabilities) == 3


def test_boosting_determinism():
    first = b.gradient_boosting(X, Y, "regression", 10, 0.2, 2, 2, 1, 0.5, None, 3)
    second = b.gradient_boosting(X, Y, "regression", 10, 0.2, 2, 2, 1, 0.5, None, 3)
    other = b.gradient_boosting(X, Y, "regression", 10, 0.2, 2, 2, 1, 0.5, None, 4)
    assert b.predict_boosting(first, X)["predicted"] == b.predict_boosting(second, X)["predicted"]
    assert b.predict_boosting(first, X)["predicted"] != b.predict_boosting(other, X)["predicted"]
    assert first["subsample"] == 0.5


def test_boosting_feature_importance():
    rows = []
    target = []
    for index in range(60):
        signal = (index % 10) / 10.0
        noise = ((index * 7) % 13) / 13.0
        rows.append([signal, noise])
        target.append(1 if signal > 0.5 else 0)
    model = b.gradient_boosting(rows, target, "classification", 20, 0.3, 3, seed=2)
    assert model["feature_importances"] == [1.0, 0.0]
    table = b.boosting_feature_importance(model, ["signal", "noise"])
    assert table[0] == {"feature": "signal", "importance": 1.0}
    assert table[1] == {"feature": "noise", "importance": 0.0}
    assert [entry["feature"] for entry in b.boosting_feature_importance(model)] == ["x1", "x2"]


def test_boosting_validation():
    cases = [
        (lambda: b.gradient_boosting(X, Y, "nope"), "task"),
        (lambda: b.gradient_boosting(X, Y, "regression", 0), "n_estimators"),
        (lambda: b.gradient_boosting(X, Y, "regression", 10, 0.0), "learning_rate"),
        (lambda: b.gradient_boosting(X, Y, "regression", 10, 0.1, 0), "max_depth"),
        (lambda: b.gradient_boosting(X, Y, "regression", 10, 0.1, 2, 1), "min_samples_split"),
        (lambda: b.gradient_boosting(X, Y, "regression", 10, 0.1, 2, 2, 0), "min_samples_leaf"),
        (lambda: b.gradient_boosting(X, Y, "regression", 10, 0.1, 2, 2, 1, 0.0), "subsample"),
        (lambda: b.gradient_boosting(X, Y, "regression", 10, 0.1, 2, 2, 1, 1.5), "subsample"),
        (lambda: b.gradient_boosting(X, Y[:-1], "regression"), "lengths"),
        (lambda: b.gradient_boosting(X, [1] * 20, "classification"), "two classes"),
        (lambda: b.gradient_boosting([], [], "regression"), "features"),
        (lambda: b.gradient_boosting(X, Y, "regression", 10, 0.1, 2, 2, 1, 1.0, 0), "max_features"),
        (lambda: b.boosting_feature_importance(b.gradient_boosting(X, Y), ["a", "b"]), "names"),
    ]
    for call, fragment in cases:
        try:
            call()
        except ValueError as error:
            assert fragment in str(error), (fragment, str(error))
        else:
            raise AssertionError("expected ValueError for " + fragment)


def test_auto_task_inference():
    src = r'''
let mrows = [{"a": 0, "b": 0, "label": 0}, {"a": 1, "b": 0, "label": 0}, {"a": 2, "b": 0, "label": 1}, {"a": 3, "b": 0, "label": 1}, {"a": 4, "b": 0, "label": 2}, {"a": 5, "b": 0, "label": 2}]
let report = analysis.tree_report(mrows, "label", ["a", "b"], "auto", 2)
print report["task"]
print report["classes"]

let regression_rows = [{"x": 0, "y": 0.5}, {"x": 1, "y": 1.5}, {"x": 2, "y": 4.5}, {"x": 3, "y": 9.5}]
let regression = analysis.tree_report(regression_rows, "y", ["x"], "auto", 2)
print regression["task"]

let text_rows = [{"x": 0, "y": "low"}, {"x": 1, "y": "high"}, {"x": 2, "y": "high"}, {"x": 3, "y": "low"}]
let text = analysis.tree_report(text_rows, "y", ["x"], "auto", 2)
print text["task"]
print text["classes"]
'''
    out = []
    execute(src, output=out.append, source_name="auto.pea")
    assert out == [
        "classification",
        "[0, 1, 2]",
        "regression",
        "classification",
        '["high", "low"]',
    ]


def test_namespace_and_record_wrappers():
    src = r'''
let model = stats.gradient_boosting([[0], [1], [2], [3], [4], [5]], [0, 0, 0, 1, 1, 1], "classification", 10, 0.3, 2, 2, 1, 1.0, "all", 1)
print model["task"]
print model["classes"]
print stats.predict_boosting(model, [[0], [5]])["predicted"]
print round(model["feature_importances"][0], 3)
print len(model["stages"])
print stats.boosting_feature_importance(model, ["x"])[0]["feature"]
print round(std.stats.predict_boosting(model, [[0]])["probabilities"][0][1], 3)

let rows = [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 0}, {"x": 3, "y": 1}, {"x": 4, "y": 1}, {"x": 5, "y": 1}]
let report = analysis.boosting_report(rows, "y", ["x"], "auto", 10, 0.3, 2, 2, 1, 1.0, null, 1)
print report["task"]
print report["n_used"]
print round(report["train_accuracy"], 3)
print report["features"]

let mrows = [{"a": 0, "b": 0, "label": 0}, {"a": 1, "b": 0, "label": 0}, {"a": 2, "b": 0, "label": 1}, {"a": 3, "b": 0, "label": 1}, {"a": 4, "b": 0, "label": 2}, {"a": 5, "b": 0, "label": 2}]
let multi = analysis.boosting_report(mrows, "label", ["a", "b"], "auto", 5, 0.2, 2)
print multi["task"]
print multi["classes"]
print round(multi["train_accuracy"], 3)
'''
    out = []
    execute(src, output=out.append, source_name="boosting.pea")
    assert out == [
        "classification",
        "[0, 1]",
        "[0, 1]",
        "1",
        "10",
        "x",
        "0.022",
        "classification",
        "6",
        "1",
        '["x"]',
        "classification",
        "[0, 1, 2]",
        "1",
    ]
