"""Phase 112: deterministic Wave 7 maturity and consolidation sector-pack evidence."""

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
from pealang.maturity_gate import (MATURITY_GATE_KINDS,
                                        MATURITY_GATE_FORMAT,
                                        MATURITY_GATE_VERSION,
                                        DEFAULT_MATURITY_GATE_PROFILE,
                                        MaturityGatePackError,
                                        MaturityGateProfileV2 as ProfileV2,
                                        build_maturity_gate_namespace,
                                        load_maturity_gate_state_v2 as load_state_v2,
                                        maturity_gate_capabilities as capabilities_v2,
                                        maturity_gate_gate as gate_v2,
                                        maturity_gate_report as report_v2,
                                        plan_maturity_gate as plan_v2,
                                        write_maturity_gate_state_v2 as write_state_v2)
from pealang.specification import SPEC_VERSION


PROVIDERS = {
    'trust': 'trust-gate',
    'safety': 'safety-gate',
    'conformance': 'conformance-gate',
    'sector': 'sector-gate',
    'pilot': 'pilot-gate',
    'security': 'security-review',
    'freeze': 'version-freeze',
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
        (root / 'apps' / f'{name}.maturity.json').write_text(json.dumps(
            _app(name, kind, ['evidence/base.txt'], [], [name]),
        ), encoding='utf-8')
    (root / 'apps' / 'config.maturity.json').write_text(json.dumps(
        _app('config', 'resource', ['evidence/base.txt']),
    ), encoding='utf-8')
    (root / 'apps' / 'demo.maturity.json').write_text(json.dumps(
        _app('demo', 'maturity-demo', ['evidence/stack.txt'],
             sorted(PROVIDERS), ['trust', 'freeze']),
    ), encoding='utf-8')


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert (MATURITY_GATE_VERSION
            == pealang.MATURITY_GATE_VERSION == '5.12.0')
    assert (MATURITY_GATE_FORMAT
            == pealang.MATURITY_GATE_FORMAT == 'pea-maturity-gate')
    assert caps == capabilities_v2()
    assert caps['version'] == '5.12.0'
    assert caps['source_filter'] == '*.maturity.json'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert caps['kinds'] == sorted(MATURITY_GATE_KINDS)
    assert caps['options'] == [
        'max_entries', 'include_preview', 'check_trust', 'check_safety', 'check_conformance', 'check_sector',
        'check_pilot', 'check_security', 'check_freeze', 'fail_on_incomplete',
        'current_version',
    ]
    assert DEFAULT_MATURITY_GATE_PROFILE.digest() == ProfileV2().digest()
    assert DEFAULT_MATURITY_GATE_PROFILE.effective_version() == '5.12.0'
    assert ProfileV2(current_version='9.9.9').effective_version() == '9.9.9'
    with pytest.raises(MaturityGatePackError):
        ProfileV2(max_entries=0)
    with pytest.raises(MaturityGatePackError):
        ProfileV2(current_version=1)


def test_plan_discovers_entries_and_orders_dependencies(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.apps] == [
        'apps/config.maturity.json',
        'apps/conformance.maturity.json',
        'apps/demo.maturity.json',
        'apps/freeze.maturity.json',
        'apps/pilot.maturity.json',
        'apps/safety.maturity.json',
        'apps/sector.maturity.json',
        'apps/security.maturity.json',
        'apps/trust.maturity.json',
    ]
    demo = plan.apps[2]
    assert demo.kind == 'maturity-demo'
    assert demo.requires == tuple(sorted(PROVIDERS))
    assert demo.dependencies == tuple(
        f'apps/{name}.maturity.json' for name in sorted(PROVIDERS)
    )
    assert demo.bindings == ('freeze', 'trust')
    assert plan.build_order == (
        'apps/config.maturity.json',
        'apps/conformance.maturity.json',
        'apps/freeze.maturity.json',
        'apps/pilot.maturity.json',
        'apps/safety.maturity.json',
        'apps/sector.maturity.json',
        'apps/security.maturity.json',
        'apps/trust.maturity.json',
        'apps/demo.maturity.json',
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
    assert payload['version'] == '5.12.0'
    assert payload['format'] == 'pea-maturity-gate'
    assert len(payload['state']) == 9


def test_changed_entry_is_incomplete_and_propagates_to_demo(tmp_path):
    _write_pack(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'apps' / 'freeze.maturity.json').write_text(
        json.dumps(
            _app('freeze', 'version-freeze', ['evidence/base.txt'], [],
                 ['freeze', 'v2']),
        ), encoding='utf-8'
    )
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.apps if item.state == 'stale'] == [
        'apps/demo.maturity.json',
        'apps/freeze.maturity.json',
    ]
    reasons = {item.path: item.reasons for item in plan.apps}
    assert reasons['apps/freeze.maturity.json'] == ('changed',)
    assert reasons['apps/demo.maturity.json'] == ('dependency',)
    assert reasons['apps/conformance.maturity.json'] == ()
    assert gate_v2(report_v2([plan])) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_incomplete=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['incomplete']}


