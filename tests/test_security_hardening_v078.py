



import pytest
from pealang.security_hardening import SecurityPolicy,SecurityValidator,SecurityViolation,redact_secrets,SignedAuditChain

def test_text_and_collection_limits():
    v=SecurityValidator(SecurityPolicy(max_text_bytes=3,max_collection_items=2))
    assert v.text('abc')=='abc'; assert v.collection([1,2])==[1,2]
    with pytest.raises(SecurityViolation): v.text('abcd')
    with pytest.raises(SecurityViolation): v.collection([1,2,3])

def test_url_policy_blocks_unsafe_targets():
    v=SecurityValidator()
    assert v.url('https://example.com/a')=='https://example.com/a'
    for url in ('http://example.com','https://127.0.0.1/x','https://localhost/x','file:///tmp/a'):
        with pytest.raises(SecurityViolation): v.url(url)

def test_path_roots(tmp_path):
    root=tmp_path/'safe'; root.mkdir(); v=SecurityValidator(SecurityPolicy(allowed_roots=(str(root),)))
    assert v.path(root/'x').parent==root.resolve()
    with pytest.raises(SecurityViolation): v.path(tmp_path/'outside')

def test_redaction_is_recursive():
    x=redact_secrets({'password':'p','nested':[{'api_key':'k','msg':'Bearer abc.def'}]})
    assert x['password']=='[REDACTED]' and x['nested'][0]['api_key']=='[REDACTED]' and '[REDACTED]' in x['nested'][0]['msg']

def test_signed_audit_chain_detects_tamper():
    c=SignedAuditChain(key=b'test-key'); c.append({'action':'read','token':'secret'}); c.append({'action':'write'})
    assert c.verify() and c.entries[0]['event']['token']=='[REDACTED]'
    c.entries[0]['event']['action']='tampered'; assert not c.verify()




