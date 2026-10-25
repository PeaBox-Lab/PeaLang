

from pealang.rc_validation_ii import *
def test_evidence_freshness():
 xs=[TimedEvidence('e1','security',100,True,3600)];assert EvidenceFreshness(50).evaluate(xs,now=120)['passed'];assert not EvidenceFreshness(10).evaluate(xs,now=120)['passed']
def test_upgrade_rollback_reupgrade_drill():
 x=UpgradeDrill('0.90','0.92',True,True,True,'abc','abc');assert UpgradeDrillSuite().evaluate([x])['passed']
 bad=UpgradeDrill('0.91','0.92',True,True,True,'a','b');assert not UpgradeDrillSuite().evaluate([bad])['passed']
def test_compatibility_drift():
 rows=[CompatibilityObservation('a','api','diag','PEAC-1'),CompatibilityObservation('b','api','diag','PEAC-1')];assert DriftSurveillance().evaluate(rows)['passed']
 assert not DriftSurveillance().evaluate(rows+[CompatibilityObservation('c','changed','diag','PEAC-1')])['passed']
def test_trends_ecosystem_recovery_and_waivers():
 assert SoakTrendGate().evaluate([TrendPoint('a',0,1,100),TrendPoint('b',0,2,105)])['passed']
 assert EcosystemGate().evaluate([EcosystemCertification('postgresql','16',True)])['passed']
 assert RecoveryGate().evaluate([RecoveryDrill('db-loss',True,True,True,True)])['passed']
 assert WaiverLifecycle().evaluate([Waiver('w1','i1',200,'owner','temporary')],now=100)['passed']
def test_rc92_gate_and_digest():
 ok={'passed':True};r=rc92_gate(freshness=ok,upgrades=ok,drift=ok,trends=ok,ecosystem=ok,recovery=ok,waivers=ok);assert r['gate']=='GO' and len(certification_digest(r))==64


