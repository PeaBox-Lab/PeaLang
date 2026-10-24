
from pealang.compatibility import Stability,feature_status,stable_features,validate_deprecation
from pealang.specification import verify_spec,SPEC_VERSION

def test_spec_complete():r=verify_spec();assert r['ok'] and r['sections']==13 and SPEC_VERSION=='0.34'
def test_core_stable():assert feature_status('core.syntax').stability==Stability.STABLE
def test_peac_preview():assert feature_status('vm.peac').stability==Stability.PREVIEW
def test_stable_list():assert 'embedding.python' in stable_features()
def test_nonremoved_ok():assert validate_deprecation('core.syntax','0.34')
def test_grammar_contains_async():
 from pealang.specification import spec_root
 assert '"async"' in (spec_root()/'grammar.ebnf').read_text()
def test_security_spec_present():
 from pealang.specification import spec_root
 assert 'unregistered host' in (spec_root()/'10-security.md').read_text()
