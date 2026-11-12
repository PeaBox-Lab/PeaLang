from pealang import analysis as a
from pealang import execute
from pealang import pipeline as p


def build_numeric():
    rows = [[1.0, 2.0], [None, 4.0], [3.0, None], [5.0, 8.0]]
    return rows, ["a", "b"]


def build_categorical():
    rows = [["red", 1.0], ["blue", 2.0], ["red", 3.0], ["green", 4.0]]
    return rows, ["color", "size"]


def test_impute_methods():
    rows, names = build_numeric()
    mean = p.fit_pipeline([{"op": "impute", "method": "mean"}], rows, names)
    assert mean["features"] == [
        [1.0, 2.0], [3.0, 4.0], [3.0, 14.0 / 3.0], [5.0, 8.0]
    ]
    assert mean["steps"][0]["missing"] == 2
    assert mean["steps"][0]["fills"][0] == {
        "name": "a", "method": "mean", "value": 3.0, "missing": 1
    }

    median = p.fit_pipeline([{"op": "impute", "method": "median"}], rows, names)
    assert median["features"][1][0] == 3.0
    assert median["features"][2][1] == 4.0

    categorical = [["red"], ["blue"], ["blue"], [None]]
    mode = p.fit_pipeline([{"op": "impute", "method": "auto"}], categorical, ["color"])
    assert mode["features"] == [["red"], ["blue"], ["blue"], ["blue"]]
    assert mode["steps"][0]["fills"][0]["method"] == "mode"

    constant = p.fit_pipeline(
        [{"op": "impute", "method": "constant", "value": 0}], rows, names
    )
    assert constant["features"][1][0] == 0
    assert constant["features"][2][1] == 0

    zero = p.fit_pipeline([{"op": "impute", "method": "zero"}], rows, names)
    assert zero["features"][1][0] == 0.0
    assert zero["features"][2][1] == 0.0


def test_onehot_encoding_and_unseen_levels():
    rows, names = build_categorical()
    fitted = p.fit_pipeline([{"op": "encode", "method": "onehot"}], rows, names)
    assert fitted["names"] == ["color=blue", "color=green", "color=red", "size"]
    assert fitted["n_features"] == 4
    assert fitted["features"] == [
        [0.0, 0.0, 1.0, 1.0],
        [1.0, 0.0, 0.0, 2.0],
        [0.0, 0.0, 1.0, 3.0],
        [0.0, 1.0, 0.0, 4.0],
    ]
    new = p.transform_pipeline(fitted, [["blue", 5.0], ["purple", 6.0]])
    assert new["features"] == [
        [1.0, 0.0, 0.0, 5.0],
        [0.0, 0.0, 0.0, 6.0],
    ]


def test_ordinal_encoding_and_unseen_levels():
    rows, names = build_categorical()
    fitted = p.fit_pipeline([{"op": "encode", "method": "ordinal"}], rows, names)
    assert fitted["names"] == ["color", "size"]
    assert fitted["features"] == [
        [2.0, 1.0], [0.0, 2.0], [2.0, 3.0], [1.0, 4.0]
    ]
    new = p.transform_pipeline(fitted, [["purple", 1.0], ["red", 2.0]])
    assert new["features"] == [[-1.0, 1.0], [2.0, 2.0]]

    label = p.fit_pipeline([{"op": "encode", "method": "label"}], rows, names)
    assert label["features"] == fitted["features"]


def test_scaling():
    fitted = p.fit_pipeline(
        [{"op": "scale", "method": "standard"}],
        [[1.0], [2.0], [3.0], [4.0]],
        ["x"],
    )
    values = [row[0] for row in fitted["features"]]
    assert abs(sum(values)) < 1e-12
    assert abs(values[0] + values[3]) < 1e-12

    minmax = p.fit_pipeline(
        [{"op": "scale", "method": "minmax"}], [[1.0], [2.0], [5.0]], ["x"]
    )
    assert minmax["features"] == [[0.0], [0.25], [1.0]]
    assert minmax["steps"][0]["columns"] == [
        {"name": "x", "center": 1.0, "scale": 4.0}
    ]


def test_full_pipeline_roundtrip():
    rows = [["red", 1.0], [None, None], ["blue", 3.0], ["red", 4.0]]
    names = ["color", "size"]
    steps = [
        {"op": "impute", "method": "auto"},
        {"op": "encode", "method": "onehot"},
        {"op": "scale", "method": "standard"},
    ]
    fitted = p.fit_pipeline(steps, rows, names)
    assert fitted["names"] == ["color=blue", "color=red", "size"]
    assert fitted["n"] == 4
    assert len(fitted["steps"]) == 3
    assert fitted["steps"][0]["missing"] == 2
    again = p.transform_pipeline(fitted, rows)
    assert again["features"] == fitted["features"]
    assert again["names"] == fitted["names"]


