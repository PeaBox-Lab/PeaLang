from pathlib import Path

import pytest

from pealang import analysis, boosting, persistence, pipeline, trees


def _records():
    return [
        {"region": "north", "spend": 10.0, "churn": 0},
        {"region": "south", "spend": 20.0, "churn": 0},
        {"region": "north", "spend": 30.0, "churn": 1},
        {"region": "south", "spend": 40.0, "churn": 1},
        {"region": "east", "spend": 50.0, "churn": 1},
        {"region": "north", "spend": 60.0, "churn": 1},
    ]


def _probes():
    return [
        {"region": "north", "spend": 12.0},
        {"region": "west", "spend": 55.0},
        {"region": "south", "spend": 35.0},
    ]


def test_tree_export_import_roundtrip():
    model = trees.decision_tree(
        [[1.0], [2.0], [3.0], [4.0]], [1.0, 2.0, 3.0, 4.0], "regression"
    )
    document = persistence.export_model(model)
    assert document["format"] == "pealang.model"
    assert document["version"] == 1
    assert document["kind"] == "model"
    assert document["payload"]["estimator"] == "decision_tree"

    restored = persistence.import_model(document)
    assert restored == model
    assert trees.predict_tree(restored, [[2.0], [3.5]]) == trees.predict_tree(
        model, [[2.0], [3.5]]
    )

    summary = persistence.model_summary(restored)
    assert summary["kind"] == "model"
    assert summary["estimator"] == "decision_tree"
    assert summary["task"] == "regression"
    assert summary["n"] == 4
    assert summary["n_features"] == 1
    assert summary["features"] == []
    assert summary["has_preprocessor"] is False
    assert summary["metrics"] == {}


def test_save_and_load_forest(tmp_path):
    model = analysis.model_pipeline(
        _records(), "churn", ["region", "spend"], None, "forest", "auto",
        {"n_estimators": 8, "max_depth": 3, "seed": 5},
    )
    path = persistence.save_model(str(tmp_path / "forest.json"), model)
    assert Path(path).exists()
    restored = persistence.load_model(path)
    assert analysis.predict_pipeline(restored, _probes()) == analysis.predict_pipeline(
        model, _probes()
    )

    summary = persistence.model_summary(restored)
    assert summary["kind"] == "model"
    assert summary["estimator"] == "random_forest"
    assert summary["task"] == "classification"
    assert summary["features"] == ["region", "spend"]
    assert summary["output_features"] == [
        "region=east", "region=north", "region=south", "spend"
    ]
    assert summary["n_features"] == 2
    assert summary["classes"] == [0, 1]
    assert summary["n"] == 6
    assert summary["has_preprocessor"] is True
    assert summary["top_features"][0]["feature"] == "spend"
    assert 0.0 < summary["metrics"]["train_accuracy"] <= 1.0
    assert "oob_score" in summary["metrics"]

    compact = persistence.save_model(str(tmp_path / "compact.json"), model, 2, True)
    small = persistence.load_model(compact)
    assert "train_predictions" not in small
    assert "oob_predictions" not in small
    assert analysis.predict_pipeline(small, _probes()) == analysis.predict_pipeline(
        model, _probes()
    )
    assert Path(compact).stat().st_size < Path(path).stat().st_size


def test_pipeline_transformer_roundtrip(tmp_path):
    fitted = pipeline.fit_pipeline(
        [
            {"op": "impute", "method": "auto"},
            {"op": "encode", "method": "onehot"},
            {"op": "scale", "method": "standard"},
        ],
        [["red", 1.0], [None, 2.0], ["blue", 3.0]],
        ["color", "x"],
    )
    path = persistence.save_model(str(tmp_path / "pipeline.json"), fitted)
    restored = persistence.load_model(path)
    assert pipeline.transform_pipeline(restored, [["red", 1.0]]) == (
        pipeline.transform_pipeline(fitted, [["red", 1.0]])
    )
    summary = persistence.model_summary(restored)
    assert summary["kind"] == "pipeline"
    assert summary["steps"] == ["impute", "encode", "scale"]
    assert summary["input_names"] == ["color", "x"]
    assert summary["names"] == ["color=blue", "color=red", "x"]
    assert summary["n_features"] == 3
    assert summary["n"] == 3


