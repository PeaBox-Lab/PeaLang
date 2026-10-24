
from pealang.kubernetes_security import *
def test_secure_manifests():
 docs=secure_kubernetes_manifests(SecureKubernetesConfig(name='demo',config_map='cfg',secret_name='sec'));assert [x['kind'] for x in docs]==['Deployment','Service','PodDisruptionBudget','NetworkPolicy'];c=docs[0]['spec']['template']['spec']['containers'][0];assert c['securityContext']['readOnlyRootFilesystem'] and c['securityContext']['capabilities']['drop']==['ALL']
def test_validation():assert validate_manifests(secure_kubernetes_manifests())['valid']
def test_yaml():
 y=to_yaml({'a':1,'b':[{'c':True}]});assert 'a: 1' in y and 'c: true' in y
def test_write(tmp_path):assert len(write_secure_manifests(tmp_path))==4 and (tmp_path/'deployment.yaml').exists()
def test_drain():
 d=DrainController();d.begin();d.end();assert d.drain(.1)
def test_drain_blocks():
 d=DrainController();d.draining=True
 try:d.begin();assert False
 except RuntimeError:assert True
def test_matrix():assert any(x.platform=='Windows' for x in rc_compatibility_matrix())
def test_soak():assert soak_test(lambda i:i,.02)['status']=='PASS'
