from pathlib import Path
from pealang.security_closure_v0994 import audit_python_tree
ROOT=Path(__file__).parents[1]
def test_security_closure_has_no_forbidden_patterns():
 r=audit_python_tree(ROOT); assert r["passed"],r
def test_supply_chain_uses_uuid5_not_md5():
 s=(ROOT/"pealang/supply_chain.py").read_text(); assert "uuid.uuid5" in s and "hashlib.md5" not in s
def test_security_workflow_present(): assert (ROOT/".github/workflows/security-scanners.yml").is_file()
