


import pytest
from pealang.rc_readiness import *
def ready():
 r=RCReadiness('0.89.0a1')
 for g in r.REQUIRED:r.add_evidence(g,'PASS',{'g':g})
 return r
def test_go():assert ready().evaluate()['decision']=='GO'
def test_critical_defect():assert ready().add_defect(Defect('BUG',Severity.HIGH,'open')).evaluate()['decision']=='NO-GO'
def test_missing_evidence():
 r=ready();del r.evidence['security'];assert r.evaluate()['decision']=='NO-GO'
def test_waiver():
 r=ready();r.evidence['cross_platform']=Evidence('cross_platform','FAIL');r.add_waiver(Waiver('W','cross_platform','lab outage','manager','0.89.0a1'));assert r.evaluate()['decision']=='GO'
 with pytest.raises(ValueError):RCReadiness('0.89.0a1').add_waiver(Waiver('x','x','','m','0.89.0a1'))
def test_doc_platform():assert documentation_gate({'README.md'},{'README.md'})['status']=='PASS' and cross_platform_gate({'linux':'PASS','windows':'PASS','macos':'PASS'})['status']=='PASS'



