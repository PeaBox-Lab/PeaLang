
import types,pytest
from pealang.compatibility import *
def test_deprecation_ledger():
 l=DeprecationLedger();l.add(Deprecation("old.api","0.81","0.90","new.api","consistent contract"))
 assert not l.validate_release("0.89") and "old.api" in l.validate_release("0.90")[0]
 with pytest.raises(ValueError):l.add(Deprecation("bad","0.90","0.81","new","bad"))
def test_migration_upgrade_downgrade_and_resume():
 r=MigrationRegistry();r.register(Migration("cfg-1","1.0","1.1",lambda d:{**d,"mode":"safe"},lambda d:{k:v for k,v in d.items() if k!="mode"}))
 up=r.migrate({"name":"demo"},"1.0","1.1");assert up.document["mode"]=="safe" and len(up.events)==1
 assert r.migrate(up.document,"1.1","1.0").document=={"name":"demo"}
 assert not r.migrate({"mode":"safe"},"1.0","1.1",applied=["up:cfg-1"]).events
def test_missing_migration_path():
 with pytest.raises(LookupError):MigrationRegistry().plan("1.0","1.2")
def test_api_snapshot_and_gate():
 old=PublicApiSnapshot([ApiSymbol("run","function","(x)")]);new=PublicApiSnapshot([ApiSymbol("run","function","(x, y=1)"),ApiSymbol("stop","function","()")]);diff=new.diff(old)
 assert diff.breaking and diff.added==("stop",) and CompatibilityGate().evaluate(diff)==["unapproved changed API: run"]
 assert not CompatibilityGate().evaluate(diff,["run"])
def test_capture_public_api():
 m=types.ModuleType("demo");m.__all__=["run"];m.run=lambda x:x
 assert PublicApiSnapshot.capture(m).symbols["run"].signature=="(x)"