def test_pipeline_validation():
    rows, names = build_numeric()
    categorical, cat_names = build_categorical()
    fitted = p.fit_pipeline(
        [{"op": "encode", "method": "onehot"}], categorical, cat_names
    )
    cases = [
        (lambda: p.fit_pipeline([], rows), "steps"),
        (lambda: p.fit_pipeline([{"op": "nope"}], rows), "unknown"),
        (lambda: p.fit_pipeline(["x"], rows), "dict"),
        (lambda: p.fit_pipeline([{"op": "impute", "method": "mean"}], [["red"]], ["c"]), "numeric"),
        (lambda: p.fit_pipeline([{"op": "impute", "method": "constant"}], rows), "value"),
        (lambda: p.fit_pipeline([{"op": "scale"}], categorical, cat_names), "numeric"),
        (lambda: p.fit_pipeline([{"op": "scale"}], rows, names), "impute"),
        (lambda: p.fit_pipeline([{"op": "encode", "method": "wat"}], categorical, cat_names), "onehot"),
        (lambda: p.fit_pipeline([{"op": "scale", "method": "wat"}], rows, names), "standard"),
        (lambda: p.transform_pipeline(fitted, [[1.0]]), "features"),
        (lambda: p.transform_pipeline({}, categorical), "fitted"),
        (lambda: p.fit_pipeline([{"op": "impute"}], rows, ["a"]), "names"),
    ]
    for call, fragment in cases:
        try:
            call()
        except ValueError as error:
            assert fragment in str(error), (fragment, str(error))
        else:
            raise AssertionError("expected ValueError for " + fragment)


def test_model_and_predict_pipeline():
    records = [
        {"color": "red", "size": 1.0, "y": 10.0},
        {"color": "blue", "size": None, "y": 20.0},
        {"color": None, "size": 3.0, "y": 30.0},
        {"color": "red", "size": 4.0, "y": 40.0},
        {"color": "blue", "size": 5.0, "y": 50.0},
        {"color": "green", "size": 6.0, "y": 60.0},
    ]
    model = a.model_pipeline(
        records, "y", ["color", "size"], None, "tree", "regression",
        {"max_depth": 3},
    )
    assert model["estimator"] == "decision_tree"
    assert model["task"] == "regression"
    assert model["features"] == ["color", "size"]
    assert model["output_features"] == [
        "color=blue", "color=green", "color=red", "size"
    ]
    assert model["n_used"] == 6
    assert model["train_r2"] == 1.0
    assert [entry["feature"] for entry in model["importance"]] == [
        "size", "color=blue", "color=green", "color=red"
    ]
    predicted = a.predict_pipeline(
        model,
        [{"color": "red", "size": 1.0}, {"color": "purple", "size": None}],
    )["predicted"]
    assert predicted == [10.0, 10.0]

    labels = [
        {"c": "a", "x": 0.0, "label": 0},
        {"c": "b", "x": 1.0, "label": 0},
        {"c": "a", "x": 2.0, "label": 1},
        {"c": "b", "x": 3.0, "label": 1},
        {"c": "a", "x": 4.0, "label": 1},
        {"c": "b", "x": 5.0, "label": 1},
    ]
    classifier = a.model_pipeline(
        labels, "label", None, None, "forest", "auto",
        {"n_estimators": 10, "max_depth": 2},
    )
    assert classifier["task"] == "classification"
    assert classifier["classes"] == [0, 1]
    assert classifier["train_accuracy"] == 1.0
    assert a.predict_pipeline(
        classifier, [{"c": "a", "x": 0.0}, {"c": "b", "x": 5.0}]
    )["predicted"] == [0, 1]


def test_model_pipeline_validation():
    records = [{"a": 1.0, "y": 1.0}, {"a": 2.0, "y": 2.0}]
    try:
        a.predict_pipeline({"estimator": "decision_tree"}, records)
    except ValueError as error:
        assert "model_pipeline" in str(error)
    else:
        raise AssertionError("expected ValueError for a plain model")
    try:
        a.model_pipeline([{"a": 1.0}], "y")
    except ValueError as error:
        assert "target" in str(error)
    else:
        raise AssertionError("expected ValueError for data without a target")


def test_namespace_and_record_wrappers():
    src = r'''
let steps = [{"op": "impute", "method": "auto"}, {"op": "encode", "method": "onehot"}, {"op": "scale", "method": "standard"}]
let rows = [{"color": "red", "size": 1.0, "y": 1.5}, {"color": "blue", "size": null, "y": 3.2}, {"color": null, "size": 3.0, "y": 4.1}, {"color": "red", "size": 4.0, "y": 7.3}]
let names = ["color", "size"]
let matrix = [[r["color"], r["size"]] for r in rows]
let fitted = stats.fit_pipeline(steps, matrix, names)
print fitted["n_features"]
print fitted["n"]
print fitted["names"]
print round(fitted["features"][0][0], 3)
print len(fitted["steps"])
print fitted["steps"][0]["missing"]
let again = stats.transform_pipeline(fitted, matrix)
print again["features"] == fitted["features"]

let model = analysis.model_pipeline(rows, "y", ["color", "size"], steps, "tree", "regression")
print model["n_used"]
print model["output_features"]
print model["features"]
print round(model["train_r2"], 3)
print analysis.predict_pipeline(model, [{"color": "blue", "size": 2.0}])["predicted"][0] > 0
'''
    out = []
    execute(src, output=out.append, source_name="pipeline.pea")
    assert out == [
        "3",
        "4",
        '["color=blue", "color=red", "size"]',
        "-0.5",
        "3",
        "2",
        "true",
        "4",
        '["color=blue", "color=red", "size"]',
        '["color", "size"]',
        "1",
        "true",
    ]
