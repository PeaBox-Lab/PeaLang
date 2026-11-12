import math

from pealang import trees as t
from pealang import execute


def approx(actual, expected, tol=1e-9):
    assert abs(actual - expected) <= tol, (actual, expected)


X = [[index] for index in range(10)]
Y = [2 * index + 1 for index in range(10)]
LABELS = [0 if index < 5 else 1 for index in range(10)]


def test_regression_tree():
    model = t.decision_tree(X, Y, "regression", max_depth=3)
    assert model["estimator"] == "decision_tree"
    assert model["task"] == "regression"
    assert model["n"] == 10
    assert model["n_features"] == 1
    assert model["classes"] == []
    assert model["max_depth"] == 3
    assert model["feature_importances"] == [1.0]

    predicted = t.predict_tree(model, X)["predicted"]
    assert predicted == [1.0, 3.0, 5.0, 8.0, 8.0, 11.0, 13.0, 15.0, 18.0, 18.0]


def test_regression_tree_depth_cap():
    model = t.decision_tree(X, Y, "regression")
    assert model["max_depth"] == 100
    assert t.predict_tree(model, X)["predicted"] == [float(value) for value in Y]


def test_classification_tree():
    model = t.decision_tree(X, LABELS, "classification", max_depth=3)
    assert model["task"] == "classification"
    assert model["classes"] == [0, 1]

    result = t.predict_tree(model, X)
    assert result["predicted"] == LABELS
    assert result["classes"] == [0, 1]
    for probabilities in result["probabilities"]:
        approx(sum(probabilities), 1.0)
    assert result["probabilities"][0] == [1.0, 0.0]
    assert result["probabilities"][-1] == [0.0, 1.0]


def test_classification_tree_string_labels():
    labels = ["b" if index < 5 else "a" for index in range(10)]
    model = t.decision_tree(X, labels, "classification")
    assert model["classes"] == ["a", "b"]
    assert t.predict_tree(model, [[0], [9]])["predicted"] == ["b", "a"]


def test_tree_feature_importance():
    rows = []
    target = []
    for index in range(60):
        a = (index % 10) / 10.0
        b = ((index * 7) % 13) / 13.0
        rows.append([a, b])
        target.append(1 if a > 0.5 else 0)
    model = t.decision_tree(rows, target, "classification", max_depth=4)
    assert model["feature_importances"] == [1.0, 0.0]
    table = t.tree_feature_importance(model, ["signal", "noise"])
    assert table[0]["feature"] == "signal"
    assert table[0]["importance"] == 1.0
    assert table[1] == {"feature": "noise", "importance": 0.0}

    default = t.tree_feature_importance(model)
    assert [entry["feature"] for entry in default] == ["x1", "x2"]


def test_tree_validation():
    cases = [
        (lambda: t.decision_tree(X, Y, "nope"), "task"),
        (lambda: t.decision_tree(X, Y, "regression", 0), "max_depth"),
        (lambda: t.decision_tree(X, Y, "regression", 2, 1), "min_samples_split"),
        (lambda: t.decision_tree(X, Y, "regression", 2, 2, 0), "min_samples_leaf"),
        (lambda: t.decision_tree(X, Y[:-1], "regression"), "lengths"),
        (lambda: t.decision_tree([], [], "regression"), "features"),
        (lambda: t.decision_tree(X, Y, "regression", 2, 2, 1, 0), "max_features"),
        (lambda: t.decision_tree(X, Y, "regression", 2, 2, 1, "bad"), "max_features"),
        (lambda: t.decision_tree(X, Y, "regression", 2, 2, 1, 1.5), "max_features"),
        (lambda: t.tree_feature_importance(t.decision_tree(X, Y), ["a", "b"]), "names"),
        (lambda: t.random_forest(X, Y, "regression", 0), "n_estimators"),
    ]
    for call, fragment in cases:
        try:
            call()
        except ValueError as error:
            assert fragment in str(error), (fragment, str(error))
        else:
            raise AssertionError("expected ValueError for " + fragment)


def test_feature_count():
    assert t._feature_count(None, 7) == 7
    assert t._feature_count("all", 7) == 7
    assert t._feature_count("sqrt", 9) == 3
    assert t._feature_count("log2", 8) == 3
    assert t._feature_count(0.5, 5) == 3
    assert t._feature_count(4, 3) == 3
    assert t._feature_count(2, 9) == 2


