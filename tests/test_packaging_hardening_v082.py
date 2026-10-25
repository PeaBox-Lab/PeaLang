
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pealang.supply_chain import *
def test_deterministic_manifest_and_tamper_detection(tmp_path):
 (tmp_path/'a.txt').write_text('a');m=deterministic_manifest(tmp_path);assert verify_manifest(tmp_path,m)['valid']
 (tmp_path/'a.txt').write_text('b');r=verify_manifest(tmp_path,m);assert not r['valid'] and r['changed']==['a.txt']
def test_sbom_and_provenance_verification(tmp_path):
 p=tmp_path/'a';p.write_text('x');sbom=generate_sbom(tmp_path,'0.82.0a1');assert verify_sbom(sbom,tmp_path)['valid']
 prov=build_provenance(tmp_path,[p],'0.82.0a1');assert verify_provenance(prov,[p])['valid']
def test_signed_manifest():
 key=Ed25519PrivateKey.generate();raw=key.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption());pub=key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw);m={'version':'0.82.0a1','digest':'abc'};sig=sign_release_manifest(m,raw);assert verify_release_signature(m,sig,pub);assert not verify_release_signature({**m,'digest':'tampered'},sig,pub)
def test_locked_dependency_and_offline_evidence(tmp_path):
 (tmp_path/'requirements.lock').write_text('cryptography==42.0.0\n');assert locked_dependency_evidence(tmp_path)['locked']
 wh=tmp_path/'wheelhouse';wh.mkdir();(wh/'cryptography-42.0.0-py3-none-any.whl').write_bytes(b'x');assert offline_install_evidence(wh,['cryptography==42.0.0'])['ready'];assert not offline_install_evidence(wh,['missing==1'])['ready']
def test_quality_gate():
 ok={'valid':True};gate=packaging_quality_gate(ok,ok,ok,True,{'ready':True},{'files':[1]});assert gate['gate']=='PASS'
 assert packaging_quality_gate(ok,ok,ok,False,{'ready':True},{'files':[1]})['gate']=='FAIL'

