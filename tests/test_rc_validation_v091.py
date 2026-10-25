


from pealang.rc_validation import *
def complete_matrix():
 return CrossPlatformSoak([SoakEvidence(os_name,py,100) for os_name in SUPPORTED_PLATFORMS for py in SUPPORTED_PYTHONS])
def test_cross_platform_matrix_requires_every_cell():
 assert complete_matrix().evaluate()['passed']
 partial=CrossPlatformSoak([SoakEvidence('linux','3.12',100)]).evaluate();assert not partial['passed'] and partial['missing']
def test_upgrade_validation():
 ok=[UpgradeFixture('0.89','0.91',True,True,True),UpgradeFixture('0.90','0.91',True,True,True)]
 assert UpgradeValidation().evaluate(ok)['passed']
 assert not UpgradeValidation().evaluate([UpgradeFixture('0.90','0.91',True,False,True)])['passed']
def test_frozen_contract_surveillance():
 s=FrozenContractSurveillance('abc',['PEA1001'],'PEAC-1');assert s.compare('abc',['PEA1001'],'PEAC-1')['passed'];assert not s.compare('changed',['PEA1001'],'PEAC-1')['passed']
def test_blocker_and_waiver_gate():
 r=BlockerRegistry();assert r.evaluate([RCBlocker('B1','high','closed')])['passed'];assert not r.evaluate([RCBlocker('B2','critical','open')])['passed'];assert not r.evaluate([RCBlocker('B3','high','waived')])['passed']
def test_rc91_go_no_go():
 cp=complete_matrix().evaluate();up=UpgradeValidation().evaluate([UpgradeFixture('0.90','0.91',True,True,True)]);fc={'passed':True};soak=SoakGate(True,True,True,True);bl=BlockerRegistry().evaluate([])
 result=rc91_gate(cross_platform=cp,upgrades=up,frozen_contract=fc,soak=soak,blockers=bl);assert result['gate']=='GO' and len(evidence_digest(cp,up,fc,soak,bl))==64



