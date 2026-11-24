"""Phase 34: std.template module tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pealang.stdlib import build_standard_library


def test_template_render():
    std = build_standard_library()['std']
    result = std['template'].render("Hello {{name}}!", {"name": "World"})
    assert result == "Hello World!"


def test_template_render_file(tmp_path):
    std = build_standard_library()['std']
    template_file = tmp_path / "template.txt"
    template_file.write_text("Hello {{name}}!")
    result = std['template'].render_file(str(template_file), {"name": "World"})
    assert result == "Hello World!"
