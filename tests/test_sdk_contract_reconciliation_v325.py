import json
from pathlib import Path

import pealang
from pealang.host_bindings import scaffold_java_sdk

ROOT = Path(__file__).parents[1]


def test_generated_java_sdk_matches_runtime_contract(tmp_path):
    target = tmp_path / 'java-sdk'
    out = scaffold_java_sdk(str(target))
    assert set(out['files']) == {
        'src/main/java/io/pealang/client/SdkClient.java',
        'pom.xml',
        'src/main/resources/application.yml',
        'README.md',
    }
    pom = (target / 'pom.xml').read_text(encoding='utf-8')
    assert '<groupId>io.pealang</groupId>' in pom
    assert '<artifactId>pealang-java-client</artifactId>' in pom
    assert f"<version>{pealang.__version__}</version>" in pom
    assert 'com.pealang' not in pom
    source = (target / 'src/main/java/io/pealang/client/SdkClient.java').read_text(
        encoding='utf-8')
    assert 'package io.pealang.client;' in source
    for name in ('health', 'ready', 'compile', 'loadModule', 'invoke'):
        assert f'public String {name}(' in source
    assert '\\"args\\":[' in source
    assert 'String.join' not in source
    assert 'com.pealang' not in source


def test_runtime_contract_uses_array_args():
    text = (ROOT / 'pealang/runtime_service.py').read_text(encoding='utf-8')
    assert "request.get('args',[])" in text


def test_sdk_docs_describe_shipped_exports():
    react = (ROOT / 'docs/REACT_SDK.md').read_text(encoding='utf-8')
    for name in ('PeaLangProvider', 'usePeaLang', 'usePeaFunction', 'PeaUi'):
        assert name in react
    assert 'v1.4.0' not in react
    help_react = (ROOT / 'help/REACT_SDK.md').read_text(encoding='utf-8')
    assert 'PeaLangProvider' in help_react
    assert 'v1.4.0' not in help_react
    browser = (ROOT / 'docs/WEB_SDK.md').read_text(encoding='utf-8')
    assert 'loadPeaWasm' in browser
    assert 'v1.5.0' not in browser
    help_browser = (ROOT / 'help/WEB_SDK.md').read_text(encoding='utf-8')
    assert 'loadPeaWasm' in help_browser
    assert 'v1.5.0' not in help_browser
    ts_react = (ROOT / 'docs/TYPESCRIPT_REACT.md').read_text(encoding='utf-8')
    assert '0.29 adds' not in ts_react
    assert pealang.__version__ in ts_react


def test_package_versions_and_pins_are_current():
    for rel in ('typescript-sdk/package.json', 'react-sdk/package.json',
                'browser-sdk/package.json'):
        data = json.loads((ROOT / rel).read_text(encoding='utf-8'))
        assert data['version'] == pealang.__version__, rel
    react = json.loads(
        (ROOT / 'react-sdk/package.json').read_text(encoding='utf-8'))
    assert react['peerDependencies']['@pealang/client'] == pealang.__version__
