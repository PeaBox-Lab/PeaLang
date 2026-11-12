from pealang import boosting as b
from pealang import execute
from pealang import interpret as i
from pealang import trees as t


def build_regression():
    rows = []
    target = []
    for index in range(40):
        x = index / 4.0
        noise = ((index * 7) % 11) / 11.0
        rows.append([x, noise])
        target.append(3 * x + 2)
    return rows, target


def test_permutation_importance_regression():
    rows, target = build_regression()
    model = b.gradient_boosting(
        rows, target, "regression", 20, 0.2, 2, 2, 1, 1.0, None, 1
    )
    report = i.permutation_importance(
        model, rows, target, "regression", 5, 3, "r2", ["x", "noise"]
    )
    assert report["estimator"] == "gradient_boosting"
    assert report["task"] == "regression"
    assert report["scoring"] == "r2"
    assert report["higher_is_better"] is True
    assert report["n_repeats"] == 5
    assert report["seed"] == 3
    assert report["baseline"] > 0.99
    top, noise = report["importances"]
    assert top["feature"] == "x"
    assert top["mean"] > 1.0
    assert len(top["values"]) == 5
    assert top["std"] >= 0.0
    assert noise["feature"] == "noise"
    assert abs(noise["mean"]) < 1e-3
    assert abs(noise["std"]) < 1e-3


def test_permutation_importance_classification():
    rows, _ = build_regression()
    labels = [0 if row[0] < 5 else 1 for row in rows]
    model = t.random_forest(
        rows, labels, "classification", 15, 3, 2, 1, "sqrt", True, 4
    )
    report = i.permutation_importance(
        model, rows, labels, "auto", 4, 1, "accuracy", ["x", "noise"]
    )
    assert report["task"] == "classification"
    assert report["scoring"] == "accuracy"
    assert report["baseline"] == 1.0
    assert report["importances"][0]["feature"] == "x"
    assert report["importances"][0]["mean"] > 0.3
    assert report["importances"][1]["mean"] == 0.0


def test_permutation_importance_lower_is_better():
    rows, target = build_regression()
    model = b.gradient_boosting(rows, target, "regression", 10, 0.2, 2, 2, 1)
    report = i.permutation_importance(
        model, rows, target, "regression", 2, 0, "rmse"
    )
    assert report["scoring"] == "rmse"
    assert report["higher_is_better"] is False
    assert report["importances"][0]["feature"] == "x1"
    assert report["importances"][0]["mean"] > 0.0


def test_partial_dependence_regression():
    rows, target = build_regression()
    model = b.gradient_boosting(
        rows, target, "regression", 20, 0.2, 2, 2, 1, 1.0, None, 1
    )
    report = i.partial_dependence(
        model, rows, ["x"], 5, "regression", ["x", "noise"]
    )
    assert report["estimator"] == "gradient_boosting"
    assert report["task"] == "regression"
    assert report["grid_size"] == 5
    assert len(report["curves"]) == 1
    curve = report["curves"][0]
    assert curve["feature"] == "x"
    assert curve["values"] == sorted(curve["values"])
    assert curve["values"][0] == 0.0
    assert curve["values"][-1] == 9.75
    assert curve["average"] == sorted(curve["average"])
    assert curve["average"][-1] - curve["average"][0] > 20.0
    assert "classes" not in curve


def test_partial_dependence_classification():
    rows, _ = build_regression()
    labels = [0 if row[0] < 5 else 1 for row in rows]
    model = t.random_forest(
        rows, labels, "classification", 15, 3, 2, 1, "sqrt", True, 4
    )
    report = i.partial_dependence(
        model, rows, [0], 4, "auto", ["x", "noise"]
    )
    curve = report["curves"][0]
    assert curve["classes"] == [0, 1]
    assert len(curve["probabilities"]) == 2
    assert all(len(row) == 4 for row in curve["probabilities"])
    assert curve["average"] == curve["probabilities"][1]
    for position in range(4):
        total = sum(row[position] for row in curve["probabilities"])
        assert abs(total - 1.0) < 1e-9
    assert curve["average"][0] < curve["average"][-1]


