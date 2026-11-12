from pealang import selection as s
from pealang import execute


X = [[index / 2.0] for index in range(40)]
Y = [3 + 2 * (index / 2.0) for index in range(40)]
LABELS = [0 if (index / 2.0) < 10 else 1 for index in range(40)]


def test_cross_validate_regression():
    report = s.cross_validate("tree", X, Y, "regression", {"max_depth": 3}, 5, 1, "r2")
    assert report["estimator"] == "tree"
    assert report["task"] == "regression"
    assert report["scoring"] == "r2"
    assert report["folds"] == 5
    assert len(report["scores"]) == 5
    assert report["mean"] > 0.9
    assert report["std"] >= 0.0
    assert report["higher_is_better"] is True
    assert report["params"] == {"max_depth": 3}


def test_cross_validate_classification():
    report = s.cross_validate(
        "forest", X, LABELS, "classification",
        {"n_estimators": 10, "max_depth": 3}, 5, 1, "accuracy",
    )
    assert report["scoring"] == "accuracy"
    assert report["folds"] == 5
    assert report["mean"] > 0.9
    assert report["higher_is_better"] is True


def test_cross_validate_lower_is_better():
    report = s.cross_validate(
        "tree", X, Y, "regression", {"max_depth": 3}, 5, 1, "rmse"
    )
    assert report["scoring"] == "rmse"
    assert report["mean"] > 0.0
    assert report["higher_is_better"] is False


def test_cross_validate_roc_auc():
    report = s.cross_validate(
        "boosting", X, LABELS, "classification",
        {"n_estimators": 10}, 3, 1, "roc_auc",
    )
    assert report["scoring"] == "roc_auc"
    assert report["mean"] > 0.9


def test_grid_search():
    report = s.grid_search(
        "tree", X, Y, "regression",
        {"max_depth": [1, 2, 3], "min_samples_leaf": [1, 2]}, 5, 1, "r2",
    )
    assert report["estimator"] == "tree"
    assert report["task"] == "regression"
    assert report["scoring"] == "r2"
    assert report["n_candidates"] == 6
    assert len(report["results"]) == 6
    means = [entry["mean"] for entry in report["results"]]
    assert means == sorted(means, reverse=True)
    assert report["best_score"] == means[0]
    assert report["best_params"] == report["results"][0]["params"]
    assert set(report["best_params"]) == {"max_depth", "min_samples_leaf"}
    assert report["best_model"]["estimator"] == "decision_tree"
    assert len(s._predict("tree", report["best_model"], X)["predicted"]) == len(X)


def test_grid_search_lower_is_better():
    report = s.grid_search(
        "tree", X, Y, "regression", {"max_depth": [1, 2, 3]}, 5, 1, "rmse"
    )
    assert report["higher_is_better"] is False
    means = [entry["mean"] for entry in report["results"]]
    assert means == sorted(means)
    assert report["best_score"] == means[0]


def test_random_search():
    first = s.random_search(
        "forest", X, LABELS, "classification",
        {"n_estimators": [5, 10, 15], "max_depth": [2, 3]}, 4, 5, 2, "accuracy",
    )
    second = s.random_search(
        "forest", X, LABELS, "classification",
        {"n_estimators": [5, 10, 15], "max_depth": [2, 3]}, 4, 5, 2, "accuracy",
    )
    assert first["n_candidates"] == 4
    assert first["task"] == "classification"
    assert first["best_model"]["estimator"] == "random_forest"
    assert [entry["params"] for entry in first["results"]] == [
        entry["params"] for entry in second["results"]
    ]
    assert first["best_score"] == second["best_score"]


def test_estimator_aliases():
    assert s._estimator_key("decision_tree") == "tree"
    assert s._estimator_key("random_forest") == "forest"
    assert s._estimator_key("gradient_boosting") == "boosting"
    assert s._estimator_key("gbm") == "boosting"


def test_selection_validation():
    cases = [
        (lambda: s.cross_validate("nope", X, Y), "estimator"),
        (lambda: s.cross_validate("tree", X, Y, "regression", None, 1), "folds"),
        (lambda: s.cross_validate("tree", X, Y, "regression", None, 100), "folds"),
        (lambda: s.cross_validate("tree", X, Y, "regression", None, 5, 0, "accuracy"), "scoring"),
        (lambda: s.grid_search("tree", X, Y, "regression", {"max_depth": 3}), "lists"),
        (lambda: s.grid_search("tree", X, Y, "regression", {"max_depth": []}), "empty"),
        (lambda: s.grid_search("tree", X, Y, "regression", {"nope": [1]}), "unknown"),
        (lambda: s.random_search("tree", X, Y, "regression", None, 0), "n_iter"),
        (lambda: s.cross_validate("tree", X, Y[:-1]), "lengths"),
        (lambda: s.cross_validate(
            "tree", [[0], [1], [2], [3], [4], [5]], [0, 0, 1, 2, 2, 2],
            "classification", {"max_depth": 2}, 2, 0, "roc_auc",
        ), "binary"),
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
let x = [[0], [1], [2], [3], [4], [5], [6], [7]]
let y = [0, 0, 0, 0, 1, 1, 1, 1]
let cv = stats.cross_validate("tree", x, y, "classification", {"max_depth": 2}, 4, 1, "accuracy")
print cv["scoring"]
print cv["folds"]
print round(cv["mean"], 3)
print cv["higher_is_better"]
let gs = stats.grid_search("tree", x, y, "classification", {"max_depth": [1, 2]}, 4, 1, "accuracy")
print gs["best_params"]
print gs["n_candidates"]
print gs["best_model"]["estimator"]
print round(gs["best_score"], 3)
let rs = stats.random_search("tree", x, y, "classification", {"max_depth": [1, 2, 3]}, 3, 4, 2, "accuracy")
print rs["n_candidates"]
print rs["task"]
let rows = [{"a": 0, "b": 0, "label": 0}, {"a": 1, "b": 0, "label": 0}, {"a": 2, "b": 0, "label": 1}, {"a": 3, "b": 0, "label": 1}, {"a": 4, "b": 0, "label": 2}, {"a": 5, "b": 0, "label": 2}]
let tuned = analysis.tune_model(rows, "label", ["a", "b"], "tree", "auto", {"max_depth": [1, 2]}, 3, 1, "accuracy")
print tuned["task"]
print tuned["features"]
print tuned["n_used"]
print tuned["best_model"]["importance"][0]["feature"]
print round(tuned["best_score"], 3)
let random_tuned = analysis.random_tune(rows, "label", ["a", "b"], "tree", "auto", {"max_depth": [1, 2]}, 2, 3, 1, "accuracy")
print random_tuned["n_candidates"]
print random_tuned["task"]
'''
    out = []
    execute(src, output=out.append, source_name="selection.pea")
    assert out == [
        "accuracy",
        "4",
        "0.875",
        "true",
        '{"max_depth": 1}',
        "2",
        "decision_tree",
        "0.875",
        "3",
        "classification",
        "classification",
        '["a", "b"]',
        "6",
        "a",
        "0.5",
        "2",
        "classification",
    ]
