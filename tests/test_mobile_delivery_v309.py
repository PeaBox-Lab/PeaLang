"""Phase 109: deterministic mobile delivery evidence sector-pack evidence."""

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
from pealang.mobile_delivery import (MOBILE_DELIVERY_KINDS,
                                        MOBILE_DELIVERY_FORMAT,
                                        MOBILE_DELIVERY_VERSION,
                                        DEFAULT_MOBILE_DELIVERY_PROFILE,
                                        MobileDeliveryPackError,
                                        MobileDeliveryProfileV2 as ProfileV2,
                                        build_mobile_delivery_namespace,
                                        load_mobile_delivery_state_v2 as load_state_v2,
                                        mobile_delivery_capabilities as capabilities_v2,
                                        mobile_delivery_gate as gate_v2,
                                        mobile_delivery_report as report_v2,
                                        plan_mobile_delivery as plan_v2,
                                        write_mobile_delivery_state_v2 as write_state_v2)
from pealang.specification import SPEC_VERSION


PROVIDERS = {
    'android': 'android-bridge',
    'ios': 'ios-bridge',
    'lifecycle': 'lifecycle-binding',
    'sdk': 'sdk-bundle',
    'sample': 'sample-app',
    'pipeline': 'build-pipeline',
    'devices': 'device-matrix',
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
        (root / 'apps' / f'{name}.mobile.json').write_text(json.dumps(
            _app(name, kind, ['evidence/base.txt'], [], [name]),
        ), encoding='utf-8')
    (root / 'apps' / 'config.mobile.json').write_text(json.dumps(
        _app('config', 'resource', ['evidence/base.txt']),
    ), encoding='utf-8')
    (root / 'apps' / 'demo.mobile.json').write_text(json.dumps(
        _app('demo', 'mobile-demo', ['evidence/stack.txt'],
             sorted(PROVIDERS), ['android', 'sample']),
    ), encoding='utf-8')


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert (MOBILE_DELIVERY_VERSION
            == pealang.MOBILE_DELIVERY_VERSION == '5.9.0')
    assert (MOBILE_DELIVERY_FORMAT
            == pealang.MOBILE_DELIVERY_FORMAT == 'pea-mobile-delivery')
    assert caps == capabilities_v2()
    assert caps['version'] == '5.9.0'
    assert caps['source_filter'] == '*.mobile.json'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert caps['kinds'] == sorted(MOBILE_DELIVERY_KINDS)
    assert caps['options'] == [
        'max_entries', 'include_preview', 'check_android', 'check_ios', 'check_lifecycle', 'check_sdk',
        'check_sample', 'check_pipeline', 'check_devices', 'fail_on_incomplete',
        'current_version',
    ]
    assert DEFAULT_MOBILE_DELIVERY_PROFILE.digest() == ProfileV2().digest()
    assert DEFAULT_MOBILE_DELIVERY_PROFILE.effective_version() == '5.9.0'
    assert ProfileV2(current_version='9.9.9').effective_version() == '9.9.9'
    with pytest.raises(MobileDeliveryPackError):
        ProfileV2(max_entries=0)
    with pytest.raises(MobileDeliveryPackError):
        ProfileV2(current_version=1)


def test_plan_discovers_entries_and_orders_dependencies(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.apps] == [
        'apps/android.mobile.json',
        'apps/config.mobile.json',
        'apps/demo.mobile.json',
        'apps/devices.mobile.json',
        'apps/ios.mobile.json',
        'apps/lifecycle.mobile.json',
        'apps/pipeline.mobile.json',
        'apps/sample.mobile.json',
        'apps/sdk.mobile.json',
    ]
    demo = plan.apps[2]
    assert demo.kind == 'mobile-demo'
    assert demo.requires == tuple(sorted(PROVIDERS))
    assert demo.dependencies == tuple(
        f'apps/{name}.mobile.json' for name in sorted(PROVIDERS)
    )
    assert demo.bindings == ('android', 'sample')
    assert plan.build_order == (
        'apps/android.mobile.json',
        'apps/config.mobile.json',
        'apps/devices.mobile.json',
        'apps/ios.mobile.json',
        'apps/lifecycle.mobile.json',
        'apps/pipeline.mobile.json',
        'apps/sample.mobile.json',
        'apps/sdk.mobile.json',
        'apps/demo.mobile.json',
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
    assert payload['version'] == '5.9.0'
    assert payload['format'] == 'pea-mobile-delivery'
    assert len(payload['state']) == 9


def test_changed_entry_is_incomplete_and_propagates_to_demo(tmp_path):
    _write_pack(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'apps' / 'devices.mobile.json').write_text(
        json.dumps(
            _app('devices', 'device-matrix', ['evidence/base.txt'], [],
                 ['devices', 'v2']),
        ), encoding='utf-8'
    )
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.apps if item.state == 'stale'] == [
        'apps/demo.mobile.json',
        'apps/devices.mobile.json',
    ]
    reasons = {item.path: item.reasons for item in plan.apps}
    assert reasons['apps/devices.mobile.json'] == ('changed',)
    assert reasons['apps/demo.mobile.json'] == ('dependency',)
    assert reasons['apps/android.mobile.json'] == ()
    assert gate_v2(report_v2([plan])) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_incomplete=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['incomplete']}


