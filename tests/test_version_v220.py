"""Version consistency: pyproject, __init__, SDKs and README all agree."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "2.21.0"


def test_pyproject_version():
    txt = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version="2.21.0"' in txt


def test_init_version():
    txt = (ROOT / "pealang" / "__init__.py").read_text(encoding="utf-8")
    assert '__version__ = "2.21.0"' in txt


def test_sdk_package_versions():
    for pkg in ("typescript-sdk/package.json", "browser-sdk/package.json",
                "react-sdk/package.json"):
        data = json.loads((ROOT / pkg).read_text(encoding="utf-8"))
        assert data["version"] == EXPECTED, pkg


def test_react_peer_dep():
    data = json.loads((ROOT / "react-sdk/package.json").read_text(encoding="utf-8"))
    assert data["peerDependencies"]["@pealang/client"] == "^2.21.0"


def test_readme_documents_2_21_0():
    txt = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "2.21.0" in txt


def test_runtime_service_version():
    txt = (ROOT / "pealang" / "runtime_service.py").read_text(encoding="utf-8")
    assert "'version':'2.21.0'" in txt


def test_user_agent_version():
    txt = (ROOT / "pealang" / "registry_auth.py").read_text(encoding="utf-8")
    assert "PeaLang/2.21.0" in txt
