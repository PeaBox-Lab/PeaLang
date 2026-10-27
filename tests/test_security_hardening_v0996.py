import json, time
from pathlib import Path
import pytest
from pealang.cloud_connectors import SFTPConfig
from pealang.signing import generate_key, TrustStore
from pealang.type_system import TypeChecker, parse_type

def test_sftp_config_has_no_unknown_host_escape_hatch():
    assert not hasattr(SFTPConfig('example.com'), 'allow_unknown_host')

def test_legacy_trust_store_does_not_persist_secret(tmp_path):
    key=tmp_path/'key'; generate_key(key); secret=key.read_text().strip()
    store=TrustStore(tmp_path/'trust.json'); kid=store.trust_key(key,'publisher')
    payload=(tmp_path/'trust.json').read_text()
    assert secret not in payload
    assert store.data['keys'][kid]['key_id']==kid
    assert 'key' not in store.data['keys'][kid]

def test_type_expression_input_limit():
    with pytest.raises(ValueError): parse_type('A'*65537)

def test_typecheck_source_input_limit():
    with pytest.raises(ValueError): TypeChecker().check('x'*2_000_001)

def test_pathological_type_input_completes_quickly():
    text='function f('+('x:Int,'*10000)+'x:Int) -> Int {'
    started=time.monotonic(); TypeChecker().check(text)
    assert time.monotonic()-started < 2.0