def test_missing_dependency_cycle_limit_and_invalid_manifest_issues(tmp_path):
    missing_root = tmp_path / 'missing'
    (missing_root / 'evidence').mkdir(parents=True)
    (missing_root / 'evidence' / 'root.txt').write_text('ok\n',
                                                        encoding='utf-8')
    (missing_root / 'orphan.mobile.json').write_text(json.dumps(_app(
        'orphan', 'resource', ['evidence/root.txt'], ['absent'],
    )), encoding='utf-8')
    broken = plan_v2(missing_root)
    assert [item.code for item in broken.issues] == ['B201']
    assert 'absent' in broken.issues[0].message
    assert broken.gate == 'FAIL'

    cycle_root = tmp_path / 'cycle'
    (cycle_root / 'evidence').mkdir(parents=True)
    (cycle_root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    for name, requires in (('a', ['b']), ('b', ['a'])):
        (cycle_root / f'{name}.mobile.json').write_text(json.dumps(_app(
            name, 'resource', ['evidence/root.txt'], requires,
        )), encoding='utf-8')
    cyclic = plan_v2(cycle_root)
    assert [item.code for item in cyclic.issues] == ['B202']
    assert cyclic.gate == 'FAIL'
    limited = plan_v2(cycle_root, ProfileV2(max_entries=1))
    assert 'B203' in [item.code for item in limited.issues]

    invalid_root = tmp_path / 'invalid'
    invalid_root.mkdir()
    (invalid_root / 'bad.mobile.json').write_text('{}', encoding='utf-8')
    assert [item.code for item in plan_v2(invalid_root).issues] == ['B204']


def test_missing_evidence_issue(tmp_path):
    root = tmp_path / 'evidence-root'
    root.mkdir()
    (root / 'app.mobile.json').write_text(json.dumps(_app(
        'app', 'resource', ['evidence/missing.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == ['B205']
    assert plan.gate == 'FAIL'


def test_governance_toggles(tmp_path):
    root = tmp_path / 'governance-root'
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'sample.mobile.json').write_text(json.dumps(_app(
        'sample', 'mobile-demo', ['evidence/root.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == [
        'B206', 'B207', 'B208', 'B209', 'B210', 'B211', 'B212',
    ]
    assert plan.gate == 'FAIL'
    relaxed = plan_v2(root, ProfileV2(
        check_android=False, check_ios=False, check_lifecycle=False, check_sdk=False,
        check_sample=False, check_pipeline=False, check_devices=False,
    ))
    assert relaxed.issues == ()
    assert relaxed.gate == 'PASS'
    toggles = (
        ('check_android', 'B206'),
        ('check_ios', 'B207'),
        ('check_lifecycle', 'B208'),
        ('check_sdk', 'B209'),
        ('check_sample', 'B210'),
        ('check_pipeline', 'B211'),
        ('check_devices', 'B212'),
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
    (root / 'preview' / 'old.mobile.json').write_text(json.dumps(_app(
        'old', 'resource', ['evidence/root.txt'],
    )), encoding='utf-8')
    assert plan_v2(root).apps == ()
    included = plan_v2(root, ProfileV2(include_preview=True))
    assert [item.path for item in included.apps] == [
        'preview/old.mobile.json',
    ]


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '5.9.0'
    assert report['format'] == 'pea-mobile-delivery'
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
        [sys.executable, '-m', 'pealang.cli', 'mobile-delivery',
         '--capabilities'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '5.9.0'
    project = tmp_path / 'project'
    _write_pack(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'mobile_delivery.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'mobile-delivery', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '5.9.0'
    assert report['app_count'] == 9
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'mobile-delivery', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['incomplete_count'] == 0
    (project / 'apps' / 'devices.mobile.json').write_text(
        json.dumps(
            _app('devices', 'device-matrix', ['evidence/base.txt'], [],
                 ['devices', 'v2']),
        ), encoding='utf-8'
    )
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'mobile-delivery', str(project),
         '--check', '--state', str(state_path), '--fail-on-incomplete'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['incomplete']
    minimal = tmp_path / 'minimal'
    (minimal / 'evidence').mkdir(parents=True)
    (minimal / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (minimal / 'sample.mobile.json').write_text(json.dumps(
        _app('sample', 'mobile-demo', ['evidence/root.txt']),
    ), encoding='utf-8')
    relaxed = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'mobile-delivery', str(minimal),
         '--check', '--no-check-android',
         '--check', '--no-check-ios',
         '--check', '--no-check-lifecycle',
         '--no-check-sdk',
         '--no-check-sample',
         '--no-check-pipeline',
         '--no-check-devices'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert relaxed.returncode == 0, relaxed.stderr
    assert json.loads(relaxed.stdout)['decision'] == {
        'gate': 'PASS', 'issues': [],
    }


def test_feature_flag_help_and_analysis_namespace_document_mobile_delivery():
    status = feature_status('sector.mobile_delivery')
    assert status.stability == Stability.STABLE
    assert status.since == '5.9.0'
    text = pea_help('mobile-delivery')
    assert 'pea mobile-delivery' in text
    assert 'MobileDeliveryProfileV2 ->' in text
    assert 'mobile_delivery_gate(report)' in text
    namespace = build_mobile_delivery_namespace()
    assert namespace['MOBILE_DELIVERY_VERSION'] == '5.9.0'
    assert (namespace['build_mobile_delivery_namespace']
            is build_mobile_delivery_namespace)
    analysis = build_analysis_namespace()
    for name in ('MobileDeliveryProfileV2', 'MobileDeliveryIssueV2',
                 'MobileDeliveryAppV2', 'MobileDeliveryPackPlanV2',
                 'PlanMobileDelivery', 'MobileDeliveryStateV2',
                 'WriteMobileDeliveryStateV2',
                 'MobileDeliveryCapabilitiesV2',
                 'MobileDeliveryReportV2', 'MobileDeliveryGateV2',
                 'MobileDeliveryNamespaceV2'):
        assert name in analysis
    assert analysis['MobileDeliveryGateV2'] is gate_v2


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.13.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.13.0'
    assert manifest['previous_version'] == '5.12.0'
    assert manifest['release_line'] == 'tagged release v5.13.0'
    assert pealang.MOBILE_DELIVERY_VERSION == '5.9.0'
    assert pealang.PILOT_EVIDENCE_VERSION == '5.8.0'
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
