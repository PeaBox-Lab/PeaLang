from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def run_example(name, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    return out


def test_causal_inference_example(tmp_path, monkeypatch):
    out = run_example("13_causal_inference.pea", tmp_path, monkeypatch)
    assert out == [
        "ipw ate: 1.542",
        "ipw ci: 1.36 to 1.724",
        "ipw max smd: 0.372",
        "ipw adjusted smd: 0.01",
        "aipw ate: 1.556",
        "aipw ci: 1.39 to 1.722",
        "matching att: 1.507",
        "matched: 24 of 30",
        "did att: 4",
        "did ci: 3.809 to 4.191",
        "iv effect: 1.995",
        "first-stage F: 946.7",
        "rdd jump: 0.984",
        "rdd ci: 0.921 to 1.046",
    ]
