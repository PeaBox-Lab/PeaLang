import json
from pathlib import Path
import pytest
from pealang import execute, compile_source, __version__
from pealang.errors import PeaError
from pealang.project import load_manifest

def test_version(): assert __version__ == "0.13.0"
def test_compat_execute():
    out=[]; execute('let x = 2\nprint x * 3', output=out.append); assert out == ['6']
def test_default_parameter():
    out=[]; execute('function f(x=4) { return x + 1 }\nprint f()', output=out.append); assert out == ['5']
def test_diagnostic_category():
    with pytest.raises(PeaError) as info: execute('print missing')
    assert 'Undefined variable' in str(info.value)
def test_manifest_validation(tmp_path):
    (tmp_path/'pea.json').write_text(json.dumps({'manifest_version':1,'project':{'name':'x','version':'1','entry':'main.txt'},'dependencies':{}}))
    with pytest.raises(PeaError): load_manifest(tmp_path)
def test_circular_import(tmp_path):
    (tmp_path/'a.pea').write_text('import "b.pea"')
    (tmp_path/'b.pea').write_text('import "a.pea"')
    with pytest.raises(PeaError, match='Circular import'): execute((tmp_path/'a.pea').read_text(),base_dir=tmp_path,source_name=str(tmp_path/'a.pea'))
