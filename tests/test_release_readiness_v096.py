from pealang.release_readiness_v096 import *
def h(x): return digest(x)
def test_docs():
 xs=[ReadinessCheck(n,True,"e") for n in ("user-guide","basics","api-docs","upgrade-guide","support-policy","release-notes")]; assert documentation_support_gate(xs)["passed"]
def test_ops():
 xs=[ReadinessCheck(n,True,"e") for n in ("wheel","sdist","container","offline-install","rollback","backup-restore","monitoring")]; assert package_ops_gate(xs)["passed"]
def test_evidence():
 xs=[ReadinessEvidence(n,"ci://1",h(n),True) for n in ("rc95","security","license","cross-platform","reproducibility","operations")]; assert evidence_gate(xs)["passed"]
def test_risk_blocks_high(): assert not residual_risk_gate([ResidualRisk("R","high","m","o")])["passed"]
def test_low_risk_releasable(): assert residual_risk_gate([ResidualRisk("R","low","m","o")])["passed"]
def test_dossier_ready():
 ok={"passed":True}; x=readiness_dossier(evidence=ok,documentation=ok,package_ops=ok,risks=ok,rc95=ok,approvals={"release-owner":True,"security-owner":True,"operations-owner":True}); assert x["decision"]=="READY-FOR-1.0"
def test_dossier_no_go_without_approvals():
 ok={"passed":True}; assert readiness_dossier(evidence=ok,documentation=ok,package_ops=ok,risks=ok,rc95=ok,approvals={})["decision"]=="NO-GO"
