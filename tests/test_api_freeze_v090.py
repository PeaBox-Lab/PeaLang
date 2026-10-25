
from pealang.api_freeze import *

def test_manifest_digest_and_additive_change():
    baseline=ApiFreezeManifest([FrozenSurface("run","function","(source)")])
    current=ApiFreezeManifest([FrozenSurface("run","function","(source)"),FrozenSurface("version","value","str")])
    diff=current.diff(baseline)
    assert diff["added"]==["version"] and freeze_gate(diff)["gate"]=="PASS" and len(current.digest())==64

def test_breaking_change_requires_approval():
    baseline=ApiFreezeManifest([FrozenSurface("run","function","(x)")])
    current=ApiFreezeManifest([FrozenSurface("run","function","(x,y)")])
    diff=current.diff(baseline)
    assert freeze_gate(diff)["gate"]=="FAIL"
    assert freeze_gate(diff,approved_breaks=["run"])["gate"]=="PASS"

def test_breaking_change_ledger():
    ledger=BreakingChangeLedger(); ledger.approve("run","required compatibility correction","reviewer")
    assert ledger.approved("run")

def test_one_zero_contract():
    manifest=ApiFreezeManifest([FrozenSurface("pea.run","function","(source)")])
    contract=compatibility_contract(manifest,["PEA1001"],"PEAC-1")
    assert contract["target"]=="1.0" and contract["rules"]["breaking_changes"]=="approval-required"

