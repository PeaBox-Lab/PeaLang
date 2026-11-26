"""Phase 95: deterministic Mobile (iOS) sector-pack evidence."""

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
from pealang.ios_pack import (IOS_KINDS, IOS_PACK_FORMAT, IOS_PACK_VERSION,
                              DEFAULT_IOS_PROFILE, IOSPackError,
                              IOSProfileV2 as ProfileV2,
                              build_ios_pack_namespace,
                              ios_pack_capabilities as capabilities_v2,
                              ios_pack_gate as gate_v2,
                              ios_pack_report as report_v2,
                              load_ios_state_v2 as load_state_v2,
                              plan_ios_pack as plan_v2,
                              write_ios_state_v2 as write_state_v2)
from pealang.specification import SPEC_VERSION


def _ios(name, kind, evidence, requires=(), bindings=()):
    return {
        'name': name, 'version': '1.0.0', 'kind': kind,
        'evidence': list(evidence), 'requires': list(requires),
        'bindings': list(bindings),
    }


def _write_pack(root: Path) -> None:
    for folder in ('apps', 'evidence'):
        (root / folder).mkdir(parents=True, exist_ok=True)
    for name in ('base.txt', 'objc.txt', 'swift.txt', 'xcode.txt'):
        (root / 'evidence' / name).write_text(name + '\n', encoding='utf-8')
    items = {
        'apps/bridge.ios.json': _ios(
            'bridge', 'swift-bridge', ['evidence/swift.txt'], [], ['swift']),
        'apps/framework.ios.json': _ios(
            'framework', 'xcframework', ['evidence/base.txt'], [],
            ['xcframework']),
        'apps/objc.ios.json': _ios(
            'objc', 'objc-compat', ['evidence/objc.txt'], [], ['objc']),
        'apps/resource.ios.json': _ios(
            'resource', 'resource', ['evidence/base.txt']),
        'apps/sample.ios.json': _ios(
            'sample', 'sample-app', ['evidence/base.txt'],
            ['bridge', 'framework', 'objc', 'resource', 'service', 'template',
             'view'],
            ['objc', 'swift', 'template', 'xcframework']),
        'apps/service.ios.json': _ios(
            'service', 'service', ['evidence/base.txt']),
        'apps/template.ios.json': _ios(
            'template', 'xcode-template', ['evidence/xcode.txt'], [],
            ['xcode']),
        'apps/view.ios.json': _ios(
            'view', 'swift-view', ['evidence/swift.txt']),
    }
    for rel, payload in items.items():
        (root / rel).write_text(json.dumps(payload), encoding='utf-8')


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert IOS_PACK_VERSION == pealang.IOS_PACK_VERSION == '3.1.58'
    assert IOS_PACK_FORMAT == pealang.IOS_PACK_FORMAT == 'pea-ios-pack'
    assert caps == capabilities_v2()
    assert caps['version'] == '3.1.58'
    assert caps['source_filter'] == '*.ios.json'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert caps['kinds'] == sorted(IOS_KINDS)
    assert DEFAULT_IOS_PROFILE.digest() == ProfileV2().digest()
    assert DEFAULT_IOS_PROFILE.effective_version() == '3.1.58'
    assert ProfileV2(current_version='9.9.9').effective_version() == '9.9.9'
    with pytest.raises(IOSPackError):
        ProfileV2(max_apps=0)
    with pytest.raises(IOSPackError):
        ProfileV2(current_version=1)


