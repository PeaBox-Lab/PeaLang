from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def test_date_features_example(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    name = "22_date_features.pea"
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    assert out == [
        "parts: 2024-3-5 weekend=1 day=19791",
        'matrix: ["year", "month", "quarter", "month_sin"]',
        "expanded: 1/4 weekend=0",
        "task: regression",
        "used: 547",
        "outputs: 9",
        "calendar: when=year .. region=east",
        "r2: 0.948",
        "top: when=month",
        "tuned outputs: 7",
        "tuned r2: 0.947",
        "tuned top: when=epoch_day",
        "probes: [351.43, 300.2]",
    ]
