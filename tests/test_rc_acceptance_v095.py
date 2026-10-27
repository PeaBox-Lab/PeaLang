from pealang.rc_acceptance_v095 import *

def h(x): return digest(x)

def test_real_evidence_contract():
 xs=[EvidenceItem(n,"ci://run/1",h(n),True) for n in ("install-matrix","security-review","license-review","runbooks","reproducibility")]; assert evidence_ingestion(xs)["passed"]

def test_evidence_missing_is_no_go(): assert not evidence_ingestion([])["passed"]

def test_blockers_closed(): assert blocker_burndown([Blocker("B1","high","closed")])["passed"]

def test_open_high_blocks(): assert not blocker_burndown([Blocker("B1","high","open")])["passed"]

def test_signed_artifacts():
 xs=[SignedArtifact(n,h(n),True,True) for n in ("wheel","sdist","container")]; assert artifact_signing(xs)["passed"]

def test_release_dry_run():
 xs=[DryRunStep(n,True,n=="rollback") for n in ("build","test","sign","publish-staging","install-staging","rollback")]; assert release_dry_run(xs)["passed"]

def test_go_decision_requires_manual_approval():
 ok={"passed":True}; r=go_no_go(evidence=ok,blockers=ok,artifacts=ok,dry_run=ok,rc94=ok,manual_approvals={"release-owner":True,"security-owner":True}); assert r["decision"]=="GO"

def test_no_go_without_approval():
 ok={"passed":True}; r=go_no_go(evidence=ok,blockers=ok,artifacts=ok,dry_run=ok,rc94=ok,manual_approvals={}); assert r["decision"]=="NO-GO"
