"""Phase 101: deterministic observability and SRE sector-pack evidence."""

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
from pealang.observability_pack import (OBSERVABILITY_KINDS,
                                        OBSERVABILITY_PACK_FORMAT,
                                        OBSERVABILITY_PACK_VERSION,
                                        DEFAULT_OBSERVABILITY_PROFILE,
                                        ObservabilityPackError,
                                        ObservabilityProfileV2 as ProfileV2,
                                        build_observability_pack_namespace,
                                        load_observability_state_v2 as load_state_v2,
                                        observability_pack_capabilities as capabilities_v2,
                                        observability_pack_gate as gate_v2,
                                        observability_pack_report as report_v2,
                                        plan_observability_pack as plan_v2,
                                        write_observability_state_v2 as write_state_v2)
from pealang.specification import SPEC_VERSION


PROVIDERS = {
    'alert': 'alert-policy',
    'dashboard': 'dashboard',
    'log': 'log',
    'metric': 'metric',
    'runbook': 'incident-runbook',
    'slo': 'slo',
    'trace': 'trace',
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
        (root / 'apps' / f'{name}.observability.json').write_text(json.dumps(
            _app(name, kind, ['evidence/base.txt'], [], [name]),
        ), encoding='utf-8')
    (root / 'apps' / 'config.observability.json').write_text(json.dumps(
        _app('config', 'resource', ['evidence/base.txt']),
    ), encoding='utf-8')
    (root / 'apps' / 'demo.observability.json').write_text(json.dumps(
        _app('demo', 'reliability-demo', ['evidence/stack.txt'],
             sorted(PROVIDERS), ['log', 'trace']),
    ), encoding='utf-8')


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert (OBSERVABILITY_PACK_VERSION
            == pealang.OBSERVABILITY_PACK_VERSION == '5.1.0')
    assert (OBSERVABILITY_PACK_FORMAT
            == pealang.OBSERVABILITY_PACK_FORMAT == 'pea-observability-pack')
    assert caps == capabilities_v2()
    assert caps['version'] == '5.1.0'
    assert caps['source_filter'] == '*.observability.json'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert caps['kinds'] == sorted(OBSERVABILITY_KINDS)
    assert caps['options'] == [
        'max_entries', 'include_preview', 'check_trace', 'check_metric',
        'check_log', 'check_slo', 'check_alert', 'check_runbook',
        'check_dashboard', 'fail_on_incomplete', 'current_version',
    ]
    assert DEFAULT_OBSERVABILITY_PROFILE.digest() == ProfileV2().digest()
    assert DEFAULT_OBSERVABILITY_PROFILE.effective_version() == '5.1.0'
    assert ProfileV2(current_version='9.9.9').effective_version() == '9.9.9'
    with pytest.raises(ObservabilityPackError):
        ProfileV2(max_entries=0)
    with pytest.raises(ObservabilityPackError):
        ProfileV2(current_version=1)


def test_plan_discovers_entries_and_orders_dependencies(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.apps] == [
        'apps/alert.observability.json',
        'apps/config.observability.json',
        'apps/dashboard.observability.json',
        'apps/demo.observability.json',
        'apps/log.observability.json',
        'apps/metric.observability.json',
        'apps/runbook.observability.json',
        'apps/slo.observability.json',
        'apps/trace.observability.json',
    ]
    demo = plan.apps[3]
    assert demo.kind == 'reliability-demo'
    assert demo.requires == tuple(sorted(PROVIDERS))
    assert demo.dependencies == tuple(
        f'apps/{name}.observability.json' for name in sorted(PROVIDERS)
    )
    assert demo.bindings == ('log', 'trace')
    assert plan.build_order == (
        'apps/alert.observability.json',
        'apps/config.observability.json',
        'apps/dashboard.observability.json',
        'apps/log.observability.json',
        'apps/metric.observability.json',
        'apps/runbook.observability.json',
        'apps/slo.observability.json',
        'apps/trace.observability.json',
        'apps/demo.observability.json',
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
    assert payload['version'] == '5.1.0'
    assert payload['format'] == 'pea-observability-pack'
    assert len(payload['state']) == 9


def test_changed_entry_is_incomplete_and_propagates_to_demo(tmp_path):
    _write_pack(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'apps' / 'trace.observability.json').write_text(json.dumps(
        _app('trace', 'trace', ['evidence/base.txt'], [], ['trace', 'v2']),
    ), encoding='utf-8')
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.apps if item.state == 'stale'] == [
        'apps/demo.observability.json', 'apps/trace.observability.json',
    ]
    reasons = {item.path: item.reasons for item in plan.apps}
    assert reasons['apps/trace.observability.json'] == ('changed',)
    assert reasons['apps/demo.observability.json'] == ('dependency',)
    assert reasons['apps/metric.observability.json'] == ()
    assert gate_v2(report_v2([plan])) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_incomplete=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['incomplete']}


