import asyncio
import json
import re
from pathlib import Path

import pealang
import pytest
from pealang.cli import main
from pealang.concurrency_resilience import (
    CancellationToken,
    CancellationReason,
    Deadline,
    run_with_deadline,
)
from pealang.core_freeze import verify_core_freeze
from pealang.specification import SECTIONS

ROOT = Path(__file__).parents[1]


def _dispatch_commands():
    text = (ROOT / 'pealang/cli.py').read_text(encoding='utf-8')
    found = set()
    for match in re.finditer(r"c\s*==\s*(['\"])(.*?)\1", text):
        found.add(match.group(2))
    for match in re.finditer(r"c\s+in\s+\(([^)]*)\)", text):
        for quoted in re.finditer(r"(['\"])(.*?)\1", match.group(1)):
            found.add(quoted.group(2))
    return {name for name in found if not name.startswith('-')}


def test_info_lists_full_dispatch_inventory(capsys):
    assert main(['info']) == 0
    info = json.loads(capsys.readouterr().out)
    assert set(info['commands']) == _dispatch_commands()


def test_manifest_note_and_metadata_are_current():
    manifest = json.loads((ROOT / 'RELEASE_MANIFEST.json').read_text(
        encoding='utf-8'))
    assert manifest['version'] == pealang.__version__
    assert 'Phase 126' in manifest['note']
    assert 'Phase 121' not in manifest['note']
    assert manifest['pytest_tests_passed'] == 436
    assert manifest['conformance_cases_passed'] == 500
    assert manifest['fuzz_iterations'] == 250
    assert manifest['tests_failed'] == 0
    assert manifest['status'] == 'PASS'
    guide = (ROOT / 'docs/USER_GUIDE.md').read_text(encoding='utf-8')
    assert f'PeaLang {pealang.__version__} release' in guide
    assert 'PeaLang 5.20.0 release' not in guide
    package_info = (ROOT / 'pealang.egg-info/PKG-INFO').read_text(
        encoding='utf-8')
    assert f"Version: {pealang.__version__}" in package_info
    output = (ROOT / 'pytest_output.txt').read_text(encoding='utf-8')
    assert 'Phase 126' in output
    assert '1236 passed' not in output
    assert '2075 passed, 1 skipped' not in output


def test_deadline_behavior_uses_never_completing_operation():
    async def case():
        token = CancellationToken()
        gate = asyncio.Event()
        with pytest.raises(asyncio.TimeoutError):
            await run_with_deadline(gate.wait(), Deadline.after(.001), token)
        assert token.cancelled and token.reason is CancellationReason.TIMEOUT

    asyncio.run(case())


def test_freeze_invariants_unchanged():
    assert len(SECTIONS) == 13
    freeze = verify_core_freeze()
    assert freeze['gate'] == 'PASS'
    assert freeze['digest'] == (
        '2e9f93e8506331d00131a33c3b99d799c3893d5f3ea1680acd3d2458327d461d')
