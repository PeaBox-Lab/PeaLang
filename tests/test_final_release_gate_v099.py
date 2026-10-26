

from pealang.final_release_gate_v099 import *
def h(x): return digest(x)
def test_closure(): assert closure_gate([ClosureItem("B1","defect","high","closed")])["passed"]
def test_open_high_blocks(): assert not closure_gate([ClosureItem("B1","defect","high","open")])["passed"]
def test_invalid_waiver_blocks(): assert not closure_gate([ClosureItem("W1","risk","low","waived")])["passed"]
def test_docs():
 ns=("README","user-guide","basics","api-reference","upgrade-guide","support-policy","security","release-notes","changelog"); assert documentation_gate([FinalDocument(n,True,True,h(n)) for n in ns])["passed"]
def test_artifacts(): assert final_artifact_gate([FinalArtifact(n,"1.0.0",h(n),True,True,True) for n in ("wheel","sdist","container")])["passed"]
def test_wrong_artifact_version_fails(): assert not final_artifact_gate([FinalArtifact("wheel","0.99.0",h("x"),True,True,True)])["passed"]
def test_final_go():
 ok={"passed":True}; r=final_go_no_go(rehearsal98=ok,closure=ok,documentation=ok,artifacts=ok,security=ok,compatibility=ok,operations=ok,approvals={"release-owner":True,"security-owner":True,"operations-owner":True}); assert r["decision"]=="GO-1.0"
def test_missing_approval_no_go():
 ok={"passed":True}; assert final_go_no_go(rehearsal98=ok,closure=ok,documentation=ok,artifacts=ok,security=ok,compatibility=ok,operations=ok,approvals={})["decision"]=="NO-GO"


