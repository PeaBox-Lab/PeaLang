from pealang.launch_candidate_v097 import *
def h(x): return digest(x)
def test_freeze_ok(): assert freeze_gate([Change("1","blocker-fix",True)])["passed"]
def test_feature_rejected(): assert not freeze_gate([Change("1","feature",True)])["passed"]
def test_artifacts(): assert artifact_gate([Artifact(n,h(n),True,True) for n in ("wheel","sdist","container")])["passed"]
def test_playbooks(): assert playbook_gate([Playbook(n,"owner",True,"e") for n in ("migration","support","incident","rollback")])["passed"]
def test_rollback(): assert rollback_gate([RollbackCriterion("error-rate",2,1)])["passed"]
def test_rollback_breach(): assert not rollback_gate([RollbackCriterion("error-rate",2,3)])["passed"]
def test_launch_pass():
 ok={"passed":True};assert launch_gate(freeze=ok,readiness96=ok,artifacts=ok,playbooks=ok,rollback=ok,approvals={"release-owner":True,"security-owner":True,"operations-owner":True})["passed"]
def test_no_go_without_approval():
 ok={"passed":True};assert not launch_gate(freeze=ok,readiness96=ok,artifacts=ok,playbooks=ok,rollback=ok,approvals={})["passed"]