def test_missing_dependency_cycle_limit_and_invalid_manifest_issues(tmp_path):
    missing_root = tmp_path / 'missing'
    (missing_root / 'evidence').mkdir(parents=True)
    (missing_root / 'evidence' / 'root.txt').write_text('ok\n',
                                                        encoding='utf-8')
    (missing_root / 'orphan.maturity.json').write_text(json.dumps(_app(
        'orphan', 'resource', ['evidence/root.txt'], ['absent'],
    )), encoding='utf-8')
    broken = plan_v2(missing_root)
    assert [item.code for item in broken.issues] == ['Z201']
    assert 'absent' in broken.issues[0].message
    assert broken.gate == 'FAIL'

    cycle_root = tmp_path / 'cycle'
    (cycle_root / 'evidence').mkdir(parents=True)
    (cycle_root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    for name, requires in (('a', ['b']), ('b', ['a'])):
        (cycle_root / f'{name}.maturity.json').write_text(json.dumps(_app(
            name, 'resource', ['evidence/root.txt'], requires,
        )), encoding='utf-8')
    cyclic = plan_v2(cycle_root)
    assert [item.code for item in cyclic.issues] == ['Z202']
    assert cyclic.gate == 'FAIL'
    limited = plan_v2(cycle_root, ProfileV2(max_entries=1))
    assert 'Z203' in [item.code for item in limited.issues]

    invalid_root = tmp_path / 'invalid'
    invalid_root.mkdir()
    (invalid_root / 'bad.maturity.json').write_text('{}', encoding='utf-8')
    assert [item.code for item in plan_v2(invalid_root).issues] == ['Z204']


def test_missing_evidence_issue(tmp_path):
    root = tmp_path / 'evidence-root'
    root.mkdir()
    (root / 'app.maturity.json').write_text(json.dumps(_app(
        'app', 'resource', ['evidence/missing.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == ['Z205']
    assert plan.gate == 'FAIL'


def test_governance_toggles(tmp_path):
    root = tmp_path / 'governance-root'
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'sample.maturity.json').write_text(json.dumps(_app(
        'sample', 'maturity-demo', ['evidence/root.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == [
        'Z206', 'Z207', 'Z208', 'Z209', 'Z210', 'Z211', 'Z212',
    ]
    assert plan.gate == 'FAIL'
    relaxed = plan_v2(root, ProfileV2(
        check_trust=False, check_safety=False, check_conformance=False, check_sector=False,
        check_pilot=False, check_security=False, check_freeze=False,
    ))
    assert relaxed.issues == ()
    assert relaxed.gate == 'PASS'
    toggles = (
        ('check_trust', 'Z206'),
        ('check_safety', 'Z207'),
        ('check_conformance', 'Z208'),
        ('check_sector', 'Z209'),
        ('check_pilot', 'Z210'),
        ('check_security', 'Z211'),
        ('check_freeze', 'Z212'),
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
    (root / 'preview' / 'old.maturity.json').write_text(json.dumps(_app(
        'old', 'resource', ['evidence/root.txt'],
    )), encoding='utf-8')
    assert plan_v2(root).apps == ()
    included = plan_v2(root, ProfileV2(include_preview=True))
    assert [item.path for item in included.apps] == [
        'preview/old.maturity.json',
    ]


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '5.12.0'
    assert report['format'] == 'pea-maturity-gate'
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
        [sys.executable, '-m', 'pealang.cli', 'maturity-gate',
         '--capabilities'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '5.12.0'
    project = tmp_path / 'project'
    _write_pack(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'maturity_gate.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'maturity-gate', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '5.12.0'
    assert report['app_count'] == 9
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'maturity-gate', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['incomplete_count'] == 0
    (project / 'apps' / 'freeze.maturity.json').write_text(
        json.dumps(
            _app('freeze', 'version-freeze', ['evidence/base.txt'], [],
                 ['freeze', 'v2']),
        ), encoding='utf-8'
    )
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'maturity-gate', str(project),
         '--check', '--state', str(state_path), '--fail-on-incomplete'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['incomplete']
    minimal = tmp_path / 'minimal'
    (minimal / 'evidence').mkdir(parents=True)
    (minimal / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (minimal / 'sample.maturity.json').write_text(json.dumps(
        _app('sample', 'maturity-demo', ['evidence/root.txt']),
    ), encoding='utf-8')
    relaxed = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'maturity-gate', str(minimal),
         '--check', '--no-check-trust',
         '--check', '--no-check-safety',
         '--check', '--no-check-conformance',
         '--no-check-sector',
         '--no-check-pilot',
         '--no-check-security',
         '--no-check-freeze'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert relaxed.returncode == 0, relaxed.stderr
    assert json.loads(relaxed.stdout)['decision'] == {
        'gate': 'PASS', 'issues': [],
    }


def test_feature_flag_help_and_analysis_namespace_document_maturity_gate():
    status = feature_status('sector.maturity_gate')
    assert status.stability == Stability.STABLE
    assert status.since == '5.12.0'
    text = pea_help('maturity-gate')
    assert 'pea maturity-gate' in text
    assert 'MaturityGateProfileV2 ->' in text
    assert 'maturity_gate_gate(report)' in text
    namespace = build_maturity_gate_namespace()
    assert namespace['MATURITY_GATE_VERSION'] == '5.12.0'
    assert (namespace['build_maturity_gate_namespace']
            is build_maturity_gate_namespace)
    analysis = build_analysis_namespace()
    for name in ('MaturityGateProfileV2', 'MaturityGateIssueV2',
                 'MaturityGateAppV2', 'MaturityGatePackPlanV2',
                 'PlanMaturityGate', 'MaturityGateStateV2',
                 'WriteMaturityGateStateV2',
                 'MaturityGateCapabilitiesV2',
                 'MaturityGateReportV2', 'MaturityGateGateV2',
                 'MaturityGateNamespaceV2'):
        assert name in analysis
    assert analysis['MaturityGateGateV2'] is gate_v2


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.16.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.16.0'
    assert manifest['previous_version'] == '5.15.0'
    assert manifest['release_line'] == 'tagged release v5.16.0'
    assert pealang.MATURITY_GATE_VERSION == '5.12.0'
    assert pealang.EMBEDDED_DELIVERY_VERSION == '5.11.0'
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
