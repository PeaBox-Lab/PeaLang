import pytest

from pealang import analysis, persistence, pipeline, target_encoding


def test_target_encode_numeric_levels():
    encoder = target_encoding.target_encode(
        ["a", "a", "b", "b", "c"], [2.0, 2.0, 10.0, 10.0, 20.0], 0.0
    )
    assert encoder["method"] == "mean"
    assert encoder["smoothing"] == 0.0
    assert encoder["min_count"] == 1
    assert encoder["kind"] == "numeric"
    assert encoder["classes"] == []
    assert encoder["n"] == 5
    assert encoder["prior"] == pytest.approx(8.8)
    assert encoder["levels"] == [
        {"level": "a", "count": 2, "mean": 2.0, "encoded": 2.0},
        {"level": "b", "count": 2, "mean": 10.0, "encoded": 10.0},
        {"level": "c", "count": 1, "mean": 20.0, "encoded": 20.0},
    ]

    smoothed = target_encoding.target_encode(
        ["a", "a", "b", "b", "c"], [2.0, 2.0, 10.0, 10.0, 20.0], 4.0
    )
    assert smoothed["prior"] == pytest.approx(8.8)
    assert smoothed["levels"][0]["encoded"] == pytest.approx(
        (2 * 2.0 + 4 * 8.8) / 6
    )
    assert smoothed["levels"][2]["encoded"] == pytest.approx(
        (20.0 + 4 * 8.8) / 5
    )

    sparse = target_encoding.target_encode(
        ["a", "a", "b", "b", "b", "c"], [2.0, 2.0, 10.0, 10.0, 10.0, 20.0],
        0.0, 3
    )
    assert sparse["min_count"] == 3
    assert [entry["encoded"] for entry in sparse["levels"]] == [
        pytest.approx(9.0), pytest.approx(10.0), pytest.approx(9.0)
    ]

    ordered = target_encoding.target_encode(
        ["b", "a", "b", None], [1.0, 2.0, 3.0, 4.0], 0.0
    )
    assert [entry["level"] for entry in ordered["levels"]] == [None, "a", "b"]
    assert ordered["levels"][0]["count"] == 1


def test_target_encode_binary_and_apply():
    encoder = target_encoding.target_encode(
        ["a", "a", "b", "b", "b", "c"],
        ["no", "no", "yes", "yes", "no", "yes"],
        0.0,
    )
    assert encoder["kind"] == "binary"
    assert encoder["classes"] == ["no", "yes"]
    assert encoder["prior"] == pytest.approx(0.5)
    assert [entry["mean"] for entry in encoder["levels"]] == [
        pytest.approx(0.0), pytest.approx(2.0 / 3.0), pytest.approx(1.0)
    ]

    encoded = target_encoding.target_apply(encoder, ["a", "c", "z", None])
    assert encoded[:2] == [0.0, 1.0]
    assert encoded[2] == pytest.approx(0.5)
    assert encoded[3] == pytest.approx(0.5)

    numeric = target_encoding.target_encode(
        ["a", "b"], [0.25, 0.75], smoothing=0.0
    )
    assert target_encoding.target_apply(numeric, ["b", "a"]) == [0.75, 0.25]


def test_target_encode_validation():
    values = ["a", "a", "b", "b"]
    target = [1.0, 3.0, 10.0, 14.0]
    for call, fragment in [
        (lambda: target_encoding.target_encode([], target), "required"),
        (lambda: target_encoding.target_encode(None, target), "iterable"),
        (lambda: target_encoding.target_encode("ab", target), "iterable"),
        (lambda: target_encoding.target_encode(values, None), "required"),
        (lambda: target_encoding.target_encode(values, "12"), "iterable"),
        (lambda: target_encoding.target_encode(values, target[:3]), "length"),
        (lambda: target_encoding.target_encode(values, [1.0, None, 3.0, 4.0]),
         "missing value at row 1"),
        (lambda: target_encoding.target_encode(values, target, -1.0),
         "smoothing"),
        (lambda: target_encoding.target_encode(values, target, True),
         "smoothing"),
        (lambda: target_encoding.target_encode(values, target, 1.0, 0),
         "min_count"),
        (lambda: target_encoding.target_encode(values, ["a", "b", "c", "d"]),
         "binary"),
        (lambda: target_encoding.target_apply({}, values), "encoder"),
        (lambda: target_encoding.target_apply(
            target_encoding.target_encode(values, target), []), "required"),
        (lambda: target_encoding.target_apply(
            target_encoding.target_encode(values, target), "ab"), "iterable"),
    ]:
        with pytest.raises(ValueError, match=fragment):
            call()


