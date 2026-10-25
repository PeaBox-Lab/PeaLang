
from pathlib import Path
SPEC_VERSION='0.34'
SECTIONS=['00-introduction.md','01-lexical-grammar.md','02-types.md','03-expressions.md','04-statements.md','05-functions.md','06-modules.md','07-errors.md','08-async.md','09-host-interop.md','10-security.md','11-compatibility.md','grammar.ebnf']
def spec_root():return Path(__file__).resolve().parent.parent/'spec'
def verify_spec(root=None):
 base=Path(root) if root else spec_root();missing=[x for x in SECTIONS if not (base/x).is_file()];return {'version':SPEC_VERSION,'sections':len(SECTIONS),'missing':missing,'ok':not missing}

