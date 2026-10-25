
import time,pytest
from pealang.registry_index import PackageRecord,build_index,validate_index,NamespacePolicy,RegistryState,RegistryIndex
from pealang.registry_auth import registry_token,bearer_headers

def rec(name='acme/demo',version='1.0.0',sha='a'*64,key='key1',expires=None):return PackageRecord(name,version,sha,'https://r.example/demo.peapkg','https://r.example/demo.sig',key,int(time.time()),expires)
def test_canonical_index(tmp_path):
 x=build_index('main',1,[rec()]);p=tmp_path/'index.json';x.save(p);assert RegistryIndex.load(p).sequence==1 and b' ' not in x.canonical_bytes()
def test_sequence_replay():
 with pytest.raises(Exception):validate_index(build_index('main',2,[rec()]),'main',2)
def test_expired_metadata():
 with pytest.raises(Exception):validate_index(build_index('main',2,[rec(expires=1)]),now=10)
def test_https_required():
 r=rec();r.url='http://bad';
 with pytest.raises(Exception):validate_index(build_index('main',1,[r]))
def test_namespace_authorization():
 p=NamespacePolicy();p.authorize('acme','key1');assert p.check('acme/demo','key1')
def test_namespace_denial():
 with pytest.raises(Exception):NamespacePolicy().check('acme/demo','key1')
def test_state_immutability(tmp_path):
 s=RegistryState(tmp_path/'state.json');s.accept(build_index('main',1,[rec()]));
 with pytest.raises(Exception):s.accept(build_index('main',2,[rec(sha='b'*64)]))
def test_state_advances_sequence(tmp_path):
 s=RegistryState(tmp_path/'state');assert s.accept(build_index('main',1,[rec()]));assert s.data['sequences']['main']==1
def test_token_env():assert registry_token('internal',{'PEALANG_REGISTRY_INTERNAL_TOKEN':'secret'})=='secret'
def test_bearer_header():assert bearer_headers('x',{'PEALANG_REGISTRY_X_TOKEN':'abc'})['Authorization']=='Bearer abc'
def test_missing_token():
 with pytest.raises(Exception):registry_token('x',{})
def test_duplicate_version_index():
 with pytest.raises(Exception):validate_index(build_index('main',1,[rec(),rec()]))

