
from pathlib import Path
import pytest
from pealang.browser_profile import validate_browser_permissions,validate_ui_schema

def test_browser_permissions_safe():assert validate_browser_permissions(['http.fetch','console'])
def test_browser_permissions_reject_process():
 with pytest.raises(Exception):validate_browser_permissions(['process'])
def test_ui_schema_valid():assert validate_ui_schema({'type':'stack','children':[{'type':'text','text':'Hello'}]})['type']=='stack'
def test_ui_schema_reject_unknown():
 with pytest.raises(Exception):validate_ui_schema({'type':'html','html':'<script>x</script>'})
def test_ts_client_present():
 p=Path(__file__).parents[1]/'typescript-sdk/src/index.ts';s=p.read_text();assert 'class PeaLangClient' in s and '/v1/invoke' in s
def test_react_hooks_present():
 p=Path(__file__).parents[1]/'react-sdk/src/index.tsx';s=p.read_text();assert 'PeaLangProvider' in s and 'usePeaFunction' in s and 'PeaUi' in s

