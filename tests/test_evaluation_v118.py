import math

from pealang import evaluation as e
from pealang import execute


def approx(actual, expected, tol=1e-9):
    assert abs(actual - expected) <= tol, (actual, expected)


def test_train_test_split():
    features = [[value] for value in range(10)]
    target = [0] * 5 + [1] * 5
    result = e.train_test_split(features, target, 0.3, True, 7)
    assert result["n_train"] == 7
    assert result["n_test"] == 3
    assert sorted(result["train_index"] + result["test_index"]) == list(range(10))
    assert set(result["train_index"]).isdisjoint(result["test_index"])
    assert result["X_train"] == [features[i] for i in result["train_index"]]
    assert result["y_test"] == [target[i] for i in result["test_index"]]

    again = e.train_test_split(features, target, 0.3, True, 7)
    assert again["test_index"] == result["test_index"]

    ordered = e.train_test_split(features, target, 0.3, False, None)
    assert ordered["test_index"] == [0, 1, 2]


def test_train_test_split_stratified():
    features = [[value] for value in range(10)]
    target = [0] * 5 + [1] * 5
    result = e.train_test_split(features, target, 0.3, True, 7, target)
    assert result["stratified"] is True
    labels = [target[i] for i in result["test_index"]]
    assert labels.count(0) == 2
    assert labels.count(1) == 1

    imbalanced = [0] * 8 + [1] * 2
    split = e.train_test_split(features, imbalanced, 0.3, True, 1, imbalanced)
    held_out = [imbalanced[i] for i in split["test_index"]]
    assert held_out.count(1) == 1
    assert len(held_out) == 3


def test_k_fold():
    folds = e.k_fold(10, 5, True, 1)
    assert len(folds) == 5
    covered = sorted(index for fold in folds for index in fold["test"])
    assert covered == list(range(10))
    for fold in folds:
        assert fold["n_train"] + fold["n_test"] == 10
        assert set(fold["train"]).isdisjoint(fold["test"])


def test_stratified_k_fold():
    labels = [0] * 8 + [1] * 4
    folds = e.stratified_k_fold(labels, 4, True, 1)
    assert len(folds) == 4
    covered = sorted(index for fold in folds for index in fold["test"])
    assert covered == list(range(12))
    for fold in folds:
        held_out = [labels[i] for i in fold["test"]]
        assert 0 in held_out
        assert 1 in held_out

    try:
        e.stratified_k_fold([0] * 8 + [1] * 2, 4)
    except ValueError:
        pass
    else:
        raise AssertionError("stratification should reject classes smaller than k")


def test_classification_metrics():
    actual = [0, 0, 1, 1, 1, 0]
    predicted = [0, 1, 1, 1, 0, 0]
    approx(e.accuracy_score(actual, predicted), 2 / 3)
    approx(e.balanced_accuracy(actual, predicted), 2 / 3)
    result = e.precision_recall_fscore(actual, predicted)
    approx(result["precision"], 2 / 3)
    approx(result["recall"], 2 / 3)
    approx(result["f1"], 2 / 3)
    approx(result["accuracy"], 2 / 3)
    assert result["positive"] == 1
    assert [entry["label"] for entry in result["per_class"]] == [0, 1]
    for entry in result["per_class"]:
        approx(entry["precision"], 2 / 3)
        approx(entry["support"], 3)

    multiclass = e.precision_recall_fscore([0, 1, 2, 2], [0, 1, 2, 0])
    assert multiclass["positive"] is None
    approx(multiclass["accuracy"], 0.75)


def test_roc_auc_and_curve():
    approx(e.roc_auc([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]), 0.75)
    assert e.roc_auc([0, 1, 1, 1], [0.1, 0.2, 0.3, 0.4]) == 1.0
    assert e.roc_auc([0, 1, 1, 1], [0.9, 0.8, 0.7, 0.6]) == 0.0
    assert e.roc_auc([0, 1], [0.5, 0.5]) == 0.5

    curve = e.roc_curve([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8])
    assert curve["fpr"] == [0.0, 0.5, 0.5, 1.0]
    assert curve["tpr"] == [0.5, 0.5, 1.0, 1.0]
    approx(curve["auc"], 0.75)
    assert len(curve["thresholds"]) == 4


def test_probability_metrics():
    actual = [0, 0, 1, 1]
    scores = [0.1, 0.4, 0.35, 0.8]
    expected = -(math.log(0.9) + math.log(0.6) + math.log(0.35) + math.log(0.8)) / 4
    approx(e.log_loss(actual, scores), expected)
    approx(e.brier_score(actual, scores), 0.158125)

    curve = e.calibration_curve([0, 0, 1, 1, 1, 0], [0.05, 0.15, 0.35, 0.45, 0.85, 0.95], 5)
    assert [row["count"] for row in curve["table"]] == [2, 1, 1, 0, 2]
    approx(curve["table"][0]["mean_predicted"], 0.1)
    approx(curve["table"][0]["fraction_positive"], 0.0)
    assert curve["table"][3]["mean_predicted"] is None