def test_forest_handles_trees_missing_a_class():
    features = [[1.0], [2.0], [3.0], [4.0], [5.0], [6.0]]
    labels = [0, 0, 0, 0, 0, 1]
    model = trees.random_forest(
        features, labels, "classification", 12, 3, seed=5
    )
    assert any(len(tree["classes"]) == 1 for tree in model["trees"])
    result = trees.predict_forest(model, [[1.0], [6.0]])
    assert result["classes"] == [0, 1]
    assert all(len(row) == 2 for row in result["probabilities"])
    for row in result["probabilities"]:
        assert abs(sum(row) - 1.0) < 1e-9
    assert len(model["oob_predictions"]) == 6

    restored = persistence.import_model(persistence.export_model(model))
    assert trees.predict_forest(restored, [[1.0], [6.0]]) == result


def test_boosting_roundtrip():
    features = [[1.0], [2.0], [3.0], [4.0], [5.0], [6.0]]
    labels = [0, 0, 0, 1, 1, 1]
    model = boosting.gradient_boosting(
        features, labels, "classification", n_estimators=5, max_depth=2, seed=3
    )
    restored = persistence.import_model(persistence.export_model(model))
    assert boosting.predict_boosting(restored, features) == (
        boosting.predict_boosting(model, features)
    )
    summary = persistence.model_summary(restored)
    assert summary["estimator"] == "gradient_boosting"
    assert summary["task"] == "classification"
    assert summary["metrics"] == {}


def test_persistence_validation(tmp_path):
    model = analysis.model_pipeline(
        _records(), "churn", ["region", "spend"], None, "tree", "auto",
        {"max_depth": 3},
    )
    document = persistence.export_model(model)
    cases = [
        (lambda: persistence.export_model([1, 2]), "record"),
        (lambda: persistence.export_model({"a": 1}), "fitted"),
        (lambda: persistence.save_model(str(tmp_path / "x.json"), {"a": 1}), "fitted"),
        (lambda: persistence.export_model(
            {"estimator": "tree", "tree": {"value": float("inf")}}
        ), "non-finite"),
        (lambda: persistence.export_model(
            {"estimator": "tree", "tree": {1: 2}}
        ), "strings"),
        (lambda: persistence.export_model({"estimator": "tree", "tree": object()}),
         "cannot persist"),
        (lambda: persistence.import_model([]), "record"),
        (lambda: persistence.import_model({"format": "other"}), "format"),
        (lambda: persistence.import_model(
            {"format": "pealang.model", "version": 9, "kind": "model",
             "payload": {"estimator": "tree"}}
        ), "version"),
        (lambda: persistence.import_model(
            {"format": "pealang.model", "version": 1, "kind": "pipeline",
             "payload": {"estimator": "tree"}}
        ), "kind"),
        (lambda: persistence.import_model(
            {"format": "pealang.model", "version": 1, "kind": "model"}
        ), "payload"),
        (lambda: persistence.import_model(
            dict(document, payload={"estimator": "tree", "tree": {1: 2}})
        ), "strings"),
        (lambda: persistence.load_model(str(tmp_path / "missing.json")), "cannot read"),
    ]
    for call, fragment in cases:
        with pytest.raises(ValueError, match=fragment):
            call()

    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        persistence.load_model(str(broken))


def test_namespace_end_to_end(tmp_path, monkeypatch):
    from pealang import execute

    monkeypatch.chdir(tmp_path)
    source = r'''
let rows = [
    {"region": "north", "plan": "basic", "spend": 10.0, "churn": 0},
    {"region": "south", "plan": "basic", "spend": 20.0, "churn": 0},
    {"region": "north", "plan": "pro", "spend": 30.0, "churn": 0},
    {"region": "south", "plan": "basic", "spend": 40.0, "churn": 1},
    {"region": "east", "plan": "basic", "spend": 50.0, "churn": 1},
    {"region": "north", "plan": "basic", "spend": 60.0, "churn": 1}
]
let model = analysis.model_pipeline(rows, "churn", ["region", "plan", "spend"], null, "forest", "auto", {"n_estimators": 8, "max_depth": 3, "seed": 5})
stats.save_model("model.json", model)
let loaded = stats.load_model("model.json")
let summary = stats.model_summary(loaded)
print summary["estimator"]
print summary["task"]
print summary["features"]
print summary["has_preprocessor"]
print len(summary["top_features"]) > 0
let probes = [{"region": "north", "plan": "basic", "spend": 12.0}, {"region": "west", "plan": "pro", "spend": 55.0}]
print analysis.predict_pipeline(loaded, probes) == analysis.predict_pipeline(model, probes)
let document = stats.export_model(model, true)
print document["format"]
print document["version"]
print "train_predictions" in document["payload"]
'''
    out = []
    execute(source, output=out.append, source_name="persistence.pea")
    assert out == [
        "random_forest",
        "classification",
        '["region", "plan", "spend"]',
        "true",
        "true",
        "true",
        "pealang.model",
        "1",
        "false",
    ]
    assert (tmp_path / "model.json").exists()
