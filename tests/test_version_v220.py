"""Version consistency: package, SDK, runtime, container, and spec metadata agree."""

import json
from pathlib import Path

from pealang.specification import SPEC_VERSION

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "5.19.0"


def test_pyproject_version():
    txt = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version="5.19.0"' in txt


def test_init_version():
    txt = (ROOT / "pealang" / "__init__.py").read_text(encoding="utf-8")
    assert '__version__ = "5.19.0"' in txt


def test_sdk_package_versions():
    for pkg in ("typescript-sdk/package.json", "browser-sdk/package.json",
                "react-sdk/package.json"):
        data = json.loads((ROOT / pkg).read_text(encoding="utf-8"))
        assert data["version"] == EXPECTED, pkg


def test_react_peer_dep():
    data = json.loads((ROOT / "react-sdk/package.json").read_text(encoding="utf-8"))
    assert data["peerDependencies"]["@pealang/client"] == "^5.19.0"


def test_readme_documents_release():
    txt = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Version: 5.19.0" in txt


def test_release_manifest_version():
    data = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    assert data["version"] == EXPECTED
    assert data["release_line"] == "tagged release v5.19.0"


def test_container_version():
    txt = (ROOT / "Containerfile").read_text(encoding="utf-8")
    assert "pealang-5.19.0-py3-none-any.whl" in txt
    assert 'org.opencontainers.image.version="5.19.0"' in txt


def test_specification_version():
    assert SPEC_VERSION == EXPECTED
    heading = (ROOT / "spec" / "00-introduction.md").read_text(encoding="utf-8").splitlines()[0]
    assert heading == "# PeaLang Language Specification 5.19.0"


def test_runtime_service_version():
    txt = (ROOT / "pealang" / "runtime_service.py").read_text(encoding="utf-8")
    assert "'version':'5.19.0'" in txt


def test_user_agent_version():
    txt = (ROOT / "pealang" / "registry_auth.py").read_text(encoding="utf-8")
    assert "PeaLang/5.19.0" in txt
