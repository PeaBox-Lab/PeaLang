import pytest
from pealang.mlops_secure import *
from types import SimpleNamespace
def test_store(tmp_path):
 s=MonitoringStore(tmp_path/'e.json');s.record('m','drift',.2);s.record('m','drift',.4);assert s.summary('m','drift')['mean']==pytest.approx(.3)
def test_alert():
 e=MonitoringEvent('1','m','drift',.3);a=evaluate_alerts('m',[e],[AlertRule('drift',.2,severity='critical')])[0];assert should_rollback([a]);acknowledge(a,'raj');assert not should_rollback([a])
def test_policy():
 entry=SimpleNamespace(stage='approved');assert can_promote(entry,['a'],{'drift':.1},PromotionPolicy(max_drift=.2))['allowed']
def test_policy_blocks():
 entry=SimpleNamespace(stage='draft');assert not can_promote(entry,[],{'drift':.3},PromotionPolicy(max_drift=.2))['allowed']
def test_routing():
 p=DeploymentPlan('m','1','2',100,'1');assert route_variant(p,'x')=='2'
def test_compare():assert compare_variants({'accuracy':.8},{'accuracy':.9})['winner']=='challenger'
def test_log():assert structured_inference_log('m','1',3,10)['input_count']==3
def test_sign_verify(tmp_path):
 try:
  from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
  from cryptography.hazmat.primitives import serialization
 except ImportError:return
 p=tmp_path/'b';p.mkdir();(p/'manifest.json').write_text('{}');private=Ed25519PrivateKey.generate();pub=private.public_key();sign_bundle(p,private);assert verify_bundle_signature(p,pub)
def test_encrypt(tmp_path):
 try:from cryptography.fernet import Fernet
 except ImportError:return
 key=Fernet.generate_key();src=tmp_path/'a';enc=tmp_path/'b';out=tmp_path/'c';src.write_text('secret');encrypt_artifact(src,enc,key);decrypt_artifact(enc,out,key);assert out.read_text()=='secret'

