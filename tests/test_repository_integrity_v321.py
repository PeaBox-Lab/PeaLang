import hashlib
import json
from pathlib import Path

import pealang

ROOT = Path(__file__).parents[1]


def test_api_snapshot_sidecar_matches_json():
    data = (ROOT / 'PUBLIC_API_SNAPSHOT.json').read_bytes()
    expected = hashlib.sha256(data).hexdigest()
    sidecar = (ROOT / 'PUBLIC_API_SNAPSHOT.sha256').read_text(encoding='utf-8')
    assert sidecar.strip().lower() == expected


def test_release_manifest_note_and_fixed_metrics_are_current():
    manifest = json.loads((ROOT / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == pealang.__version__
    assert manifest['previous_version'] == '5.20.0'
    assert 'Phase 88' not in manifest['note']
    assert 'Phase 121' in manifest['note']
    assert manifest['pytest_tests_passed'] == 436
    assert manifest['conformance_cases_passed'] == 500
    assert manifest['fuzz_iterations'] == 250
    assert manifest['tests_failed'] == 0
    assert manifest['status'] == 'PASS'


def test_sdk_metadata_versions_match_runtime():
    pom = (ROOT / 'java-sdk' / 'pom.xml').read_text(encoding='utf-8')
    assert f'<version>{pealang.__version__}</version>' in pom
    readme = (ROOT / 'browser-sdk' / 'README.md').read_text(encoding='utf-8')
    assert readme.splitlines()[0] == f'# PeaLang Browser SDK {pealang.__version__}'


def test_roadmap_tail_and_stale_test_output_are_removed():
    roadmap = (ROOT / 'ROADMAP.md').read_text(encoding='utf-8').rstrip()
    assert not roadmap.endswith('### Phase 34: Standard Library Completion (2.41.0)')
    output = (ROOT / 'pytest_output.txt').read_text(encoding='utf-8')
    assert '1236 passed' not in output
    assert '2075 passed, 1 skipped' in output
