from pealang.rc_hardening import *
def evidence():return [Evidence.from_payload(x,True,{'ok':True}) for x in RCReadinessGate.REQUIRED]
def test_rc_go_when_all_gates_pass():
 r=RCReadinessGate().evaluate(evidence(),DefectRegistry());assert r['gate']=='GO' and len(r['digest'])==64
def test_blocker_forces_no_go():
 d=Defect('D1',Severity.BLOCKER,'open','blocker');r=RCReadinessGate().evaluate(evidence(),DefectRegistry([d]));assert r['gate']=='NO-GO' and 'D1' in r['critical_defects']
def test_valid_waiver_can_clear_defect_gate():
 w=Waiver('W1','D1','release-owner','temporary','0.90');d=Defect('D1',Severity.HIGH,'open','known',waiver_id='W1');assert RCReadinessGate().evaluate(evidence(),DefectRegistry([d],[w]))['gate']=='GO'
def test_missing_evidence_and_feature_freeze_fail():assert RCReadinessGate().evaluate([],DefectRegistry(),feature_freeze=False)['gate']=='NO-GO'
def test_cross_platform_contract():assert cross_platform_evidence(['Windows','Linux','macOS'])['passed'] and not cross_platform_evidence(['linux'])['passed']
