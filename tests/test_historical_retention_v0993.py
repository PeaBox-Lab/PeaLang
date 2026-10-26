
import json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_ledger():
 d=json.loads((ROOT/"docs/project/HISTORICAL_CAPABILITY_LEDGER.json").read_text());assert all(x["disposition"] in {"RETAINED","RESTORED","SUPERSEDED","INTENTIONALLY_RETIRED"} for x in d["capabilities"])
def test_fixtures():
 assert all((ROOT/x).is_file() for x in ("pea_tests/smoke.pea","pea_tests/smoke.out","pea_tests/assertions.pea","pea_tests/assertions.out"))
def test_examples(): assert len(list((ROOT/"examples/historical").glob("*.pea")))>=19
def test_policy(): assert "pealang/**" in json.loads((ROOT/"release/retention_policy.json").read_text())["protected"]
def test_root_normalization(tmp_path):
 a=tmp_path/"a.zip";b=tmp_path/"b.zip"
 with zipfile.ZipFile(a,"w") as z:z.writestr("PeaLang_v0.1.0/docs/X.md","same")
 with zipfile.ZipFile(b,"w") as z:z.writestr("PeaLang_v0.2.0/docs/X.md","same")
 sys.path.insert(0,str(ROOT/"tools"));from retention_audit import compare
 r=compare(a,b);assert r["unchanged"]==["docs/X.md"] and r["passed"]

