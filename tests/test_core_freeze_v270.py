"""Phase 70: frozen 3.0 core manifest and release gate."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
from pealang import (
    CORE_SURFACES,
    FREEZE_RELEASE,
    CoreFreezeManifest,
    CoreSurface,
    Stability,
    default_core_manifest,
    feature_status,
)
from pealang.help import help as pea_help
from pealang.specification import SPEC_VERSION


def _passing_inputs():
    return {
        'api': {'gate': 'PASS'},
        'conformance': {'suite': {'ok': True}},
        'spec': {'ok': True, 'version': SPEC_VERSION},
    }


def test_default_manifest_is_stable_and_complete():
    manifest = default_core_manifest()
    assert len(manifest.surfaces) == len(CORE_SURFACES) == 11
    assert manifest.to_dict()['policy'] == 'pealang-3.0-core-freeze'
    assert manifest.to_dict()['core_version'] == '3.0'
    assert manifest.digest() == default_core_manifest().digest()
    assert all(surface.stability == 'frozen' for surface in manifest.surfaces.values())


def test_manifest_diff_detects_removed_and_changed_surfaces():
    baseline = default_core_manifest()
    removed = CoreFreezeManifest(CORE_SURFACES[:-1])
    assert removed.diff(baseline)['removed'] == [CORE_SURFACES[-1].name]

    changed = CoreFreezeManifest((
        CoreSurface('core.syntax', 'syntax', '0.1', stability='preview'),
        *CORE_SURFACES[1:],
    ))
    assert 'core.syntax' in changed.diff(baseline)['changed']


def test_manifest_rejects_duplicate_surfaces():
    manifest = CoreFreezeManifest()
    manifest.add(CORE_SURFACES[0])
    try:
        manifest.add(CORE_SURFACES[0])
    except ValueError as exc:
        assert 'duplicate frozen surface' in str(exc)
    else:
        raise AssertionError('duplicate surface was accepted')


def test_core_freeze_gate_passes_with_all_inputs():
    from pealang.core_freeze import core_freeze_gate

    result = core_freeze_gate(**_passing_inputs())
    assert result['gate'] == 'PASS'
    assert result['issues'] == []
    assert all(result['checks'].values())


def test_core_freeze_gate_reports_each_failed_check():
    from pealang.core_freeze import core_freeze_gate

    inputs = _passing_inputs()
    inputs['api'] = {'gate': 'FAIL'}
    inputs['conformance'] = {'suite': {'ok': False}}
    inputs['spec'] = {'ok': True, 'version': '0.0.0'}
    inputs['manifest'] = CoreFreezeManifest((
        CoreSurface('core.syntax', 'syntax', '0.1', stability='preview'),
    ))
    result = core_freeze_gate(**inputs)
    assert result['gate'] == 'FAIL'
    assert set(result['issues']) == {
        'public_api', 'conformance', 'specification', 'surfaces',
    }


def test_verify_core_freeze_passes_against_repository():
    from pealang.core_freeze import verify_core_freeze

    result = verify_core_freeze()
    assert result['gate'] == 'PASS', result
    assert result['release'] == FREEZE_RELEASE
    assert result['spec_version'] == result['package_version'] == pealang.__version__
    assert result['digest'] == default_core_manifest().digest()
    assert all(result['checks'].values())


def test_core_freeze_report_cli_passes():
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'freeze'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['freeze']['gate'] == 'PASS'
    assert report['manifest']['core_version'] == '3.0'


def test_core_freeze_feature_flag_is_stable():
    assert feature_status('language.core_freeze_v3').stability == Stability.STABLE


def test_help_documents_freeze_gate():
    text = pea_help('freeze')
    assert 'pea freeze' in text
    assert 'verify_core_freeze()' in text
    assert 'CORE_SURFACES' in text
