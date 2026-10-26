


from pealang.rc_validation_iii import *

def h(x): return canonical_digest(x)

def test_extended_soak_gate():
    r=[SoakRun(p,"3.12",180,200) for p in ("windows","linux","macos")]
    assert certify_extended_soak(r)["passed"]

def test_soak_rejects_failure():
    r=[SoakRun("windows","3.12",180,200,failures=1)]
    assert not certify_extended_soak(r)["passed"]

def test_ecosystem_certification():
    xs=[EcosystemCertification(n,"1",True,h(n)) for n in ("fastapi","java","typescript")]
    assert certify_ecosystem(xs)["passed"]

def test_recovery_integrity_and_rto():
    d=h("state"); xs=[RecoveryDrill("registry",d,d,8),RecoveryDrill("orchestration",d,d,12)]
    assert certify_recovery(xs)["passed"]

def test_reproducible_builds():
    b={k:h(k) for k in ("api","diagnostics","bytecode","package")}
    assert verify_reproducibility([b,dict(b)])["passed"]

def test_drift_fails():
    a={k:h(k) for k in ("api","diagnostics","bytecode","package")}; b=dict(a); b["package"]=h("changed")
    assert not verify_reproducibility([a,b])["passed"]

def test_consolidated_gate_digest():
    ok={"passed":True}; r=release_candidate_gate(soak=ok,ecosystem=ok,recovery=ok,reproducibility=ok)
    assert r["passed"] and len(r["evidence_digest"])==64