def test_pipeline_target_step_and_persistence(tmp_path):
    rows = [["a", 1.0], ["a", 3.0], ["b", 10.0], ["b", 14.0],
            ["c", 100.0]]
    names = ["segment", "spend"]
    target = [2.0, 6.0, 20.0, 28.0, 200.0]

    fitted = pipeline.fit_pipeline(
        [{"op": "target", "columns": ["segment"], "smoothing": 0.0}],
        rows,
        names,
        target,
    )
    assert fitted["names"] == names
    assert fitted["input_names"] == names
    assert fitted["features"] == [
        [4.0, 1.0], [4.0, 3.0], [24.0, 10.0], [24.0, 14.0], [200.0, 100.0]
    ]
    step = fitted["steps"][0]
    assert step["op"] == "target"
    assert step["prior"] == pytest.approx(51.2)
    assert step["smoothing"] == 0.0
    assert step["kind"] == "numeric"
    assert step["columns"][0]["encoded"] is True
    assert step["columns"][1] == {
        "name": "spend", "encoded": False, "levels": []
    }
    assert step["columns"][0]["levels"][0] == {
        "level": "a", "count": 2, "mean": 4.0, "encoded": 4.0
    }

    new = pipeline.transform_pipeline(
        fitted, [["a", 9.0], ["z", 8.0]]
    )
    assert new["names"] == names
    assert new["features"] == [[4.0, 9.0], [pytest.approx(51.2), 8.0]]

    path = persistence.save_model(str(tmp_path / "target.json"), fitted)
    restored = persistence.load_model(path)
    assert pipeline.transform_pipeline(restored, [["a", 9.0], ["z", 8.0]]) == new
    summary = persistence.model_summary(restored)
    assert summary["steps"] == ["target"]
    assert summary["names"] == names

    auto = pipeline.fit_pipeline([{"op": "target"}], rows, names, target)
    assert [(entry["name"], entry["encoded"])
            for entry in auto["steps"][0]["columns"]] == [
        ("segment", True), ("spend", False)
    ]
    single = pipeline.fit_pipeline(
        [{"op": "target", "columns": "segment", "smoothing": 0.0}],
        rows,
        names,
        target,
    )
    assert single["features"] == fitted["features"]

    noop = pipeline.fit_pipeline(
        [{"op": "target", "required": False}], [[1.0], [2.0]], ["x"],
        [1.0, 2.0],
    )
    assert noop["features"] == [[1.0], [2.0]]
    assert noop["names"] == ["x"]
    assert noop["steps"][0]["columns"] == [
        {"name": "x", "encoded": False, "levels": []}
    ]


def test_pipeline_target_step_validation():
    rows = [["a", 1.0], ["a", 2.0], ["b", 3.0]]
    names = ["segment", "spend"]
    target = [1.0, 2.0, 3.0]
    for call, fragment in [
        (lambda: pipeline.fit_pipeline([{"op": "target"}], rows, names),
         "requires a target"),
        (lambda: pipeline.fit_pipeline(
            [{"op": "target"}], rows, names, target[:2]), "length"),
        (lambda: pipeline.fit_pipeline(
            [{"op": "target", "columns": ["nope"]}], rows, names, target),
         "unknown target column"),
        (lambda: pipeline.fit_pipeline(
            [{"op": "target"}], [[1.0], [2.0]], ["x"], [1.0, 2.0]),
         "no categorical"),
        (lambda: pipeline.fit_pipeline(
            [{"op": "target", "method": "median"}], rows, names, target),
         "method"),
        (lambda: pipeline.fit_pipeline(
            [{"op": "target", "smoothing": -1.0}], rows, names, target),
         "smoothing"),
        (lambda: pipeline.fit_pipeline(
            [{"op": "target", "min_count": 0}], rows, names, target),
         "min_count"),
    ]:
        with pytest.raises(ValueError, match=fragment):
            call()

    fitted = pipeline.fit_pipeline(
        [{"op": "target", "smoothing": 0.0}], rows, names, target
    )
    with pytest.raises(ValueError, match="number of features"):
        pipeline.transform_pipeline(fitted, [["a"]])