def test_plan_discovers_apps_and_orders_dependencies(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.apps] == [
        'apps/bridge.ios.json',
        'apps/framework.ios.json',
        'apps/objc.ios.json',
        'apps/resource.ios.json',
        'apps/sample.ios.json',
        'apps/service.ios.json',
        'apps/template.ios.json',
        'apps/view.ios.json',
    ]
    assert [item.kind for item in plan.apps] == [
        'swift-bridge', 'xcframework', 'objc-compat', 'resource',
        'sample-app', 'service', 'xcode-template', 'swift-view',
    ]
    sample = plan.apps[4]
    assert sample.requires == (
        'bridge', 'framework', 'objc', 'resource', 'service', 'template',
        'view',
    )
    assert sample.dependencies == (
        'apps/bridge.ios.json', 'apps/framework.ios.json',
        'apps/objc.ios.json', 'apps/resource.ios.json',
        'apps/service.ios.json', 'apps/template.ios.json',
        'apps/view.ios.json',
    )
    assert sample.bindings == ('objc', 'swift', 'template', 'xcframework')
    assert plan.build_order == (
        'apps/bridge.ios.json',
        'apps/framework.ios.json',
        'apps/objc.ios.json',
        'apps/resource.ios.json',
        'apps/service.ios.json',
        'apps/template.ios.json',
        'apps/view.ios.json',
        'apps/sample.ios.json',
    )
    assert len(plan.incomplete) == 8
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
    assert payload['version'] == '3.1.58'
    assert payload['format'] == 'pea-ios-pack'
    assert len(payload['state']) == 8


def test_changed_app_is_incomplete_and_propagates_to_sample(tmp_path):
    _write_pack(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'apps' / 'objc.ios.json').write_text(json.dumps(
        _ios('objc', 'objc-compat', ['evidence/objc.txt'], [], ['objc', 'v2']),
    ), encoding='utf-8')
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.apps if item.state == 'stale'] == [
        'apps/objc.ios.json', 'apps/sample.ios.json',
    ]
    reasons = {item.path: item.reasons for item in plan.apps}
    assert reasons['apps/objc.ios.json'] == ('changed',)
    assert reasons['apps/sample.ios.json'] == ('dependency',)
    assert reasons['apps/bridge.ios.json'] == ()
    assert gate_v2(report_v2([plan])) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_incomplete=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['incomplete']}


