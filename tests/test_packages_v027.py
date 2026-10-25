from pathlib import Path
import json,tarfile
from pealang.package_manager import Version,satisfies,init_manifest,write_lock,audit,build_package,install

def test_semver():assert satisfies('1.4.2','^1.2.0') and not satisfies('2.0.0','^1.2.0') and satisfies('1.2.5','~1.2.0')
def test_init(tmp_path):p=init_manifest(tmp_path,'demo');assert p.exists() and (tmp_path/'src/main.pea').exists()
def setup_dep(tmp_path):
 dep=tmp_path/'dep';init_manifest(dep,'dep');app=tmp_path/'app';init_manifest(app,'app');text=(app/'pea.toml').read_text();text=text.replace('[dependencies]','[dependencies]\ndep = { path = "../dep", version = "^0.1.0" }');(app/'pea.toml').write_text(text);return app,dep
def test_lock_path_dependency(tmp_path):
 app,_=setup_dep(tmp_path);p,lock=write_lock(app);assert p.exists() and lock['dependencies'][0]['name']=='dep' and len(lock['dependencies'][0]['manifest_sha256'])==64
def test_install_path_dependency(tmp_path):
 app,_=setup_dep(tmp_path);write_lock(app);assert install(app)==['dep'] and (app/'.pea_modules/dep/pea.toml').exists()
def test_audit_clean(tmp_path):app,_=setup_dep(tmp_path);write_lock(app);assert audit(app)==[]
def test_audit_checksum_change(tmp_path):
 app,dep=setup_dep(tmp_path);write_lock(app);(dep/'pea.toml').write_text((dep/'pea.toml').read_text()+'\n# changed\n');assert any('checksum changed' in x for x in audit(app))
def test_build_reproducible(tmp_path):
 app,_=setup_dep(tmp_path);write_lock(app);a,ha=build_package(app,tmp_path/'a.peapkg');b,hb=build_package(app,tmp_path/'b.peapkg');assert ha==hb
 with tarfile.open(a) as tf:assert 'pea.toml' in tf.getnames() and 'pea.lock' in tf.getnames()
def test_git_lock_metadata(tmp_path):
 app=tmp_path/'a';init_manifest(app,'a');p=app/'pea.toml';p.write_text(p.read_text().replace('[dependencies]','[dependencies]\nx = { git = "https://example.invalid/x.git", version = "1.0.0", rev = "abc" }'));_,lock=write_lock(app);assert lock['dependencies'][0]['source']=='git'
