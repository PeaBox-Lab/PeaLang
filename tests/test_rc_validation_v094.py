

from pealang.rc_validation_iv import *

def h(x): return digest(x)

def test_install_matrix_complete():
 ps=[InstallProbe(o,v,"wheel",True,True,True,True) for o in ("windows","linux","macos") for v in ("3.10","3.11","3.12","3.13")]
 assert install_matrix(ps)["passed"]

def test_install_matrix_missing_cell(): assert not install_matrix([])["passed"]

def test_artifact_reproducibility():
 def run(): return [ArtifactBuild(k,h(k),h(k+"s"),h(k+"p")) for k in ("wheel","sdist","container")]
 assert reproducible_artifacts([run(),run()])["passed"]

def test_artifact_drift():
 a=[ArtifactBuild(k,h(k),h(k+"s"),h(k+"p")) for k in ("wheel","sdist","container")]; b=list(a); b[0]=ArtifactBuild("wheel",h("x"),h("wheels"),h("wheelp"))
 assert not reproducible_artifacts([a,b])["passed"]

def test_review_closure(): assert review_gate(ReviewClosure(True,True,True))["passed"]

def test_high_finding_blocks(): assert not review_gate(ReviewClosure(True,True,True,high_findings=1))["passed"]

def test_runbooks():
 xs=[RunbookProbe(n,True,"release-team",10) for n in ("rollback","restore","key-rotation","incident")]
 assert runbook_gate(xs)["passed"]

def test_v1_evidence_gate():
 ok={"passed":True}; x=v1_evidence_gate(install=ok,reproducibility=ok,reviews=ok,runbooks=ok,rc93=ok); assert x["passed"] and len(x["digest"])==64


