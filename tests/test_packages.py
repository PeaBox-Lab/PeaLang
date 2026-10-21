
import json
from pathlib import Path
from pealang.project import write_lock,verify_lock

def make_project(tmp_path):
    dep=tmp_path/'dep'; dep.mkdir(); (dep/'main.pea').write_text('export answer\nlet answer = 42\n')
    (dep/'pea.json').write_text(json.dumps({'manifest_version':1,'project':{'name':'dep','version':'1','entry':'main.pea'},'dependencies':{}}))
    (tmp_path/'main.pea').write_text('print "ok"\n')
    (tmp_path/'pea.json').write_text(json.dumps({'manifest_version':1,'project':{'name':'app','version':'1','entry':'main.pea'},'dependencies':{'dep':{'path':'dep'}}}))
    return dep

def test_lock_and_verify(tmp_path):
    make_project(tmp_path); path,lock=write_lock(tmp_path)
    assert path.exists() and len(lock['dependencies'])==1
    assert verify_lock(tmp_path)['ok']

def test_integrity_change_detected(tmp_path):
    dep=make_project(tmp_path); write_lock(tmp_path)
    (dep/'main.pea').write_text('let answer = 99\nexport answer\n')
    result=verify_lock(tmp_path); assert not result['ok']; assert 'integrity mismatch' in result['problems'][0]