def _store_rows():
    stores = ["s" + str(index) for index in range(9)]
    rows = []
    for k in range(180):
        rows.append({
            "store": stores[k % 9],
            "region": "north" if k % 2 else "south",
            "sales": 50.0 + (k % 9) * 15.0 + (k % 5)
                     + (10.0 if k % 2 else 0.0),
        })
    return rows


def test_model_pipeline_target_step(tmp_path):
    rows = _store_rows()
    steps = [
        {"op": "impute", "method": "auto"},
        {"op": "target", "columns": ["store"], "smoothing": 10.0},
        {"op": "encode", "method": "onehot"},
        {"op": "scale", "method": "standard"},
    ]
    model = analysis.model_pipeline(
        rows, "sales", ["store", "region"], steps, "tree", "regression",
        {"max_depth": 5},
    )
    assert model["output_features"] == [
        "store", "region=north", "region=south"
    ]
    assert model["importance"][0]["feature"] == "store"
    assert model["train_r2"] > 0.95

    probes = [
        {"store": "s0", "region": "north"},
        {"store": "unseen", "region": "south"},
    ]
    expected = analysis.predict_pipeline(model, probes)
    path = persistence.save_model(str(tmp_path / "store.json"), model)
    restored = persistence.load_model(path)
    assert analysis.predict_pipeline(restored, probes) == expected

    plain = analysis.model_pipeline(
        rows, "sales", ["store", "region"], None, "tree", "regression",
        {"max_depth": 5},
    )
    assert len(plain["output_features"]) > len(model["output_features"])


def test_model_pipeline_binary_target_step():
    rows = []
    for k in range(120):
        rows.append({
            "segment": "s" + str(k % 6),
            "y": "yes" if k % 3 == 0 else "no",
        })
    steps = [
        {"op": "target", "columns": ["segment"], "smoothing": 2.0},
        {"op": "scale", "method": "standard"},
    ]
    model = analysis.model_pipeline(
        rows, "y", ["segment"], steps, "tree", "classification",
        {"max_depth": 2},
    )
    step = model["preprocessor"]["steps"][0]
    assert step["kind"] == "binary"
    assert step["classes"] == ["no", "yes"]
    assert model["output_features"] == ["segment"]
    assert set(analysis.predict_pipeline(model, [{"segment": "s0"}])["predicted"]) <= {"no", "yes"}


def test_namespace_end_to_end():
    from pealang import execute

    source = r'''
let encoder = stats.target_encode(["a", "a", "b", "b"], [1.0, 3.0, 10.0, 14.0], 0.0)
print round(encoder["prior"], 2)
print len(encoder["levels"])
print stats.target_apply(encoder, ["a", "z"])
let rows = [["a", 1.0], ["a", 2.0], ["b", 3.0], ["b", 4.0]]
let fitted = stats.fit_pipeline([{"op": "target", "smoothing": 0.0}], rows, ["segment", "spend"], [1.0, 2.0, 30.0, 40.0])
print fitted["names"]
print fitted["features"]
let later = stats.transform_pipeline(fitted, [["z", 5.0]])
print later["features"]
print stats.target_apply(encoder, ["a"])[0] + 0.5
'''
    out = []
    execute(source, output=out.append, source_name="target.pea")
    assert out == [
        "7",
        "2",
        "[2.0, 7.0]",
        '["segment", "spend"]',
        "[[1.5, 1.0], [1.5, 2.0], [35.0, 3.0], [35.0, 4.0]]",
        "[[18.25, 5.0]]",
        "2.5",
    ]
