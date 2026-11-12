from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def run_example(name, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    return out


def test_statistical_analysis(tmp_path, monkeypatch):
    out = run_example("06_statistical_analysis.pea", tmp_path, monkeypatch)
    assert out == [
        "mean: 82.125",
        "median: 82.5",
        "std: 9.45",
        "iqr: 11.5",
        "t: 3.34",
        "p: 0.0049",
        "significant: true",
        "skew: -0.34",
        "ci: 76.12 .. 88.25",
    ]


def test_matrix_regression(tmp_path, monkeypatch):
    out = run_example("07_matrix_regression.pea", tmp_path, monkeypatch)
    assert out == [
        "slope: 1.99",
        "intercept: 0.05",
        "r2: 0.9973",
        "multi intercept: 0.213",
        "slopes: 2",
        "multi r2: 0.9799",
        "det: 5",
        "inverse00: 0.4",
        "solved: 2, 3",
    ]


def test_segmentation_clustering(tmp_path, monkeypatch):
    out = run_example("08_segmentation_clustering.pea", tmp_path, monkeypatch)
    assert out == [
        "clusters: 2",
        "labels: 6",
        "inertia positive: true",
        "centers: 2",
        "components: 2",
        "explained: 0.999",
        "projected rows: 6",
    ]
