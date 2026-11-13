import math
from datetime import date, datetime, timedelta

import pytest

from pealang import analysis, dates, persistence, pipeline


def test_parse_date_formats_and_errors():
    expected = date(2024, 3, 9)
    for value in [
        "2024-03-09",
        "2024/03/09",
        "2024.03.09",
        "20240309",
        "2024-03-09T12:30:00",
        "2024-03-09 12:30:00",
        " 2024-03-09 ",
    ]:
        assert dates.parse_date(value) == expected
    assert dates.parse_date(date(2024, 3, 9)) == expected
    assert dates.parse_date(datetime(2024, 3, 9, 5)) == expected

    for value in ["", "not a date", "2023-02-29", "2024-13-01", None, 20240309,
                  True]:
        with pytest.raises(ValueError, match="cannot parse date"):
            dates.parse_date(value)

    assert dates.is_date("2024-02-29") is True
    assert dates.is_date("2023-02-29") is False
    assert dates.is_date(None) is False


def test_date_parts_all():
    parts = dates.date_parts("2024-03-09", list(dates.PART_NAMES))
    assert parts["year"] == 2024
    assert parts["month"] == 3
    assert parts["day"] == 9
    assert parts["weekday"] == 5
    assert parts["quarter"] == 1
    assert parts["day_of_year"] == 69
    assert parts["week"] == 10
    assert parts["is_weekend"] == 1
    assert parts["is_month_start"] == 0
    assert parts["is_month_end"] == 0
    assert parts["epoch_day"] == 19791
    assert parts["month_sin"] == pytest.approx(math.sin(2 * math.pi * 2 / 12))
    assert parts["month_cos"] == pytest.approx(math.cos(2 * math.pi * 2 / 12))
    assert parts["weekday_sin"] == pytest.approx(math.sin(2 * math.pi * 5 / 7))
    assert parts["weekday_cos"] == pytest.approx(math.cos(2 * math.pi * 5 / 7))

    assert dates.date_parts("2024-03-09") == {
        "year": 2024,
        "month": 3,
        "day": 9,
        "weekday": 5,
        "quarter": 1,
        "is_weekend": 1,
    }
    assert dates.date_parts("2024-01-01", ["is_month_start"]) == {
        "is_month_start": 1
    }
    assert dates.date_parts("2024-02-29", ["is_month_end"]) == {
        "is_month_end": 1
    }


def test_calendar_features_matrix():
    result = dates.calendar_features(
        ["2024-01-01", "2024-03-09", "2024-12-31"],
        ["year", "month", "weekday"],
    )
    assert result == {
        "features": [[2024, 1, 0], [2024, 3, 5], [2024, 12, 1]],
        "names": ["year", "month", "weekday"],
        "parts": ["year", "month", "weekday"],
        "n": 3,
    }
    prefixed = dates.calendar_features(["2024-01-01"], ["month", "month"], "sale")
    assert prefixed["parts"] == ["month"]
    assert prefixed["names"] == ["sale_month"]
    assert prefixed["features"] == [[1]]

    assert dates.calendar_features(["2024-01-01"])["names"] == [
        "year", "month", "day", "weekday", "quarter", "is_weekend"
    ]

    for call, fragment in [
        (lambda: dates.calendar_features([]), "required"),
        (lambda: dates.calendar_features(None), "required"),
        (lambda: dates.calendar_features("2024-01-01"), "iterable"),
        (lambda: dates.calendar_features(["2024-01-01"], ["century"]), "part"),
        (lambda: dates.calendar_features(["2024-01-01"], []), "empty"),
        (lambda: dates.calendar_features(["2024-01-01", "bad"]), "row 1"),
        (lambda: dates.calendar_features(["2024-01-01"], "month", ""), "prefix"),
    ]:
        with pytest.raises(ValueError, match=fragment):
            call()


def test_analysis_date_features():
    records = [
        {"order": "2024-01-05", "amount": 10.0},
        {"order": "2024-12-31", "amount": 20.0},
    ]
    expanded = analysis.date_features(records, "order")
    assert expanded[0]["order_year"] == 2024
    assert expanded[0]["order_month"] == 1
    assert expanded[0]["order_day"] == 5
    assert expanded[0]["order_weekday"] == 4
    assert expanded[0]["order_quarter"] == 1
    assert expanded[0]["order_is_weekend"] == 0
    assert expanded[0]["order"] == "2024-01-05"
    assert expanded[0]["amount"] == 10.0

    custom = analysis.date_features(
        records, "order", ["month", "quarter"], "sale", True
    )
    assert set(custom[0]) == {"amount", "sale_month", "sale_quarter"}
    assert custom[1]["sale_month"] == 12
    assert custom[1]["sale_quarter"] == 4

    for call, fragment in [
        (lambda: analysis.date_features([], "order"), "required"),
        (lambda: analysis.date_features(records, "missing"), "unknown column"),
        (lambda: analysis.date_features(records, "order", []), "empty"),
        (lambda: analysis.date_features([{"order": None}], "order"), "row 0"),
        (lambda: analysis.date_features(records, "order", ["month"], ""), "prefix"),
    ]:
        with pytest.raises(ValueError, match=fragment):
            call()