def test_partial_dependence_multiclass():
    rows, _ = build_regression()
    labels = [0 if row[0] < 3 else (1 if row[0] < 7 else 2) for row in rows]
    model = b.gradient_boosting(
        rows, labels, "classification", 10, 0.2, 2, 2, 1, 1.0, None, 2
    )
    report = i.partial_dependence(model, rows, None, 3, "auto", ["x", "noise"])
    assert len(report["curves"]) == 2
    curve = report["curves"][0]
    assert curve["classes"] == [0, 1, 2]
    assert len(curve["probabilities"]) == 3
    assert all(len(row) == 3 for row in curve["probabilities"])


def test_interpret_validation():
    rows, target = build_regression()
    model = b.gradient_boosting(rows, target, "regression", 5, 0.2, 2, 2, 1)
    cases = [
        (lambda: i.permutation_importance({}, rows, target), "model"),
        (lambda: i.permutation_importance(model, rows, target, "regression", 0), "n_repeats"),
        (lambda: i.permutation_importance(model, rows, target[:-1], "regression"), "lengths"),
        (lambda: i.permutation_importance(model, rows, target, "regression", 1, 0, "r2", ["a"]), "names"),
        (lambda: i.permutation_importance(model, rows, target, "regression", 1, 0, "accuracy"), "scoring"),
        (lambda: i.partial_dependence(model, rows, None, 1), "grid_size"),
        (lambda: i.partial_dependence(model, rows, [5], 3), "range"),
        (lambda: i.partial_dependence(model, rows, ["zzz"], 3, "auto", ["x", "noise"]), "unknown"),
        (lambda: i.partial_dependence(model, rows, [], 3), "empty"),
    ]
    for call, fragment in cases:
        try:
            call()
        except ValueError as error:
            assert fragment in str(error), (fragment, str(error))
        else:
            raise AssertionError("expected ValueError for " + fragment)


def test_namespace_and_record_wrappers():
    src = r'''
let rows = []
for k in range(0, 24) {
    let x = k / 2.0
    let noise = ((k * 5) % 7) / 7.0
    rows = rows + [{"x": x, "noise": noise, "y": 2.0 * x + 1.0}]
}
let model = analysis.interpret_report(rows, "y", ["x", "noise"], "boosting", "regression", {"n_estimators": 10, "learning_rate": 0.2, "max_depth": 2}, 3, 4, 5, "r2", ["x"])
print model["estimator"]
print model["n_used"]
print model["features"]
print model["scoring"]
print model["permutation_importance"][0]["feature"]
print round(model["baseline"], 2)
print model["partial_dependence"][0]["feature"]
print len(model["partial_dependence"][0]["values"])
print round(model["partial_dependence"][0]["average"][0], 2)
print round(model["partial_dependence"][0]["average"][-1], 2)
print len(model["importance"])
let pi = stats.permutation_importance(model, [[r["x"], r["noise"]] for r in rows], [r["y"] for r in rows], "regression", 3, 5, "r2", ["x", "noise"])
print pi["importances"][0]["feature"]
print len(pi["importances"])
let pd = stats.partial_dependence(model, [[r["x"], r["noise"]] for r in rows], [0], 3, "regression", ["x", "noise"])
print pd["curves"][0]["feature"]
print len(pd["curves"])
print std.stats.permutation_importance(model, [[r["x"], r["noise"]] for r in rows], [r["y"] for r in rows], "regression", 2, 1, "r2")["importances"][0]["feature"]
'''
    out = []
    execute(src, output=out.append, source_name="interpret.pea")
    assert out == [
        "gradient_boosting",
        "24",
        '["x", "noise"]',
        "r2",
        "x",
        "0.98",
        "x",
        "4",
        "3.06",
        "21.78",
        "2",
        "x",
        "2",
        "x",
        "1",
        "x1",
    ]
