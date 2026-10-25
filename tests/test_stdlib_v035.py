
import pytest
from pealang import execute
from pealang.stdlib import MODULES,STDLIB_VERSION,stdlib_manifest,build_standard_library
EXPECTED={'std.collections','std.string','std.math','std.datetime','std.json','std.csv','std.regex','std.file','std.path','std.http','std.crypto','std.logging','std.testing','std.concurrent'}
def test_manifest_complete():assert set(MODULES)==EXPECTED and STDLIB_VERSION=='0.35'
def test_all_stable():assert all(x.stability=='Stable' for x in MODULES.values())
def test_collections():
 s=build_standard_library();assert s['std']['collections']['unique']([1,1,2])==[1,2]
def test_string():assert build_standard_library()['std']['string']['trim'](' x ')=='x'
def test_math():assert build_standard_library()['std']['math']['sqrt'](9)==3
def test_json():assert build_standard_library()['std']['json']['parse']('{"x":1}')['x']==1
def test_regex():assert build_standard_library()['std']['regex']['match']('a+','caa')
def test_crypto():assert len(build_standard_library()['std']['crypto']['sha256']('x'))==64
def test_file_denied(tmp_path):
 with pytest.raises(Exception,match='file.read'):build_standard_library()['std']['file']['read'](tmp_path/'x')
def test_file_allowed(tmp_path):
 s=build_standard_library(permissions={'file.read','file.write'});p=tmp_path/'x';s['std']['file']['write'](p,'ok');assert s['std']['file']['read'](p)=='ok'
def test_http_denied():
 with pytest.raises(Exception,match='http.request'):build_standard_library()['std']['http']['get']('https://example.invalid')
def test_logging_denied():
 with pytest.raises(Exception,match='log'):build_standard_library()['std']['logging']['info']('x')
def test_concurrent_denied():
 with pytest.raises(Exception,match='concurrent'):build_standard_library()['std']['concurrent']['map'](lambda x:x,[1])
def test_pealang_std_namespace():
 out=[];execute('print std.string.upper("pea")',output=out.append);assert out==['PEA']
def test_legacy_json_retained():
 ns=build_standard_library();assert ns['json']['parse']('{"x":1}')['x']==1
def test_manifest_permissions():
 m=stdlib_manifest();assert m['modules']['std.http']['permissions']==['http.request'] and m['modules']['std.file']['permissions']==['file.read','file.write']

