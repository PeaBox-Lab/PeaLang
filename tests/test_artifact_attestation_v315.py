"""Phase 115: deterministic release artifact attestation and provenance sector-pack evidence."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
import pytest
from pealang.analysis import build_analysis_namespace
from pealang.compatibility import Stability, feature_status
from pealang.core_freeze import core_freeze_report
from pealang.help import help as pea_help
from pealang.artifact_attestation import (ARTIFACT_ATTESTATION_KINDS,
                                        ARTIFACT_ATTESTATION_FORMAT,
                                        ARTIFACT_ATTESTATION_VERSION,
                                        DEFAULT_ARTIFACT_ATTESTATION_PROFILE,
                                        ArtifactAttestationPackError,
                                        ArtifactAttestationProfileV2 as ProfileV2,
                                        build_artifact_attestation_namespace,
                                        load_artifact_attestation_state_v2 as load_state_v2,
                                        artifact_attestation_capabilities as capabilities_v2,
                                        artifact_attestation_gate as gate_v2,
                                        artifact_attestation_report as report_v2,
                                        plan_artifact_attestation as plan_v2,
                                        write_artifact_attestation_state_v2 as write_state_v2)
from pealang.specification import SPEC_VERSION


PROVIDERS = {
    'wheel': 'wheel-digest',
    'sdist': 'sdist-digest',
    'container': 'container-manifest',
    'sbom': 'sbom',
    'provenance': 'provenance',
    'signature': 'signature',
    'repro': 'reproducibility',
}


def _app(name, kind, evidence, requires=(), bindings=()):
    return {
        'name': name, 'version': '1.0.0', 'kind': kind,
        'evidence': list(evidence), 'requires': list(requires),
        'bindings': list(bindings),
    }


def _write_pack(root: Path) -> None:
    (root / 'apps').mkdir(parents=True, exist_ok=True)
    (root / 'evidence').mkdir(parents=True, exist_ok=True)
    (root / 'evidence' / 'base.txt').write_text('base\n', encoding='utf-8')
    (root / 'evidence' / 'stack.txt').write_text('stack\n', encoding='utf-8')
    for name, kind in PROVIDERS.items():
        (root / 'apps' / f'{name}.attestation.json').write_text(json.dumps(
            _app(name, kind, ['evidence/base.txt'], [], [name]),
        ), encoding='utf-8')
    (root / 'apps' / 'config.attestation.json').write_text(json.dumps(
        _app('config', 'resource', ['evidence/base.txt']),
    ), encoding='utf-8')
    (root / 'apps' / 'demo.attestation.json').write_text(json.dumps(
        _app('demo', 'artifact-demo', ['evidence/stack.txt'],
             sorted(PROVIDERS), ['signature', 'provenance']),
    ), encoding='utf-8')


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert (ARTIFACT_ATTESTATION_VERSION
            == pealang.ARTIFACT_ATTESTATION_VERSION == '5.15.0')
    assert (ARTIFACT_ATTESTATION_FORMAT
            == pealang.ARTIFACT_ATTESTATION_FORMAT == 'pea-artifact-attestation')
    assert caps == capabilities_v2()
    assert caps['version'] == '5.15.0'
    assert caps['source_filter'] == '*.attestation.json'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert caps['kinds'] == sorted(ARTIFACT_ATTESTATION_KINDS)
    assert caps['options'] == [
        'max_entries', 'include_preview', 'check_wheel', 'check_sdist', 'check_container', 'check_sbom',
        'check_provenance', 'check_signature', 'check_repro', 'fail_on_incomplete',
        'current_version',
    ]
    assert DEFAULT_ARTIFACT_ATTESTATION_PROFILE.digest() == ProfileV2().digest()
    assert DEFAULT_ARTIFACT_ATTESTATION_PROFILE.effective_version() == '5.15.0'
    assert ProfileV2(current_version='9.9.9').effective_version() == '9.9.9'
    with pytest.raises(ArtifactAttestationPackError):
        ProfileV2(max_entries=0)
    with pytest.raises(ArtifactAttestationPackError):
        ProfileV2(current_version=1)


def test_plan_discovers_entries_and_orders_dependencies(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.apps] == [
        'apps/config.attestation.json',
        'apps/container.attestation.json',
        'apps/demo.attestation.json',
        'apps/provenance.attestation.json',
        'apps/repro.attestation.json',
        'apps/sbom.attestation.json',
        'apps/sdist.attestation.json',
        'apps/signature.attestation.json',
        'apps/wheel.attestation.json',
    ]
    demo = plan.apps[2]
    assert demo.kind == 'artifact-demo'
    assert demo.requires == tuple(sorted(PROVIDERS))
    assert demo.dependencies == tuple(
        f'apps/{name}.attestation.json' for name in sorted(PROVIDERS)
    )
    assert demo.bindings == ('provenance', 'signature')
    assert plan.build_order == (
        'apps/config.attestation.json',
        'apps/container.attestation.json',
        'apps/provenance.attestation.json',
        'apps/repro.attestation.json',
        'apps/sbom.attestation.json',
        'apps/sdist.attestation.json',
        'apps/signature.attestation.json',
        'apps/wheel.attestation.json',
        'apps/demo.attestation.json',
    )
    assert len(plan.incomplete) == 9
    assert all(item.state == 'stale' for item in plan.apps)
    assert plan.gate == 'PASS'
    assert plan.issues == ()
    assert len(plan.digest) == 64
    assert all(len(item.fingerprint()) == 64 for item in plan.apps)
    assert all('\\' not in item.path and ':' not in item.path
               for item in plan.apps)


def test_state_round_trip_and_digest_ignores_host_root(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    state_path = write_state_v2(tmp_path, plan)
    state = load_state_v2(state_path)
    clean = plan_v2(tmp_path, state=state)
    assert clean.incomplete == ()
    assert all(item.state == 'current' for item in clean.apps)
    assert all(item.reasons == () for item in clean.apps)
    assert clean.gate == 'PASS'
    copy_root = tmp_path / 'copy'
    _write_pack(copy_root)
    assert plan_v2(copy_root).digest == plan.digest
    payload = json.loads(state_path.read_text(encoding='utf-8'))
    assert payload['version'] == '5.15.0'
    assert payload['format'] == 'pea-artifact-attestation'
    assert len(payload['state']) == 9


def test_changed_entry_is_incomplete_and_propagates_to_demo(tmp_path):
    _write_pack(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'apps' / 'repro.attestation.json').write_text(
        json.dumps(
            _app('repro', 'reproducibility', ['evidence/base.txt'], [],
                 ['repro', 'v2']),
        ), encoding='utf-8'
    )
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.apps if item.state == 'stale'] == [
        'apps/demo.attestation.json',
        'apps/repro.attestation.json',
    ]
    reasons = {item.path: item.reasons for item in plan.apps}
    assert reasons['apps/repro.attestation.json'] == ('changed',)
    assert reasons['apps/demo.attestation.json'] == ('dependency',)
    assert reasons['apps/container.attestation.json'] == ()
    assert gate_v2(report_v2([plan])) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_incomplete=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['incomplete']}


def test_missing_dependency_cycle_limit_and_invalid_manifest_issues(tmp_path):
    missing_root = tmp_path / 'missing'
    (missing_root / 'evidence').mkdir(parents=True)
    (missing_root / 'evidence' / 'root.txt').write_text('ok\n',
                                                        encoding='utf-8')
    (missing_root / 'orphan.attestation.json').write_text(json.dumps(_app(
        'orphan', 'resource', ['evidence/root.txt'], ['absent'],
    )), encoding='utf-8')
    broken = plan_v2(missing_root)
    assert [item.code for item in broken.issues] == ['AT201']
    assert 'absent' in broken.issues[0].message
    assert broken.gate == 'FAIL'

    cycle_root = tmp_path / 'cycle'
    (cycle_root / 'evidence').mkdir(parents=True)
    (cycle_root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    for name, requires in (('a', ['b']), ('b', ['a'])):
        (cycle_root / f'{name}.attestation.json').write_text(json.dumps(_app(
            name, 'resource', ['evidence/root.txt'], requires,
        )), encoding='utf-8')
    cyclic = plan_v2(cycle_root)
    assert [item.code for item in cyclic.issues] == ['AT202']
    assert cyclic.gate == 'FAIL'
    limited = plan_v2(cycle_root, ProfileV2(max_entries=1))
    assert 'AT203' in [item.code for item in limited.issues]

    invalid_root = tmp_path / 'invalid'
    invalid_root.mkdir()
    (invalid_root / 'bad.attestation.json').write_text('{}', encoding='utf-8')
    assert [item.code for item in plan_v2(invalid_root).issues] == ['AT204']


def test_missing_evidence_issue(tmp_path):
    root = tmp_path / 'evidence-root'
    root.mkdir()
    (root / 'app.attestation.json').write_text(json.dumps(_app(
        'app', 'resource', ['evidence/missing.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == ['AT205']
    assert plan.gate == 'FAIL'


def test_governance_toggles(tmp_path):
    root = tmp_path / 'governance-root'
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'sample.attestation.json').write_text(json.dumps(_app(
        'sample', 'artifact-demo', ['evidence/root.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == [
        'AT206', 'AT207', 'AT208', 'AT209', 'AT210', 'AT211', 'AT212',
    ]
    assert plan.gate == 'FAIL'
    relaxed = plan_v2(root, ProfileV2(
        check_wheel=False, check_sdist=False, check_container=False, check_sbom=False,
        check_provenance=False, check_signature=False, check_repro=False,
    ))
    assert relaxed.issues == ()
    assert relaxed.gate == 'PASS'
    toggles = (
        ('check_wheel', 'AT206'),
        ('check_sdist', 'AT207'),
        ('check_container', 'AT208'),
        ('check_sbom', 'AT209'),
        ('check_provenance', 'AT210'),
        ('check_signature', 'AT211'),
        ('check_repro', 'AT212'),
    )
    for field, code in toggles:
        single = plan_v2(root, ProfileV2(**{field: False}))
        codes = [item.code for item in single.issues]
        assert code not in codes
        assert len(codes) == 6


def test_preview_entries_are_skipped_until_enabled(tmp_path):
    root = tmp_path / 'preview-root'
    (root / 'preview').mkdir(parents=True)
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'preview' / 'old.attestation.json').write_text(json.dumps(_app(
        'old', 'resource', ['evidence/root.txt'],
    )), encoding='utf-8')
    assert plan_v2(root).apps == ()
    included = plan_v2(root, ProfileV2(include_preview=True))
    assert [item.path for item in included.apps] == [
        'preview/old.attestation.json',
    ]


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '5.15.0'
    assert report['format'] == 'pea-artifact-attestation'
    assert report['plan_count'] == 1
    assert report['app_count'] == 9
    assert report['incomplete_count'] == 9
    assert report['clean_count'] == 0
    assert report['error_count'] == 0
    assert report['gate'] == 'PASS'
    assert len(report['digest']) == 64
    assert gate_v2(report) == {'gate': 'PASS', 'issues': []}
    assert 'version' in gate_v2({**report, 'version': 'old'})['issues']
    assert 'format' in gate_v2({**report, 'format': 'old'})['issues']
    assert 'digest' in gate_v2({**report, 'digest': '0' * 64})['issues']
    assert 'counts' in gate_v2({**report, 'app_count': 99})['issues']
    tampered = json.loads(json.dumps(report))
    tampered['plans'][0]['apps'][0]['fingerprint'] = '0' * 64
    assert 'app_fingerprint' in gate_v2(tampered)['issues']


def test_cli_capabilities_check_emit_state_and_strict_gate(tmp_path):
    project_root = Path(__file__).resolve().parent.parent
    caps = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'artifact-attestation',
         '--capabilities'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '5.15.0'
    project = tmp_path / 'project'
    _write_pack(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'artifact_attestation.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'artifact-attestation', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '5.15.0'
    assert report['app_count'] == 9
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'artifact-attestation', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['incomplete_count'] == 0
    (project / 'apps' / 'repro.attestation.json').write_text(
        json.dumps(
            _app('repro', 'reproducibility', ['evidence/base.txt'], [],
                 ['repro', 'v2']),
        ), encoding='utf-8'
    )
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'artifact-attestation', str(project),
         '--check', '--state', str(state_path), '--fail-on-incomplete'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['incomplete']
    minimal = tmp_path / 'minimal'
    (minimal / 'evidence').mkdir(parents=True)
    (minimal / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (minimal / 'sample.attestation.json').write_text(json.dumps(
        _app('sample', 'artifact-demo', ['evidence/root.txt']),
    ), encoding='utf-8')
    relaxed = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'artifact-attestation', str(minimal),
         '--check', '--no-check-wheel',
         '--check', '--no-check-sdist',
         '--check', '--no-check-container',
         '--no-check-sbom',
         '--no-check-provenance',
         '--no-check-signature',
         '--no-check-repro'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert relaxed.returncode == 0, relaxed.stderr
    assert json.loads(relaxed.stdout)['decision'] == {
        'gate': 'PASS', 'issues': [],
    }


def test_feature_flag_help_and_analysis_namespace_document_artifact_attestation():
    status = feature_status('sector.artifact_attestation')
    assert status.stability == Stability.STABLE
    assert status.since == '5.15.0'
    text = pea_help('artifact-attestation')
    assert 'pea artifact-attestation' in text
    assert 'ArtifactAttestationProfileV2 ->' in text
    assert 'artifact_attestation_gate(report)' in text
    namespace = build_artifact_attestation_namespace()
    assert namespace['ARTIFACT_ATTESTATION_VERSION'] == '5.15.0'
    assert (namespace['build_artifact_attestation_namespace']
            is build_artifact_attestation_namespace)
    analysis = build_analysis_namespace()
    for name in ('ArtifactAttestationProfileV2', 'ArtifactAttestationIssueV2',
                 'ArtifactAttestationAppV2', 'ArtifactAttestationPackPlanV2',
                 'PlanArtifactAttestation', 'ArtifactAttestationStateV2',
                 'WriteArtifactAttestationStateV2',
                 'ArtifactAttestationCapabilitiesV2',
                 'ArtifactAttestationReportV2', 'ArtifactAttestationGateV2',
                 'ArtifactAttestationNamespaceV2'):
        assert name in analysis
    assert analysis['ArtifactAttestationGateV2'] is gate_v2


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.24.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.24.0'
    assert manifest['previous_version'] == '5.23.0'
    assert manifest['release_line'] == 'tagged release v5.24.0'
    assert pealang.ARTIFACT_ATTESTATION_VERSION == '5.15.0'
    assert pealang.CI_EVIDENCE_VERSION == '5.14.0'
    assert pealang.CAPACITY_PACK_VERSION == '5.4.0'
    assert pealang.CHAOS_PACK_VERSION == '5.3.0'
    assert pealang.SLO_PACK_VERSION == '5.2.0'
    assert pealang.OBSERVABILITY_PACK_VERSION == '5.1.0'
    assert pealang.CERTIFIED_PACK_VERSION == '5.0.0'
    assert pealang.ECOSYSTEM_PACK_VERSION == '3.1.62'
    assert pealang.CLOUD_PACK_VERSION == '3.1.61'
    assert pealang.EMBEDDED_PACK_VERSION == '3.1.60'
    assert pealang.GAME_PACK_VERSION == '3.1.59'
    assert pealang.IOS_PACK_VERSION == '3.1.58'
    assert pealang.ANDROID_PACK_VERSION == '3.1.57'
    assert pealang.WEB_PACK_VERSION == '3.1.56'
    assert pealang.DATA_PACK_VERSION == '3.1.55'
    assert pealang.FINANCE_PACK_VERSION == '3.1.54'
    assert pealang.DEVEX_V2_VERSION == '3.1.53'
    assert pealang.PROJECT_TEMPLATES_V2_VERSION == '3.1.52'
    assert pealang.MIGRATION_ASSISTANTS_VERSION == '3.1.51'
    assert pealang.VERSIONED_DOCS_VERSION == '3.1.50'
    assert pealang.BUILD_SYSTEM_V2_VERSION == '3.1.49'
    assert pealang.TEST_FRAMEWORK_V2_VERSION == '3.1.48'
    assert pealang.LINTER_V3_VERSION == '3.1.47'
    assert pealang.FORMATTER_V3_VERSION == '3.1.46'
    assert pealang.DAP_V2_VERSION == '3.1.45'
    assert pealang.LSP_V2_VERSION == '3.1.44'
    assert pealang.PARALLEL_RUNTIME_VERSION == '3.1.43'
    assert pealang.RUNTIME_PROFILER_VERSION == '3.1.43'
    assert pealang.WASM_BACKEND_VERSION == '3.1.42'
    assert pealang.NATIVE_BACKEND_VERSION == '3.1.41'
    assert pealang.BYTECODE_JIT_VERSION == '3.1.40'
    assert pealang.FAST_INTERPRETER_VERSION == '3.1.39'
    assert pealang.OPTIMIZER_VERSION == '3.1.38'
    assert pealang.CORE_RELEASE_FROZEN_AT == '3.1.37'


def test_frozen_core_gate_still_passes():
    report = core_freeze_report()
    assert report['release'] == '3.1.37'
    assert report['freeze']['gate'] == 'PASS'
    assert report['freeze']['digest'] == (
        '2e9f93e8506331d00131a33c3b99d799c3893d5f3ea1680acd3d2458327d461d')
