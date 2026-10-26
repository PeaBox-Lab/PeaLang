from pealang.pre_v1_evidence_v0992 import *
def h(x): return digest(x)
def test_inventory_requires_all(): assert not evidence_inventory([])["passed"]
def test_inventory_complete():
 xs=[Evidence(n,"ci://run/1",h(n),True) for n in REQUIRED]; r=evidence_inventory(xs); assert r["passed"] and r["verified"]==len(REQUIRED)
def test_invalid_evidence_fails(): assert not evidence_inventory([Evidence(REQUIRED[0],"",h("x"),True)])["passed"]
def test_pre_v1_no_go_without_real_evidence():
 ok={"passed":True}; no={"passed":False}; assert pre_v1_gate(audit_closure=ok,final_gate=ok,evidence=no,approvals={})["decision"]=="NO-GO"
def test_pre_v1_ready_when_everything_passes():
 ok={"passed":True}; a={"release-owner":True,"security-owner":True,"operations-owner":True}; assert pre_v1_gate(audit_closure=ok,final_gate=ok,evidence=ok,approvals=a)["decision"]=="READY-FOR-1.0"
def test_template_is_fail_closed(tmp_path): assert local_evidence_template(tmp_path)["policy"]=="fail-closed"