def test_pipeline_date_step_and_persistence(tmp_path):
    rows = [
        ["2024-01-05", "north", 1.0],
        ["2024-03-09", "south", 2.0],
        ["2024-12-31", "north", 3.0],
    ]
    names = ["when", "region", "spend"]
    fitted = pipeline.fit_pipeline(
        [{"op": "date", "parts": ["year", "month", "weekday"]}], rows, names
    )
    assert fitted["names"] == [
        "when=year", "when=month", "when=weekday", "region", "spend"
    ]
    assert fitted["features"] == [
        [2024, 1, 4, "north", 1.0],
        [2024, 3, 5, "south", 2.0],
        [2024, 12, 1, "north", 3.0],
    ]
    assert fitted["steps"][0]["op"] == "date"
    assert fitted["steps"][0]["columns"] == [
        {"name": "when", "date": True, "parts": ["year", "month", "weekday"]},
        {"name": "region", "date": False, "parts": []},
        {"name": "spend", "date": False, "parts": []},
    ]

    new = pipeline.transform_pipeline(fitted, [["2025-07-04", "west", 9.0]])
    assert new["features"] == [[2025, 7, 4, "west", 9.0]]

    path = persistence.save_model(str(tmp_path / "dates.json"), fitted)
    restored = persistence.load_model(path)
    assert pipeline.transform_pipeline(restored, [["2025-07-04", "west", 9.0]]) == new
    summary = persistence.model_summary(restored)
    assert summary["steps"] == ["date"]
    assert summary["names"] == fitted["names"]

    full = pipeline.fit_pipeline(
        [
            {"op": "impute", "method": "auto"},
            {"op": "date", "parts": ["year", "month"]},
            {"op": "encode", "method": "onehot"},
            {"op": "scale", "method": "standard"},
        ],
        [["2024-01-05", "north", 1.0], [None, "south", 2.0],
         ["2024-12-31", "north", 3.0]],
        names,
    )
    assert full["names"] == [
        "when=year", "when=month", "region=north", "region=south", "spend"
    ]
    assert all(
        isinstance(value, (int, float))
        for row in full["features"] for value in row
    )


def test_pipeline_date_step_validation():
    dates_only = [["2024-01-05"], [None]]
    with pytest.raises(ValueError, match="complete dates"):
        pipeline.fit_pipeline([{"op": "date"}], dates_only, ["when"])
    with pytest.raises(ValueError, match="no date columns"):
        pipeline.fit_pipeline([{"op": "date"}], [[1.0], [2.0]], ["x"])

    noop = pipeline.fit_pipeline(
        [{"op": "date", "required": False}], [[1.0], [2.0]], ["x"]
    )
    assert noop["names"] == ["x"]
    assert noop["features"] == [[1.0], [2.0]]
    assert noop["steps"][0]["columns"] == [
        {"name": "x", "date": False, "parts": []}
    ]

    with pytest.raises(ValueError, match="part"):
        pipeline.fit_pipeline(
            [{"op": "date", "parts": ["year", "century"]}],
            [["2024-01-05"]],
            ["when"],
        )

    fitted = pipeline.fit_pipeline(
        [{"op": "date", "parts": ["year"]}], [["2024-01-05"]], ["when"]
    )
    with pytest.raises(ValueError, match="complete dates"):
        pipeline.transform_pipeline(fitted, [[None]])
    with pytest.raises(ValueError, match="cannot parse date"):
        pipeline.transform_pipeline(fitted, [["not a date"]])
    with pytest.raises(ValueError, match="number of features"):
        pipeline.transform_pipeline(fitted, [["2024-01-05", "extra"]])


def _sales_rows():
    rows = []
    start = date(2024, 1, 1)
    for k in range(120):
        current = start + timedelta(days=k)
        stamp = current.isoformat()
        region = "north" if k % 2 == 0 else "south"
        sales = 100.0 + current.month * 6 + current.weekday() * 2
        if k % 17 == 5:
            stamp = None
        rows.append({"when": stamp, "region": region, "sales": sales})
    return rows


def test_default_model_pipeline_expands_dates(tmp_path):
    rows = _sales_rows()
    model = analysis.model_pipeline(
        rows, "sales", ["when", "region"], None, "tree", "regression",
        {"max_depth": 4},
    )
    assert model["features"] == ["when", "region"]
    assert "when=month" in model["output_features"]
    assert "when=weekday" in model["output_features"]
    assert "region=north" in model["output_features"]
    assert model["n_used"] == 120
    assert model["train_r2"] > 0.8

    probes = [
        {"when": "2025-07-04", "region": "north"},
        {"when": None, "region": "west"},
    ]
    expected = analysis.predict_pipeline(model, probes)
    path = persistence.save_model(str(tmp_path / "sales.json"), model)
    restored = persistence.load_model(path)
    assert analysis.predict_pipeline(restored, probes) == expected


def test_namespace_end_to_end():
    from pealang import execute

    source = r'''
print stats.is_date("2024-02-29")
print stats.date_parts("2024-03-09", ["weekday", "epoch_day"])["weekday"]
let matrix = stats.calendar_features(["2024-01-05", "2024-02-10"], ["year", "month", "is_weekend"])
print matrix["names"]
print matrix["features"]
let rows = [{"when": "2024-01-05", "region": "north", "spend": 10.0}, {"when": "2024-02-10", "region": "south", "spend": 20.0}]
let expanded = analysis.date_features(rows, "when", ["year", "is_weekend"])
print expanded[0]["when_year"]
print expanded[0]["when_is_weekend"]
print len(expanded[0])
let steps = [{"op": "date", "parts": ["year", "month"]}]
let fitted = stats.fit_pipeline(steps, [["2024-01-05"], ["2024-02-10"]], ["when"])
print fitted["names"]
print fitted["steps"][0]["op"]
let later = stats.transform_pipeline(fitted, [["2025-07-04"]])
print later["features"]
'''
    out = []
    execute(source, output=out.append, source_name="dates.pea")
    assert out == [
        "true",
        "5",
        '["year", "month", "is_weekend"]',
        "[[2024, 1, 0], [2024, 2, 1]]",
        "2024",
        "0",
        "5",
        '["when=year", "when=month"]',
        "date",
        "[[2025, 7]]",
    ]