def test_missing_dependency_cycle_limit_and_invalid_manifest_issues(tmp_path):
    missing_root = tmp_path / 'missing'
    (missing_root / 'evidence').mkdir(parents=True)
    (missing_root / 'evidence' / 'root.txt').write_text('ok\n',
                                                        encoding='utf-8')
    (missing_root / 'orphan.ios.json').write_text(json.dumps(_ios(
        'orphan', 'resource', ['evidence/root.txt'], ['absent'],
    )), encoding='utf-8')
    broken = plan_v2(missing_root)
    assert [item.code for item in broken.issues] == ['I201']
    assert 'absent' in broken.issues[0].message
    assert broken.gate == 'FAIL'

    cycle_root = tmp_path / 'cycle'
    (cycle_root / 'evidence').mkdir(parents=True)
    (cycle_root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    for name, requires in (('a', ['b']), ('b', ['a'])):
        (cycle_root / f'{name}.ios.json').write_text(json.dumps(_ios(
            name, 'resource', ['evidence/root.txt'], requires,
        )), encoding='utf-8')
    cyclic = plan_v2(cycle_root)
    assert [item.code for item in cyclic.issues] == ['I202']
    assert cyclic.gate == 'FAIL'
    limited = plan_v2(cycle_root, ProfileV2(max_apps=1))
    assert 'I203' in [item.code for item in limited.issues]

    invalid_root = tmp_path / 'invalid'
    invalid_root.mkdir()
    (invalid_root / 'bad.ios.json').write_text('{}', encoding='utf-8')
    assert [item.code for item in plan_v2(invalid_root).issues] == ['I204']


def test_missing_evidence_issue(tmp_path):
    root = tmp_path / 'evidence-root'
    root.mkdir()
    (root / 'app.ios.json').write_text(json.dumps(_ios(
        'app', 'resource', ['evidence/missing.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == ['I205']
    assert plan.gate == 'FAIL'


def test_swift_objc_framework_and_template_governance_issues_and_toggles(tmp_path):
    root = tmp_path / 'governance-root'
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'sample.ios.json').write_text(json.dumps(_ios(
        'sample', 'sample-app', ['evidence/root.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == [
        'I206', 'I207', 'I208', 'I209',
    ]
    assert plan.gate == 'FAIL'
    relaxed = plan_v2(root, ProfileV2(
        check_swift=False, check_objc=False, check_xcframework=False,
        check_templates=False,
    ))
    assert relaxed.issues == ()
    assert relaxed.gate == 'PASS'
    swift_off = plan_v2(root, ProfileV2(check_swift=False))
    assert [item.code for item in swift_off.issues] == ['I207', 'I208', 'I209']
    objc_off = plan_v2(root, ProfileV2(check_objc=False))
    assert [item.code for item in objc_off.issues] == ['I206', 'I208', 'I209']
    framework_off = plan_v2(root, ProfileV2(check_xcframework=False))
    assert [item.code for item in framework_off.issues] == [
        'I206', 'I207', 'I209',
    ]
    template_off = plan_v2(root, ProfileV2(check_templates=False))
    assert [item.code for item in template_off.issues] == [
        'I206', 'I207', 'I208',
    ]


def test_preview_apps_are_skipped_until_enabled(tmp_path):
    root = tmp_path / 'preview-root'
    (root / 'preview').mkdir(parents=True)
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'preview' / 'old.ios.json').write_text(json.dumps(_ios(
        'old', 'resource', ['evidence/root.txt'],
    )), encoding='utf-8')
    assert plan_v2(root).apps == ()
    included = plan_v2(root, ProfileV2(include_preview=True))
    assert [item.path for item in included.apps] == ['preview/old.ios.json']


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '3.1.58'
    assert report['format'] == 'pea-ios-pack'
    assert report['plan_count'] == 1
    assert report['app_count'] == 8
    assert report['incomplete_count'] == 8
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
        [sys.executable, '-m', 'pealang.cli', 'ios-pack', '--capabilities'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '3.1.58'
    project = tmp_path / 'project'
    _write_pack(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'ios.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'ios-pack', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '3.1.58'
    assert report['app_count'] == 8
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'ios-pack', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['incomplete_count'] == 0
    (project / 'apps' / 'objc.ios.json').write_text(json.dumps(
        _ios('objc', 'objc-compat', ['evidence/objc.txt'], [], ['objc', 'v2']),
    ), encoding='utf-8')
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'ios-pack', str(project),
         '--check', '--state', str(state_path), '--fail-on-incomplete'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['incomplete']
    minimal = tmp_path / 'minimal'
    (minimal / 'evidence').mkdir(parents=True)
    (minimal / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (minimal / 'sample.ios.json').write_text(json.dumps(
        _ios('sample', 'sample-app', ['evidence/root.txt']),
    ), encoding='utf-8')
    relaxed = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'ios-pack', str(minimal),
         '--check', '--no-check-swift', '--no-check-objc',
         '--no-check-xcframework', '--no-check-templates'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert relaxed.returncode == 0, relaxed.stderr
    assert json.loads(relaxed.stdout)['decision'] == {
        'gate': 'PASS', 'issues': [],
    }


def test_feature_flag_help_and_analysis_namespace_document_ios():
    status = feature_status('sector.ios_pack')
    assert status.stability == Stability.STABLE
    assert status.since == '3.1.58'
    text = pea_help('ios-pack')
    assert 'pea ios-pack' in text
    assert 'IOSProfileV2 ->' in text
    assert 'ios_pack_gate(report)' in text
    namespace = build_ios_pack_namespace()
    assert namespace['IOS_PACK_VERSION'] == '3.1.58'
    assert namespace['build_ios_pack_namespace'] is build_ios_pack_namespace
    analysis = build_analysis_namespace()
    for name in ('IOSProfileV2', 'IOSIssueV2', 'IOSAppV2', 'IOSPackPlanV2',
                 'PlanIOSPack', 'IOSStateV2', 'WriteIOSStateV2',
                 'IOSCapabilitiesV2', 'IOSReportV2', 'IOSGateV2',
                 'IOSNamespaceV2'):
        assert name in analysis
    assert analysis['IOSGateV2'] is gate_v2


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.6.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.6.0'
    assert manifest['previous_version'] == '5.5.0'
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
