
import warnings
from pealang.rc_stabilization import *
def test_snapshot(tmp_path):
 (tmp_path/'x.py').write_text('def f(a,b=1): pass\nclass C: pass\n');s=public_api_snapshot(tmp_path);assert len(s['symbols'])==2 and len(snapshot_digest(s))==64
def test_compare():
 a={'symbols':[{'module':'m','name':'f','signature':'(a)'}]};b={'symbols':[{'module':'m','name':'f','signature':'(a)'},{'module':'m','name':'g','signature':'()'}]};r=compare_api_snapshots(a,b);assert r['compatible'] and r['added']==['m.g']
def test_compare_break():
 a={'symbols':[{'module':'m','name':'f','signature':'(a)'}]};b={'symbols':[]};assert not compare_api_snapshots(a,b)['compatible']
def test_deprecated():
 @deprecated('old','new')
 def f():return 1
 with warnings.catch_warnings(record=True) as w:warnings.simplefilter('always');assert f()==1 and w
def test_schedule():assert validate_deprecation_schedule([Deprecation('x','y','0.63','1.0')])['valid']
def test_integrations():
 r=run_integration_matrix({'ok':lambda:True});assert integration_summary(r)['ready']
def test_upgrade():assert len(upgrade_compatibility(['0.60','0.61','0.62'])['upgrades'])==3
def test_threat():assert len(threat_model()['threats'])>=5
def test_migration():assert 'back up registry and monitoring databases' in migration_guide()['steps']
def test_gate():assert rc_gate({'tests':True,'licenses':False})['status']=='BLOCKED'