def test_missing_dependency_cycle_limit_and_invalid_manifest_issues(tmp_path):
    missing_root = tmp_path / 'missing'
    (missing_root / 'evidence').mkdir(parents=True)
    (missing_root / 'evidence' / 'root.txt').write_text('ok\n',
                                                        encoding='utf-8')
    (missing_root / 'orphan.observability.json').write_text(json.dumps(_app(
        'orphan', 'resource', ['evidence/root.txt'], ['absent'],
    )), encoding='utf-8')
    broken = plan_v2(missing_root)
    assert [item.code for item in broken.issues] == ['O201']
    assert 'absent' in broken.issues[0].message
    assert broken.gate == 'FAIL'

    cycle_root = tmp_path / 'cycle'
    (cycle_root / 'evidence').mkdir(parents=True)
    (cycle_root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    for name, requires in (('a', ['b']), ('b', ['a'])):
        (cycle_root / f'{name}.observability.json').write_text(json.dumps(_app(
            name, 'resource', ['evidence/root.txt'], requires,
        )), encoding='utf-8')
    cyclic = plan_v2(cycle_root)
    assert [item.code for item in cyclic.issues] == ['O202']
    assert cyclic.gate == 'FAIL'
    limited = plan_v2(cycle_root, ProfileV2(max_entries=1))
    assert 'O203' in [item.code for item in limited.issues]

    invalid_root = tmp_path / 'invalid'
    invalid_root.mkdir()
    (invalid_root / 'bad.observability.json').write_text('{}', encoding='utf-8')
    assert [item.code for item in plan_v2(invalid_root).issues] == ['O204']


def test_missing_evidence_issue(tmp_path):
    root = tmp_path / 'evidence-root'
    root.mkdir()
    (root / 'app.observability.json').write_text(json.dumps(_app(
        'app', 'resource', ['evidence/missing.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == ['O205']
    assert plan.gate == 'FAIL'


def test_governance_toggles(tmp_path):
    root = tmp_path / 'governance-root'
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'sample.observability.json').write_text(json.dumps(_app(
        'sample', 'reliability-demo', ['evidence/root.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == [
        'O206', 'O207', 'O208', 'O209', 'O210', 'O211', 'O212',
    ]
    assert plan.gate == 'FAIL'
    relaxed = plan_v2(root, ProfileV2(
        check_trace=False, check_metric=False, check_log=False,
        check_slo=False, check_alert=False, check_runbook=False,
        check_dashboard=False,
    ))
    assert relaxed.issues == ()
    assert relaxed.gate == 'PASS'
    toggles = (
        ('check_trace', 'O206'),
        ('check_metric', 'O207'),
        ('check_log', 'O208'),
        ('check_slo', 'O209'),
        ('check_alert', 'O210'),
        ('check_runbook', 'O211'),
        ('check_dashboard', 'O212'),
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
    (root / 'preview' / 'old.observability.json').write_text(json.dumps(_app(
        'old', 'resource', ['evidence/root.txt'],
    )), encoding='utf-8')
    assert plan_v2(root).apps == ()
    included = plan_v2(root, ProfileV2(include_preview=True))
    assert [item.path for item in included.apps] == [
        'preview/old.observability.json',
    ]


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '5.1.0'
    assert report['format'] == 'pea-observability-pack'
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
        [sys.executable, '-m', 'pealang.cli', 'observability-pack',
         '--capabilities'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '5.1.0'
    project = tmp_path / 'project'
    _write_pack(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'observability.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'observability-pack', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '5.1.0'
    assert report['app_count'] == 9
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'observability-pack', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['incomplete_count'] == 0
    (project / 'apps' / 'trace.observability.json').write_text(json.dumps(
        _app('trace', 'trace', ['evidence/base.txt'], [], ['trace', 'v2']),
    ), encoding='utf-8')
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'observability-pack', str(project),
         '--check', '--state', str(state_path), '--fail-on-incomplete'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['incomplete']
    minimal = tmp_path / 'minimal'
    (minimal / 'evidence').mkdir(parents=True)
    (minimal / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (minimal / 'sample.observability.json').write_text(json.dumps(
        _app('sample', 'reliability-demo', ['evidence/root.txt']),
    ), encoding='utf-8')
    relaxed = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'observability-pack', str(minimal),
         '--check', '--no-check-trace', '--no-check-metric', '--no-check-log',
         '--no-check-slo', '--no-check-alert', '--no-check-runbook',
         '--no-check-dashboard'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert relaxed.returncode == 0, relaxed.stderr
    assert json.loads(relaxed.stdout)['decision'] == {
        'gate': 'PASS', 'issues': [],
    }


def test_feature_flag_help_and_analysis_namespace_document_observability():
    status = feature_status('sector.observability_pack')
    assert status.stability == Stability.STABLE
    assert status.since == '5.1.0'
    text = pea_help('observability-pack')
    assert 'pea observability-pack' in text
    assert 'ObservabilityProfileV2 ->' in text
    assert 'observability_pack_gate(report)' in text
    namespace = build_observability_pack_namespace()
    assert namespace['OBSERVABILITY_PACK_VERSION'] == '5.1.0'
    assert (namespace['build_observability_pack_namespace']
            is build_observability_pack_namespace)
    analysis = build_analysis_namespace()
    for name in ('ObservabilityProfileV2', 'ObservabilityIssueV2',
                 'ObservabilityAppV2', 'ObservabilityPackPlanV2',
                 'PlanObservabilityPack', 'ObservabilityStateV2',
                 'WriteObservabilityStateV2', 'ObservabilityCapabilitiesV2',
                 'ObservabilityReportV2', 'ObservabilityGateV2',
                 'ObservabilityNamespaceV2'):
        assert name in analysis
    assert analysis['ObservabilityGateV2'] is gate_v2


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.25.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.25.0'
    assert manifest['previous_version'] == '5.24.0'
    assert manifest['release_line'] == 'tagged release v5.25.0'
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
