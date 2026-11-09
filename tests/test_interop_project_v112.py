from pealang import execute
from pealang.project import TEMPLATES


def test_interop_v112():
    src = r'''
print interop.cpu_count() >= 1
print len(interop.hostname()) > 0
print interop.pid() > 0
print interop.user() != null
'''
    out = []
    execute(src, output=out.append, source_name="interop.pea")
    assert out == ["true", "true", "true", "true"]


def test_automation_template_v112():
    assert "automation" in TEMPLATES
    assert "interop.walk" in TEMPLATES["automation"]