def test_random_forest_regression():
    model = t.random_forest(X, Y, "regression", 20, max_depth=4, seed=3)
    assert model["estimator"] == "random_forest"
    assert model["n_estimators"] == 20
    assert len(model["trees"]) == 20
    assert model["feature_importances"] == [1.0]
    approx(model["oob_score"], 0.896834250313458)
    predicted = t.predict_forest(model, X)["predicted"]
    assert [round(value, 2) for value in predicted] == [
        2.3, 2.7, 4.2, 6.7, 8.9, 10.4, 12.4, 14.3, 16.7, 18.6
    ]


def test_random_forest_determinism():
    first = t.random_forest(X, Y, "regression", 10, max_depth=4, seed=11)
    second = t.random_forest(X, Y, "regression", 10, max_depth=4, seed=11)
    other = t.random_forest(X, Y, "regression", 10, max_depth=4, seed=12)
    assert t.predict_forest(first, X)["predicted"] == t.predict_forest(second, X)["predicted"]
    assert first["oob_score"] == second["oob_score"]
    assert t.predict_forest(first, X)["predicted"] != t.predict_forest(other, X)["predicted"]


def test_random_forest_classification():
    model = t.random_forest(X, LABELS, "classification", 20, max_depth=4, seed=3)
    assert model["classes"] == [0, 1]
    result = t.predict_forest(model, X)
    assert result["predicted"] == LABELS
    assert model["oob_score"] == 0.9
    for probabilities in result["probabilities"]:
        approx(sum(probabilities), 1.0)
    assert t.predict_forest(model, [[0], [9]])["predicted"] == [0, 1]


def test_random_forest_without_bootstrap():
    model = t.random_forest(X, Y, "regression", 5, max_depth=3, bootstrap=False, seed=1)
    assert model["bootstrap"] is False
    assert model["oob_score"] is None
    assert model["oob_predictions"] == []
    assert len(t.predict_forest(model, X)["predicted"]) == 10


def test_forest_importance():
    model = t.random_forest(X, LABELS, "classification", 10, max_depth=3, seed=2)
    table = t.forest_feature_importance(model, ["x"])
    assert table[0]["feature"] == "x"
    approx(table[0]["importance"], 1.0)


def test_namespace_and_record_wrappers():
    src = r'''
let tree = stats.decision_tree([[0], [1], [2], [3], [4], [5]], [0, 0, 0, 1, 1, 1], "classification", 3)
print tree["task"]
print tree["classes"]
print stats.predict_tree(tree, [[0], [5]])["predicted"]
print stats.predict_tree(tree, [[0]])["probabilities"]
let forest = stats.random_forest([[0], [1], [2], [3], [4], [5]], [0, 0, 0, 1, 1, 1], "classification", 5, 3, 2, 1, "all", true, 1)
print len(forest["trees"])
print round(forest["oob_score"], 3)
print stats.tree_feature_importance(tree, ["x"])[0]["feature"]
print round(std.stats.forest_feature_importance(forest, ["x"])[0]["importance"], 3)
print stats.predict_forest(forest, [[0], [5]])["predicted"]

let rows = [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 0}, {"x": 3, "y": 1}, {"x": 4, "y": 1}, {"x": 5, "y": 1}]
let report = analysis.tree_report(rows, "y", ["x"], "auto", 3)
print report["task"]
print report["n_used"]
print report["train_accuracy"]
print report["importance"][0]["feature"]

let forest_report = analysis.forest_report(rows, "y", null, "auto", 5, 3, 2, 1, "all", true, 2)
print forest_report["task"]
print forest_report["n_used"]
print forest_report["features"]
print round(forest_report["train_accuracy"], 3)
'''
    out = []
    execute(src, output=out.append, source_name="trees.pea")
    assert out == [
        "classification",
        "[0, 1]",
        "[0, 1]",
        "[[1.0, 0.0]]",
        "5",
        "0.6",
        "x",
        "1",
        "[0, 1]",
        "classification",
        "6",
        "1",
        "x",
        "classification",
        "6",
        '["x"]',
        "1",
    ]


def test_record_wrapper_regression():
    src = r'''
let rows = []
for i in range(0, 20) {
    let x = i / 2.0
    rows = rows + [{"x": x, "y": 2 * x + 1}]
}
let tree = analysis.tree_report(rows, "y", ["x"], "regression", 3)
print tree["n_used"]
print tree["features"]
print round(tree["train_r2"], 3)
print round(tree["train_rmse"], 3)
print round(tree["importance"][0]["importance"], 3)
print stats.predict_tree(tree, [[2.0], [4.0]])["predicted"]
'''
    out = []
    execute(src, output=out.append, source_name="tree_regression.pea")
    assert out == ["20", '["x"]', "0.985", "0.707", "1", "[4.0, 9.0]"]
