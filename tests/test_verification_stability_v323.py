from pathlib import Path

import pealang

ROOT = Path(__file__).parents[1]

TIMEOUT_TESTS = (
    'tests/test_async_concurrency_v265.py',
    'tests/test_async_vm_v026.py',
    'tests/test_concurrency_resilience_v084.py',
)


def test_async_timeout_tests_use_pending_operations():
    for rel in TIMEOUT_TESTS:
        text = (ROOT / rel).read_text(encoding='utf-8')
        assert '.wait()' in text


def test_java_client_surface_is_declared():
    source = (ROOT / 'java-sdk' / 'src' / 'main' / 'java' / 'io' / 'pealang'
              / 'client' / 'PeaLangClient.java').read_text(encoding='utf-8')
    test = (ROOT / 'java-sdk' / 'src' / 'test' / 'java' / 'io' / 'pealang'
            / 'client' / 'PeaLangClientTest.java').read_text(encoding='utf-8')
    for name in ('health', 'ready', 'compile', 'loadModule', 'invoke'):
        assert f' {name}(' in source
        assert f'"{name}"' in test


def test_sdk_contract_versions_match_runtime():
    for rel in (
        'typescript-sdk/package.json', 'react-sdk/package.json',
        'browser-sdk/package.json',
    ):
        assert f'"version": "{pealang.__version__}"' in (
            ROOT / rel).read_text(encoding='utf-8')
    pom = (ROOT / 'java-sdk' / 'pom.xml').read_text(encoding='utf-8')
    assert f'<version>{pealang.__version__}</version>' in pom
