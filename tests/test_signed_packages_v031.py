import json,tarfile,io,pytest
from pealang.signing import generate_key,sign_package,verify_package,TrustStore
from pealang.secure_packages import safe_extract,validate_remote_source,dependency_confusion_guard,write_receipt
def package(tmp_path,data=b'hello'):
 p=tmp_path/'x.peapkg'
 with tarfile.open(p,'w:gz') as tf:
  i=tarfile.TarInfo('pea.toml');i.size=len(data);tf.addfile(i,io.BytesIO(data))
 return p
def test_sign_verify(tmp_path):
 p=package(tmp_path);k=tmp_path/'key';generate_key(k);sig,_=sign_package(p,k);assert verify_package(p,sig,k)
def test_tamper_rejected(tmp_path):
 p=package(tmp_path);k=tmp_path/'key';generate_key(k);sig,_=sign_package(p,k);p.write_bytes(p.read_bytes()+b'x')
 with pytest.raises(Exception):verify_package(p,sig,k)
def test_wrong_key_rejected(tmp_path):
 p=package(tmp_path);a=tmp_path/'a';b=tmp_path/'b';generate_key(a);generate_key(b);sig,_=sign_package(p,a)
 with pytest.raises(Exception):verify_package(p,sig,b)
def test_trust_store_https(tmp_path):
 k=tmp_path/'k';generate_key(k);s=TrustStore(tmp_path/'trust.json');kid=s.trust_key(k,'publisher');s.trust_registry('main','https://packages.example.com',[kid]);assert s.data['registries']['main']['keys']==[kid]
def test_http_registry_rejected(tmp_path):
 with pytest.raises(Exception):TrustStore(tmp_path/'t').trust_registry('bad','http://bad.example',[])
def test_safe_extract(tmp_path):
 p=package(tmp_path);d=tmp_path/'out';safe_extract(p,d);assert (d/'pea.toml').exists()
def test_traversal_rejected(tmp_path):
 p=tmp_path/'bad.peapkg'
 with tarfile.open(p,'w:gz') as tf:
  i=tarfile.TarInfo('../evil');i.size=1;tf.addfile(i,io.BytesIO(b'x'))
 with pytest.raises(Exception):safe_extract(p,tmp_path/'out')
def test_https_source():assert validate_remote_source('https://registry.example/x')
def test_dependency_confusion_guard():
 with pytest.raises(Exception):dependency_confusion_guard('x','git','public')
def test_receipt(tmp_path):
 p=package(tmp_path);d=tmp_path/'dest';d.mkdir();r=write_receipt(d,p,key_id='abc');assert json.loads(r.read_text())['key_id']=='abc'
