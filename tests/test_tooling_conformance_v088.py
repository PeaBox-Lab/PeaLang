import pytest
from pealang.tooling_conformance import *
def test_diagnostics_are_stable():
 r=DiagnosticRegistry().register(DiagnosticContract('PEA1001',Severity.ERROR,'Unexpected token'))
 assert r.validate('PEA1001','error','Unexpected token x') and r.snapshot()['PEA1001']['severity']=='error'
 with pytest.raises(ValueError):r.register(DiagnosticContract('PEA1001',Severity.ERROR,'duplicate'))
def test_lsp_dap_profiles_and_negotiation():
 l=LSPConformance().certify(LSPConformance.REQUIRED);d=DAPConformance().certify(DAPConformance.REQUIRED);assert l['passed'] and d['passed']
 assert EditorCapabilityNegotiator().negotiate({'hover','completion'},{'hover'})==frozenset({'hover'})
def test_debug_session_reproducible():
 b=BreakpointFixture('app.pea',10);a=ReproducibleDebugSession([b]);c=ReproducibleDebugSession([b])
 for s in (a,c):s.record('breakpoint','app.pea',10,'main',{'x':1},('main',))
 assert a.breakpoint_hit('app.pea',10) and a.fingerprint()==c.fingerprint()
def test_tooling_gate_fail_and_pass():
 ok={'passed':True};bad={'passed':False};assert tooling_certification_gate(lsp=ok,dap=ok,diagnostics_stable=True,debug_reproducible=True)['gate']=='PASS'
 assert tooling_certification_gate(lsp=bad,dap=ok,diagnostics_stable=True,debug_reproducible=True)['gate']=='FAIL'
def test_compatibility_matrix():
 m=CompatibilityMatrix().register(ToolProtocolProfile('vscode','lsp','3.17',frozenset({'hover','completion'})));assert m.supports('vscode','lsp',{'hover'}) and not m.supports('vscode','lsp',{'rename'})