def test_regression_metrics():
    actual = [3, -0.5, 2, 7]
    predicted = [2.5, 0.0, 2, 8]
    approx(e.mean_squared_error(actual, predicted), 0.375)
    approx(e.root_mean_squared_error(actual, predicted), math.sqrt(0.375))
    approx(e.mean_absolute_error(actual, predicted), 0.5)
    approx(e.median_absolute_error(actual, predicted), 0.5)
    approx(e.r2_score(actual, predicted), 0.9486081370449679)
    approx(e.explained_variance_score(actual, predicted), 0.9571734475374732)
    approx(e.mean_absolute_percentage_error([100, 200], [110, 180]), 0.1)
    assert e.r2_score([1, 2, 3], [1, 2, 3]) == 1.0


def test_polynomial_features():
    result = e.polynomial_features([[2, 3], [4, 5]], 2)
    assert result["names"] == ["x1", "x2", "x1^2", "x1*x2", "x2^2"]
    assert result["features"][0] == [2.0, 3.0, 4.0, 6.0, 9.0]
    assert result["features"][1] == [4.0, 5.0, 16.0, 20.0, 25.0]

    interactions = e.polynomial_features([[2, 3]], 2, False, True)
    assert interactions["names"] == ["x1", "x2", "x1*x2"]
    assert interactions["features"] == [[2.0, 3.0, 6.0]]

    biased = e.polynomial_features([[2, 3]], 1, True)
    assert biased["names"] == ["1", "x1", "x2"]
    assert biased["features"] == [[1.0, 2.0, 3.0]]


def test_encoders():
    encoded = e.label_encode(["b", "a", "b", "c"])
    assert encoded["codes"] == [0, 1, 0, 2]
    assert encoded["classes"] == ["b", "a", "c"]
    assert encoded["n_classes"] == 3

    ordinal = e.ordinal_encode(["b", "a", "b"], ["a", "b"])
    assert ordinal["codes"] == [1, 0, 1]
    assert ordinal["classes"] == ["a", "b"]


def test_feature_scaling():
    result = e.standardize_features([[1, 10], [2, 20], [3, 30]])
    assert result["means"] == [2.0, 20.0]
    assert result["stds"] == [1.0, 10.0]
    assert result["features"] == [[-1.0, -1.0], [0.0, 0.0], [1.0, 1.0]]
    assert e.standardize_transform([[4, 40]], result["means"], result["scales"]) == [[2.0, 2.0]]

    scaled = e.minmax_features([[1, 10], [2, 20], [3, 30]])
    assert scaled["mins"] == [1.0, 10.0]
    assert scaled["maxs"] == [3.0, 30.0]
    assert scaled["features"] == [[0.0, 0.0], [0.5, 0.5], [1.0, 1.0]]
    assert e.minmax_transform([[4, 40]], scaled["mins"], scaled["ranges"]) == [[1.5, 1.5]]


def test_namespace_and_record_wrappers():
    src = r'''
print round(stats.accuracy_score([0, 0, 1, 1], [0, 1, 1, 1]), 3)
print round(stats.roc_auc([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]), 3)
print round(stats.r2_score([1, 2, 3], [1, 2, 3]), 3)
print stats.polynomial_features([[2, 3]], 2)["names"][3]
print stats.label_encode(["a", "b", "a"])["codes"][1]
print round(std.stats.mean_squared_error([1, 2], [1, 3]), 3)

let rows = [{"y": 1, "p": 1.1}, {"y": 2, "p": 1.9}, {"y": 3, "p": 3.2}]
let metrics = analysis.evaluate_regression(rows, "y", "p")
print metrics["n"]
print round(metrics["r2"], 3)

let classes = [{"a": 0, "b": 0, "s": 0.1}, {"a": 0, "b": 1, "s": 0.4}, {"a": 1, "b": 1, "s": 0.7}, {"a": 1, "b": 1, "s": 0.9}]
let quality = analysis.evaluate_classification(classes, "a", "b", "s")
print round(quality["accuracy"], 3)
print round(quality["roc_auc"], 3)

let holdout = analysis.train_test_split(rows, 0.34, 1)
print holdout["n_train"]
print holdout["n_test"]

let expanded = analysis.add_polynomial_features([{"x1": 2, "x2": 3}], ["x1", "x2"], 2)
print expanded[0]["x1*x2"]
'''
    out = []
    execute(src, output=out.append, source_name="evaluation.pea")
    assert out == [
        "0.75",
        "0.75",
        "1",
        "x1*x2",
        "1",
        "0.5",
        "3",
        "0.97",
        "0.75",
        "1",
        "1",
        "2",
        "6",
    ]
