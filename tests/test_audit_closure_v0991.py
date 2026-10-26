
from pealang.audit_closure_v0991 import audit_repository
from pathlib import Path
def test_repository_audit_closure():
 r=audit_repository(Path(__file__).parents[1]); assert r["passed"],r
def test_interface_inventory_is_exact():
 assert audit_repository(Path(__file__).parents[1])["interface_sites"]==23
def test_component_status_exists(): assert (Path(__file__).parents[1]/"docs/project/COMPONENT_STATUS_1_0.md").is_file()
def test_known_limitations_exists(): assert (Path(__file__).parents[1]/"docs/KNOWN_LIMITATIONS_1_0.md").is_file()

