
import io,tarfile,json,pytest
from pealang.ed25519_signing import generate_ed25519_keypair,sign_ed25519,verify_ed25519,PublicTrustStore
from pealang.registry import PackageCache,install_verified
def pkg(tmp_path):
 p=tmp_path/'demo.peapkg'
 with tarfile.open(p,'w:gz') as tf:
  d=b'[project]\nname="demo"\n';i=tarfile.TarInfo('pea.toml');i.size=len(d);tf.addfile(i,io.BytesIO(d))
 return p
def test_ed25519_sign_verify(tmp_path):
 p=pkg(tmp_path);kid,priv,pub=generate_ed25519_keypair(tmp_path/'priv',tmp_path/'pub');sig,e=sign_ed25519(p,priv,publisher='test');assert e.key_id==kid and verify_ed25519(p,sig,pub)
def test_ed25519_tamper(tmp_path):
 p=pkg(tmp_path);_,priv,pub=generate_ed25519_keypair(tmp_path/'priv',tmp_path/'pub');sig,_=sign_ed25519(p,priv);p.write_bytes(p.read_bytes()+b'x')
 with pytest.raises(Exception):verify_ed25519(p,sig,pub)
def test_revoked_key(tmp_path):
 p=pkg(tmp_path);kid,priv,pub=generate_ed25519_keypair(tmp_path/'priv',tmp_path/'pub');sig,_=sign_ed25519(p,priv)
 with pytest.raises(Exception):verify_ed25519(p,sig,pub,[kid])
def test_public_trust_store(tmp_path):
 kid,_,pub=generate_ed25519_keypair(tmp_path/'priv',tmp_path/'pub');s=PublicTrustStore(tmp_path/'trust.json');assert s.trust(pub,'publisher')==kid;s.configure_registry('main','https://packages.example.com',[kid])
def test_revoke_store(tmp_path):
 kid,_,pub=generate_ed25519_keypair(tmp_path/'priv',tmp_path/'pub');s=PublicTrustStore(tmp_path/'t');s.trust(pub);s.revoke(kid,'rotation');assert kid in s.data['revoked']
def test_revoked_registry_key_rejected(tmp_path):
 kid,_,pub=generate_ed25519_keypair(tmp_path/'priv',tmp_path/'pub');s=PublicTrustStore(tmp_path/'t');s.trust(pub);s.revoke(kid)
 with pytest.raises(Exception):s.configure_registry('main','https://x.example',[kid])
def test_verified_install(tmp_path):
 p=pkg(tmp_path);kid,priv,pub=generate_ed25519_keypair(tmp_path/'priv',tmp_path/'pub');sig,_=sign_ed25519(p,priv);dest=tmp_path/'out';r=install_verified(p,sig,pub,dest);assert (dest/'pea.toml').exists() and json.loads(r.read_text())['key_id']==kid
def test_cache(tmp_path):
 c=PackageCache(tmp_path/'cache');p,h=c.put('x.peapkg',b'abc');assert c.find_hash(h)==p
def test_private_public_different(tmp_path):
 _,priv,pub=generate_ed25519_keypair(tmp_path/'private',tmp_path/'public');assert priv.read_text()!=pub.read_text()
def test_https_registry_only(tmp_path):
 _,_,pub=generate_ed25519_keypair(tmp_path/'private',tmp_path/'public');s=PublicTrustStore(tmp_path/'t');kid=s.trust(pub)
 with pytest.raises(Exception):s.configure_registry('bad','http://packages.example',[kid])

