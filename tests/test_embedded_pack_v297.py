"""Phase 97: deterministic Embedded / IoT / OS sector-pack evidence."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
import pytest
from pealang.analysis import build_analysis_namespace
from pealang.compatibility import Stability, feature_status
from pealang.core_freeze import core_freeze_report
from pealang.embedded_pack import (DEFAULT_EMBEDDED_PROFILE, EMBEDDED_KINDS,
                                   EMBEDDED_PACK_FORMAT,
                                   EMBEDDED_PACK_VERSION, EmbeddedPackError,
                                   EmbeddedProfileV2 as ProfileV2,
                                   build_embedded_pack_namespace,
                                   embedded_pack_capabilities as capabilities_v2,
                                   embedded_pack_gate as gate_v2,
                                   embedded_pack_report as report_v2,
                                   load_embedded_state_v2 as load_state_v2,
                                   plan_embedded_pack as plan_v2,
                                   write_embedded_state_v2 as write_state_v2)
from pealang.help import help as pea_help
from pealang.specification import SPEC_VERSION


def _app(name, kind, evidence, requires=(), bindings=()):
    return {
        'name': name, 'version': '1.0.0', 'kind': kind,
        'evidence': list(evidence), 'requires': list(requires),
        'bindings': list(bindings),
    }


def _write_pack(root: Path) -> None:
    for folder in ('apps', 'evidence'):
        (root / folder).mkdir(parents=True, exist_ok=True)
    for name in ('base.txt', 'firmware.txt'):
        (root / 'evidence' / name).write_text(name + '\n', encoding='utf-8')
    items = {
        'apps/demo.embedded.json': _app(
            'demo', 'firmware-demo', ['evidence/base.txt'],
            ['native', 'cabi', 'rtos', 'static', 'gpio', 'i2c', 'spi', 'can',
             'safety'],
            ['bounded-memory', 'signed-update', 'native', 'c-abi', 'rtos',
             'static', 'gpio', 'i2c', 'spi', 'can', 'safety']),
        'apps/cabi.embedded.json': _app(
            'cabi', 'c-abi', ['evidence/base.txt'], [], ['c-abi']),
        'apps/can.embedded.json': _app(
            'can', 'can-api', ['evidence/base.txt'], [], ['can']),
        'apps/gpio.embedded.json': _app(
            'gpio', 'gpio-api', ['evidence/base.txt'], [], ['gpio']),
        'apps/i2c.embedded.json': _app(
            'i2c', 'i2c-api', ['evidence/base.txt'], [], ['i2c']),
        'apps/level.embedded.json': _app(
            'level', 'resource', ['evidence/base.txt']),
        'apps/native.embedded.json': _app(
            'native', 'native-profile', ['evidence/base.txt'], [], ['native']),
        'apps/rtos.embedded.json': _app(
            'rtos', 'rtos-binding', ['evidence/base.txt'], [], ['rtos']),
        'apps/safety.embedded.json': _app(
            'safety', 'safety-audit', ['evidence/firmware.txt'], [],
            ['safety']),
        'apps/spi.embedded.json': _app(
            'spi', 'spi-api', ['evidence/base.txt'], [], ['spi']),
        'apps/static.embedded.json': _app(
            'static', 'static-binary', ['evidence/base.txt'], [], ['static']),
    }
    for rel, payload in items.items():
        (root / rel).write_text(json.dumps(payload), encoding='utf-8')


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert EMBEDDED_PACK_VERSION == pealang.EMBEDDED_PACK_VERSION == '3.1.60'
    assert EMBEDDED_PACK_FORMAT == pealang.EMBEDDED_PACK_FORMAT == 'pea-embedded-pack'
    assert caps == capabilities_v2()
    assert caps['version'] == '3.1.60'
    assert caps['source_filter'] == '*.embedded.json'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert caps['kinds'] == sorted(EMBEDDED_KINDS)
    assert caps['options'] == [
        'max_firmware', 'include_preview', 'check_native', 'check_c_abi',
        'check_rtos', 'check_static', 'check_bus', 'check_safety',
        'check_memory', 'check_signed', 'fail_on_incomplete',
        'current_version',
    ]
    assert DEFAULT_EMBEDDED_PROFILE.digest() == ProfileV2().digest()
    assert DEFAULT_EMBEDDED_PROFILE.effective_version() == '3.1.60'
    assert ProfileV2(current_version='9.9.9').effective_version() == '9.9.9'
    with pytest.raises(EmbeddedPackError):
        ProfileV2(max_firmware=0)
    with pytest.raises(EmbeddedPackError):
        ProfileV2(current_version=1)


def test_plan_discovers_apps_and_orders_dependencies(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.apps] == [
        'apps/cabi.embedded.json',
        'apps/can.embedded.json',
        'apps/demo.embedded.json',
        'apps/gpio.embedded.json',
        'apps/i2c.embedded.json',
        'apps/level.embedded.json',
        'apps/native.embedded.json',
        'apps/rtos.embedded.json',
        'apps/safety.embedded.json',
        'apps/spi.embedded.json',
        'apps/static.embedded.json',
    ]
    assert [item.kind for item in plan.apps] == [
        'c-abi', 'can-api', 'firmware-demo', 'gpio-api', 'i2c-api', 'resource',
        'native-profile', 'rtos-binding', 'safety-audit', 'spi-api',
        'static-binary',
    ]
    demo = plan.apps[2]
    assert demo.requires == (
        'cabi', 'can', 'gpio', 'i2c', 'native', 'rtos', 'safety', 'spi',
        'static',
    )
    assert demo.dependencies == (
        'apps/cabi.embedded.json', 'apps/can.embedded.json',
        'apps/gpio.embedded.json', 'apps/i2c.embedded.json',
        'apps/native.embedded.json', 'apps/rtos.embedded.json',
        'apps/safety.embedded.json', 'apps/spi.embedded.json',
        'apps/static.embedded.json',
    )
    assert demo.bindings == (
        'bounded-memory', 'c-abi', 'can', 'gpio', 'i2c', 'native', 'rtos',
        'safety', 'signed-update', 'spi', 'static',
    )
    assert plan.build_order == (
        'apps/cabi.embedded.json',
        'apps/can.embedded.json',
        'apps/gpio.embedded.json',
        'apps/i2c.embedded.json',
        'apps/level.embedded.json',
        'apps/native.embedded.json',
        'apps/rtos.embedded.json',
        'apps/safety.embedded.json',
        'apps/spi.embedded.json',
        'apps/static.embedded.json',
        'apps/demo.embedded.json',
    )
    assert len(plan.incomplete) == 11
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
    assert payload['version'] == '3.1.60'
    assert payload['format'] == 'pea-embedded-pack'
    assert len(payload['state']) == 11


def test_changed_app_is_incomplete_and_propagates_to_demo(tmp_path):
    _write_pack(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'apps' / 'native.embedded.json').write_text(json.dumps(
        _app('native', 'native-profile', ['evidence/base.txt'], [],
             ['native', 'v2']),
    ), encoding='utf-8')
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.apps if item.state == 'stale'] == [
        'apps/demo.embedded.json', 'apps/native.embedded.json',
    ]
    reasons = {item.path: item.reasons for item in plan.apps}
    assert reasons['apps/native.embedded.json'] == ('changed',)
    assert reasons['apps/demo.embedded.json'] == ('dependency',)
    assert reasons['apps/safety.embedded.json'] == ()
    assert gate_v2(report_v2([plan])) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_incomplete=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['incomplete']}


def test_missing_dependency_cycle_limit_and_invalid_manifest_issues(tmp_path):
    missing_root = tmp_path / 'missing'
    (missing_root / 'evidence').mkdir(parents=True)
    (missing_root / 'evidence' / 'root.txt').write_text('ok\n',
                                                        encoding='utf-8')
    (missing_root / 'orphan.embedded.json').write_text(json.dumps(_app(
        'orphan', 'resource', ['evidence/root.txt'], ['absent'],
    )), encoding='utf-8')
    broken = plan_v2(missing_root)
    assert [item.code for item in broken.issues] == ['E201']
    assert 'absent' in broken.issues[0].message
    assert broken.gate == 'FAIL'

    cycle_root = tmp_path / 'cycle'
    (cycle_root / 'evidence').mkdir(parents=True)
    (cycle_root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    for name, requires in (('a', ['b']), ('b', ['a'])):
        (cycle_root / f'{name}.embedded.json').write_text(json.dumps(_app(
            name, 'resource', ['evidence/root.txt'], requires,
        )), encoding='utf-8')
    cyclic = plan_v2(cycle_root)
    assert [item.code for item in cyclic.issues] == ['E202']
    assert cyclic.gate == 'FAIL'
    limited = plan_v2(cycle_root, ProfileV2(max_firmware=1))
    assert 'E203' in [item.code for item in limited.issues]

    invalid_root = tmp_path / 'invalid'
    invalid_root.mkdir()
    (invalid_root / 'bad.embedded.json').write_text('{}', encoding='utf-8')
    assert [item.code for item in plan_v2(invalid_root).issues] == ['E204']


def test_missing_evidence_issue(tmp_path):
    root = tmp_path / 'evidence-root'
    root.mkdir()
    (root / 'app.embedded.json').write_text(json.dumps(_app(
        'app', 'resource', ['evidence/missing.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == ['E205']
    assert plan.gate == 'FAIL'


def test_governance_toggles(tmp_path):
    root = tmp_path / 'governance-root'
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'sample.embedded.json').write_text(json.dumps(_app(
        'sample', 'firmware-demo', ['evidence/root.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == [
        'E206', 'E207', 'E208', 'E209', 'E210', 'E211', 'E212', 'E213',
    ]
    assert plan.gate == 'FAIL'
    relaxed = plan_v2(root, ProfileV2(
        check_native=False, check_c_abi=False, check_rtos=False,
        check_static=False, check_bus=False, check_safety=False,
        check_memory=False, check_signed=False,
    ))
    assert relaxed.issues == ()
    assert relaxed.gate == 'PASS'
    toggles = (
        ('check_native', 'E206'), ('check_c_abi', 'E207'),
        ('check_rtos', 'E208'), ('check_static', 'E209'),
        ('check_bus', 'E210'), ('check_safety', 'E211'),
        ('check_memory', 'E212'), ('check_signed', 'E213'),
    )
    for field, code in toggles:
        single = plan_v2(root, ProfileV2(**{field: False}))
        codes = [item.code for item in single.issues]
        assert code not in codes
        assert len(codes) == 7


def test_preview_apps_are_skipped_until_enabled(tmp_path):
    root = tmp_path / 'preview-root'
    (root / 'preview').mkdir(parents=True)
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'preview' / 'old.embedded.json').write_text(json.dumps(_app(
        'old', 'resource', ['evidence/root.txt'],
    )), encoding='utf-8')
    assert plan_v2(root).apps == ()
    included = plan_v2(root, ProfileV2(include_preview=True))
    assert [item.path for item in included.apps] == [
        'preview/old.embedded.json',
    ]


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '3.1.60'
    assert report['format'] == 'pea-embedded-pack'
    assert report['plan_count'] == 1
    assert report['app_count'] == 11
    assert report['incomplete_count'] == 11
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
        [sys.executable, '-m', 'pealang.cli', 'embedded-pack',
         '--capabilities'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '3.1.60'
    project = tmp_path / 'project'
    _write_pack(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'embedded.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'embedded-pack', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '3.1.60'
    assert report['app_count'] == 11
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'embedded-pack', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['incomplete_count'] == 0
    (project / 'apps' / 'cabi.embedded.json').write_text(json.dumps(
        _app('cabi', 'c-abi', ['evidence/base.txt'], [], ['c-abi', 'v2']),
    ), encoding='utf-8')
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'embedded-pack', str(project),
         '--check', '--state', str(state_path), '--fail-on-incomplete'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['incomplete']
    minimal = tmp_path / 'minimal'
    (minimal / 'evidence').mkdir(parents=True)
    (minimal / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (minimal / 'sample.embedded.json').write_text(json.dumps(
        _app('sample', 'firmware-demo', ['evidence/root.txt']),
    ), encoding='utf-8')
    relaxed = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'embedded-pack', str(minimal),
         '--check', '--no-check-native', '--no-check-c-abi',
         '--no-check-rtos', '--no-check-static', '--no-check-bus',
         '--no-check-safety', '--no-check-memory', '--no-check-signed'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert relaxed.returncode == 0, relaxed.stderr
    assert json.loads(relaxed.stdout)['decision'] == {
        'gate': 'PASS', 'issues': [],
    }


def test_feature_flag_help_and_analysis_namespace_document_embedded():
    status = feature_status('sector.embedded_pack')
    assert status.stability == Stability.STABLE
    assert status.since == '3.1.60'
    text = pea_help('embedded-pack')
    assert 'pea embedded-pack' in text
    assert 'EmbeddedProfileV2 ->' in text
    assert 'embedded_pack_gate(report)' in text
    namespace = build_embedded_pack_namespace()
    assert namespace['EMBEDDED_PACK_VERSION'] == '3.1.60'
    assert (namespace['build_embedded_pack_namespace']
            is build_embedded_pack_namespace)
    analysis = build_analysis_namespace()
    for name in ('EmbeddedProfileV2', 'EmbeddedIssueV2', 'EmbeddedAppV2',
                 'EmbeddedPackPlanV2', 'PlanEmbeddedPack', 'EmbeddedStateV2',
                 'WriteEmbeddedStateV2', 'EmbeddedCapabilitiesV2',
                 'EmbeddedReportV2', 'EmbeddedGateV2',
                 'EmbeddedNamespaceV2'):
        assert name in analysis
    assert analysis['EmbeddedGateV2'] is gate_v2


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.17.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.17.0'
    assert manifest['previous_version'] == '5.16.0'
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
