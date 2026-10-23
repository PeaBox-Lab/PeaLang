import json,zipfile
from pealang.supply_chain import *
def test_checksums(tmp_path):
 p=tmp_path/'a';p.write_text('x');assert len(sha256_file(p))==64 and write_checksums([p],tmp_path/'SHA256SUMS')
def test_sbom(tmp_path):
 (tmp_path/'pyproject.toml').write_text('[project]\n');(tmp_path/'a.py').write_text('x=1');s=generate_sbom(tmp_path);assert s['bomFormat']=='CycloneDX' and len(s['components'])==3
def test_inventory(tmp_path):
 (tmp_path/'pyproject.toml').write_text('dependencies = [\n  "fastapi>=1",\n]\n');assert dependency_inventory(tmp_path)[0]['name']=='fastapi'
def test_provenance(tmp_path):
 p=tmp_path/'a';p.write_text('x');assert build_provenance(tmp_path,[p])['subject'][0]['digest']['sha256']==sha256_file(p)
def test_verify_wheel(tmp_path):
 p=tmp_path/'x.whl'
 with zipfile.ZipFile(p,'w') as z:z.writestr('pealang/__init__.py','');z.writestr('pealang-0.62.0.dist-info/METADATA','Version: 0.62.0\n')
 assert verify_wheel(p)['valid']
def test_verify_source(tmp_path):
 p=tmp_path/'x.zip'
 with zipfile.ZipFile(p,'w') as z:z.writestr('PeaLang/pyproject.toml','');z.writestr('PeaLang/README.md','')
 assert verify_source_archive(p)['valid']
def test_migration(tmp_path):
 a=tmp_path/'a';b=tmp_path/'b';a.mkdir();b.mkdir();assert migration_check(a,b)['compatible']
def test_checklist_readiness():assert len(release_checklist())>=10 and readiness_assessment({'a':True,'b':False})['score']==50
def test_container_ci():assert 'USER 10001:10001' in containerfile() and len(ci_matrix()['os'])==3
