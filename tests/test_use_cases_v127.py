from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def test_target_encoding_example(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    name = "23_target_encoding.pea"
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    assert out == [
        "prior: 202.51",
        "levels: 8",
        "alpha: 150.82",
        "unseen: 202.51",
        "smoothing: 139.33 -> 190.9",
        'outputs: ["store", "region=east", "region=north", "region=south"]',
        "r2: 0.988",
        "top: store",
        "onehot width: 11 r2: 0.917",
        "probes: [127.3, 193.7]",
        "reload: true",
        'binary: ["high", "low"] prior=0.903 (share of low)',
    ]
