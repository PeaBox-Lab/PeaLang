
from pealang.release_rehearsal_v098 import *
def h(x): return digest(x)
def test_signed_staging():
 xs=[RehearsalStep(n,True,h(n),"ci://rehearsal") for n in ("build","sbom","provenance","sign","publish-staging","verify-staging")]; assert signed_staging_gate(xs)["passed"]
def test_staging_missing_fails(): assert not signed_staging_gate([])["passed"]
def test_install_upgrade_rollback():
 d=h("state"); xs=[InstallDrill(n,"linux",True,d,d) for n in ("clean-install","upgrade","rollback")]; assert install_upgrade_rollback_gate(xs)["passed"]
def test_changed_state_fails(): assert not install_upgrade_rollback_gate([InstallDrill("rollback","linux",True,h("a"),h("b"))])["passed"]
def test_operations(): assert operations_gate([OperationalDrill(n,"owner",True,"ticket://1") for n in ("support","incident","rollback")])["passed"]
def test_rehearsal_pass():
 ok={"passed":True}; assert rehearsal_gate(launch97=ok,staging=ok,install=ok,operations=ok,approvals={"release-owner":True,"security-owner":True,"operations-owner":True})["decision"]=="REHEARSAL-PASS"
def test_missing_approval_no_go():
 ok={"passed":True}; assert rehearsal_gate(launch97=ok,staging=ok,install=ok,operations=ok,approvals={})["decision"]=="NO-GO"

