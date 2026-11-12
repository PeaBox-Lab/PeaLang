from pealang import execute
from pealang import imbalance as im


def build_imbalanced():
    labels = [0] * 20 + [1] * 5
    rows = [[index / 10.0, ((index * 7) % 5) / 5.0] for index in range(25)]
    return rows, labels


def test_class_balance():
    _, labels = build_imbalanced()
    report = im.class_balance(labels)
    assert report["n"] == 25
    assert report["classes"] == [0, 1]
    assert report["majority"] == 0
    assert report["minority"] == 1
    assert report["imbalance_ratio"] == 4.0
    assert report["counts"][0] == {"class": 0, "count": 20, "share": 0.8}
    assert report["counts"][1]["count"] == 5
    assert abs(report["counts"][1]["share"] - 0.2) < 1e-12


def test_random_oversample():
    rows, labels = build_imbalanced()
    result = im.random_oversample(rows, labels, 1)
    assert result["method"] == "random_oversample"
    assert result["n"] == 40
    assert result["added"] == 15
    assert result["removed"] == 0
    assert result["target"].count(0) == 20
    assert result["target"].count(1) == 20
    assert result["features"][: len(rows)] == rows
    assert result["target"][: len(labels)] == labels
    repeat = im.random_oversample(rows, labels, 1)
    assert result["features"] == repeat["features"]
    assert result["target"] == repeat["target"]


def test_random_undersample():
    rows, labels = build_imbalanced()
    result = im.random_undersample(rows, labels, 1)
    assert result["method"] == "random_undersample"
    assert result["n"] == 10
    assert result["added"] == 0
    assert result["removed"] == 15
    assert result["target"].count(0) == 5
    assert result["target"].count(1) == 5
    assert all(row in rows for row in result["features"])
    repeat = im.random_undersample(rows, labels, 1)
    assert result["features"] == repeat["features"]
    assert result["target"] == repeat["target"]


def test_smote_balances_and_interpolates():
    rows, labels = build_imbalanced()
    result = im.smote(rows, labels, 3, 7)
    assert result["method"] == "smote"
    assert result["n"] == 40
    assert result["added"] == 15
    assert result["target"].count(0) == 20
    assert result["target"].count(1) == 20
    assert result["features"][: len(rows)] == rows
    synthetic = result["features"][len(rows):]
    minority = [rows[index] for index, label in enumerate(labels) if label == 1]
    for row in synthetic:
        assert all(
            min(source[position] for source in minority)
            <= row[position]
            <= max(source[position] for source in minority)
            for position in range(len(row))
        )
        assert row not in minority
    repeat = im.smote(rows, labels, 3, 7)
    assert result["features"] == repeat["features"]
    assert result["target"] == repeat["target"]


def test_smote_multiclass_and_single_row():
    rows = [[index / 10.0, ((index * 7) % 5) / 5.0] for index in range(16)]
    labels = [0] * 10 + [1] * 4 + [2] * 2
    result = im.smote(rows, labels, 2, 3)
    assert result["n"] == 30
    assert [result["target"].count(value) for value in (0, 1, 2)] == [10, 10, 10]

    single = im.smote(rows[:7], [0] * 6 + [1], 5, 1)
    assert single["n"] == 12
    assert single["target"].count(1) == 6
    assert single["features"][-1] == rows[6]


def test_imbalance_validation():
    rows, labels = build_imbalanced()
    cases = [
        (lambda: im.class_balance([]), "target"),
        (lambda: im.smote(rows, labels[:-1]), "lengths"),
        (lambda: im.smote(rows, labels, 0), "k"),
        (lambda: im.random_oversample([], []), "features"),
        (lambda: im.random_undersample(rows, labels[:-1]), "lengths"),
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
let rows = [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 0}, {"x": 3, "y": 0}, {"x": 4, "y": 0}, {"x": 5, "y": 1}]
let balance = stats.class_balance([r["y"] for r in rows])
print balance["n"]
print balance["classes"]
print balance["imbalance_ratio"]
print balance["counts"][0]["count"]
let balanced = analysis.balance_classes(rows, "y", ["x"], "smote", 2, 3)
print balanced["method"]
print balanced["n_used"]
print balanced["n"]
print balanced["added"]
print balanced["before"][1]["count"]
print balanced["after"][1]["count"]
print len(balanced["rows"])
let over = analysis.balance_classes(rows, "y", ["x"], "oversample", 2, 3)
print over["added"]
print over["removed"]
let under = analysis.balance_classes(rows, "y", ["x"], "undersample", 2, 3)
print under["n"]
print under["removed"]
let raw = std.stats.smote([[0.0], [1.0], [2.0], [3.0], [4.0], [5.0]], [0, 0, 0, 0, 0, 1], 2, 3)
print raw["n"]
print raw["added"]
'''
    out = []
    execute(src, output=out.append, source_name="imbalance.pea")
    assert out == [
        "6",
        "[0, 1]",
        "5",
        "5",
        "smote",
        "6",
        "10",
        "4",
        "1",
        "5",
        "10",
        "4",
        "0",
        "2",
        "4",
        "10",
        "4",
    ]
