import io,tarfile,pytest
from pealang import RuntimeOptions,VMRuntime,PeaRuntime
from pealang.browser_profile import validate_browser_permissions
from pealang.secure_packages import safe_extract,validate_remote_source
from pealang.stdlib import build_standard_library
def test_process_denied_default():assert not RuntimeOptions().allow_process
def test_vm_host_permission_denied():
 r=VMRuntime().register_function('secret.get',lambda:1,'secret.get')
 with pytest.raises(Exception):r.load('function f(){return secret.get()}\nexport f').call('f')
def test_interpreter_host_permission_denied():
 r=PeaRuntime().register_function('secret.get',lambda:1,'secret.get')
 with pytest.raises(Exception):r.load('function f(){return secret.get()}\nexport f').call('f')
def test_http_permission_denied():
 with pytest.raises(Exception):build_standard_library()['std']['http']['get']('https://example.invalid')
def test_file_permission_denied(tmp_path):
 with pytest.raises(Exception):build_standard_library()['std']['file']['read'](tmp_path/'x')
def test_browser_process_denied():
 with pytest.raises(Exception):validate_browser_permissions(['process'])
def test_remote_http_denied():
 with pytest.raises(Exception):validate_remote_source('http://example.invalid/x')
def test_archive_traversal_denied(tmp_path):
 p=tmp_path/'bad.tgz'
 with tarfile.open(p,'w:gz') as tf:
  i=tarfile.TarInfo('../evil');i.size=1;tf.addfile(i,io.BytesIO(b'x'))
 with pytest.raises(Exception):safe_extract(p,tmp_path/'out')

