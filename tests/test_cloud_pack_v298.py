"""Phase 98: deterministic Cloud Infrastructure / DevOps sector-pack evidence."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
import pytest
from pealang.analysis import build_analysis_namespace
from pealang.cloud_pack import (CLOUD_KINDS, CLOUD_PACK_FORMAT,
                                CLOUD_PACK_VERSION, DEFAULT_CLOUD_PROFILE,
                                CloudPackError, CloudProfileV2 as ProfileV2,
                                build_cloud_pack_namespace,
                                cloud_pack_capabilities as capabilities_v2,
                                cloud_pack_gate as gate_v2,
                                cloud_pack_report as report_v2,
                                load_cloud_state_v2 as load_state_v2,
                                plan_cloud_pack as plan_v2,
                                write_cloud_state_v2 as write_state_v2)
from pealang.compatibility import Stability, feature_status
from pealang.core_freeze import core_freeze_report
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
    for name in ('base.txt', 'stack.txt'):
        (root / 'evidence' / name).write_text(name + '\n', encoding='utf-8')
    items = {
        'apps/demo.cloud.json': _app(
            'demo', 'deployment-demo', ['evidence/stack.txt'],
            ['bash', 'cdk', 'container', 'go', 'iam', 'k8s', 'observability',
             'pipeline', 'python', 'terraform'],
            ['bash', 'cdk', 'container', 'drift-check', 'go', 'iam', 'k8s',
             'lockfile', 'observability', 'pipeline', 'python',
             'signed-package', 'terraform']),
        'apps/bash.cloud.json': _app(
            'bash', 'bash-script', ['evidence/base.txt'], [], ['bash']),
        'apps/cdk.cloud.json': _app(
            'cdk', 'cdk-stack', ['evidence/base.txt'], [], ['cdk']),
        'apps/config.cloud.json': _app(
            'config', 'resource', ['evidence/base.txt']),
        'apps/container.cloud.json': _app(
            'container', 'container-image', ['evidence/base.txt'], [],
            ['container']),
        'apps/go.cloud.json': _app(
            'go', 'go-service', ['evidence/base.txt'], [], ['go']),
        'apps/iam.cloud.json': _app(
            'iam', 'iam-policy', ['evidence/base.txt'], [], ['iam']),
        'apps/k8s.cloud.json': _app(
            'k8s', 'k8s-manifest', ['evidence/base.txt'], [], ['k8s']),
        'apps/observability.cloud.json': _app(
            'observability', 'observability', ['evidence/base.txt'], [],
            ['observability']),
        'apps/pipeline.cloud.json': _app(
            'pipeline', 'ci-pipeline', ['evidence/base.txt'], [],
            ['pipeline']),
        'apps/python.cloud.json': _app(
            'python', 'python-service', ['evidence/base.txt'], [], ['python']),
        'apps/terraform.cloud.json': _app(
            'terraform', 'terraform-module', ['evidence/base.txt'], [],
            ['terraform']),
    }
    for rel, payload in items.items():
        (root / rel).write_text(json.dumps(payload), encoding='utf-8')


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert CLOUD_PACK_VERSION == pealang.CLOUD_PACK_VERSION == '3.1.61'
    assert CLOUD_PACK_FORMAT == pealang.CLOUD_PACK_FORMAT == 'pea-cloud-pack'
    assert caps == capabilities_v2()
    assert caps['version'] == '3.1.61'
    assert caps['source_filter'] == '*.cloud.json'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert caps['kinds'] == sorted(CLOUD_KINDS)
    assert caps['options'] == [
        'max_deployments', 'include_preview', 'check_container',
        'check_orchestration', 'check_pipeline', 'check_observability',
        'check_iam', 'check_source', 'check_lockfile', 'check_signed',
        'check_drift', 'fail_on_incomplete', 'current_version',
    ]
    assert DEFAULT_CLOUD_PROFILE.digest() == ProfileV2().digest()
    assert DEFAULT_CLOUD_PROFILE.effective_version() == '3.1.61'
    assert ProfileV2(current_version='9.9.9').effective_version() == '9.9.9'
    with pytest.raises(CloudPackError):
        ProfileV2(max_deployments=0)
    with pytest.raises(CloudPackError):
        ProfileV2(current_version=1)


def test_plan_discovers_apps_and_orders_dependencies(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.apps] == [
        'apps/bash.cloud.json',
        'apps/cdk.cloud.json',
        'apps/config.cloud.json',
        'apps/container.cloud.json',
        'apps/demo.cloud.json',
        'apps/go.cloud.json',
        'apps/iam.cloud.json',
        'apps/k8s.cloud.json',
        'apps/observability.cloud.json',
        'apps/pipeline.cloud.json',
        'apps/python.cloud.json',
        'apps/terraform.cloud.json',
    ]
    assert [item.kind for item in plan.apps] == [
        'bash-script', 'cdk-stack', 'resource', 'container-image',
        'deployment-demo', 'go-service', 'iam-policy', 'k8s-manifest',
        'observability', 'ci-pipeline', 'python-service', 'terraform-module',
    ]
    demo = plan.apps[4]
    assert demo.requires == (
        'bash', 'cdk', 'container', 'go', 'iam', 'k8s', 'observability',
        'pipeline', 'python', 'terraform',
    )
    assert demo.dependencies == (
        'apps/bash.cloud.json', 'apps/cdk.cloud.json',
        'apps/container.cloud.json', 'apps/go.cloud.json',
        'apps/iam.cloud.json', 'apps/k8s.cloud.json',
        'apps/observability.cloud.json', 'apps/pipeline.cloud.json',
        'apps/python.cloud.json', 'apps/terraform.cloud.json',
    )
    assert demo.bindings == (
        'bash', 'cdk', 'container', 'drift-check', 'go', 'iam', 'k8s',
        'lockfile', 'observability', 'pipeline', 'python', 'signed-package',
        'terraform',
    )
    assert plan.build_order == (
        'apps/bash.cloud.json',
        'apps/cdk.cloud.json',
        'apps/config.cloud.json',
        'apps/container.cloud.json',
        'apps/go.cloud.json',
        'apps/iam.cloud.json',
        'apps/k8s.cloud.json',
        'apps/observability.cloud.json',
        'apps/pipeline.cloud.json',
        'apps/python.cloud.json',
        'apps/terraform.cloud.json',
        'apps/demo.cloud.json',
    )
    assert len(plan.incomplete) == 12
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
    assert payload['version'] == '3.1.61'
    assert payload['format'] == 'pea-cloud-pack'
    assert len(payload['state']) == 12


def test_changed_app_is_incomplete_and_propagates_to_demo(tmp_path):
    _write_pack(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'apps' / 'go.cloud.json').write_text(json.dumps(
        _app('go', 'go-service', ['evidence/base.txt'], [], ['go', 'v2']),
    ), encoding='utf-8')
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.apps if item.state == 'stale'] == [
        'apps/demo.cloud.json', 'apps/go.cloud.json',
    ]
    reasons = {item.path: item.reasons for item in plan.apps}
    assert reasons['apps/go.cloud.json'] == ('changed',)
    assert reasons['apps/demo.cloud.json'] == ('dependency',)
    assert reasons['apps/terraform.cloud.json'] == ()
    assert gate_v2(report_v2([plan])) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_incomplete=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['incomplete']}


def test_missing_dependency_cycle_limit_and_invalid_manifest_issues(tmp_path):
    missing_root = tmp_path / 'missing'
    (missing_root / 'evidence').mkdir(parents=True)
    (missing_root / 'evidence' / 'root.txt').write_text('ok\n',
                                                        encoding='utf-8')
    (missing_root / 'orphan.cloud.json').write_text(json.dumps(_app(
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
        (cycle_root / f'{name}.cloud.json').write_text(json.dumps(_app(
            name, 'resource', ['evidence/root.txt'], requires,
        )), encoding='utf-8')
    cyclic = plan_v2(cycle_root)
    assert [item.code for item in cyclic.issues] == ['E202']
    assert cyclic.gate == 'FAIL'
    limited = plan_v2(cycle_root, ProfileV2(max_deployments=1))
    assert 'E203' in [item.code for item in limited.issues]

    invalid_root = tmp_path / 'invalid'
    invalid_root.mkdir()
    (invalid_root / 'bad.cloud.json').write_text('{}', encoding='utf-8')
    assert [item.code for item in plan_v2(invalid_root).issues] == ['E204']


def test_missing_evidence_issue(tmp_path):
    root = tmp_path / 'evidence-root'
    root.mkdir()
    (root / 'app.cloud.json').write_text(json.dumps(_app(
        'app', 'resource', ['evidence/missing.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == ['E205']
    assert plan.gate == 'FAIL'


def test_governance_toggles(tmp_path):
    root = tmp_path / 'governance-root'
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'sample.cloud.json').write_text(json.dumps(_app(
        'sample', 'deployment-demo', ['evidence/root.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == [
        'E206', 'E207', 'E208', 'E209', 'E210', 'E211', 'E212', 'E213',
        'E214',
    ]
    assert plan.gate == 'FAIL'
    relaxed = plan_v2(root, ProfileV2(
        check_container=False, check_orchestration=False,
        check_pipeline=False, check_observability=False, check_iam=False,
        check_source=False, check_lockfile=False, check_signed=False,
        check_drift=False,
    ))
    assert relaxed.issues == ()
    assert relaxed.gate == 'PASS'
    toggles = (
        ('check_container', 'E206'),
        ('check_orchestration', 'E207'),
        ('check_pipeline', 'E208'),
        ('check_observability', 'E209'),
        ('check_iam', 'E210'),
        ('check_source', 'E211'),
        ('check_lockfile', 'E212'),
        ('check_signed', 'E213'),
        ('check_drift', 'E214'),
    )
    for field, code in toggles:
        single = plan_v2(root, ProfileV2(**{field: False}))
        codes = [item.code for item in single.issues]
        assert code not in codes
        assert len(codes) == 8


def test_preview_apps_are_skipped_until_enabled(tmp_path):
    root = tmp_path / 'preview-root'
    (root / 'preview').mkdir(parents=True)
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'preview' / 'old.cloud.json').write_text(json.dumps(_app(
        'old', 'resource', ['evidence/root.txt'],
    )), encoding='utf-8')
    assert plan_v2(root).apps == ()
    included = plan_v2(root, ProfileV2(include_preview=True))
    assert [item.path for item in included.apps] == [
        'preview/old.cloud.json',
    ]


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '3.1.61'
    assert report['format'] == 'pea-cloud-pack'
    assert report['plan_count'] == 1
    assert report['app_count'] == 12
    assert report['incomplete_count'] == 12
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
        [sys.executable, '-m', 'pealang.cli', 'cloud-pack', '--capabilities'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '3.1.61'
    project = tmp_path / 'project'
    _write_pack(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'cloud.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'cloud-pack', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '3.1.61'
    assert report['app_count'] == 12
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'cloud-pack', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['incomplete_count'] == 0
    (project / 'apps' / 'go.cloud.json').write_text(json.dumps(
        _app('go', 'go-service', ['evidence/base.txt'], [], ['go', 'v2']),
    ), encoding='utf-8')
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'cloud-pack', str(project),
         '--check', '--state', str(state_path), '--fail-on-incomplete'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['incomplete']
    minimal = tmp_path / 'minimal'
    (minimal / 'evidence').mkdir(parents=True)
    (minimal / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (minimal / 'sample.cloud.json').write_text(json.dumps(
        _app('sample', 'deployment-demo', ['evidence/root.txt']),
    ), encoding='utf-8')
    relaxed = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'cloud-pack', str(minimal),
         '--check', '--no-check-container', '--no-check-orchestration',
         '--no-check-pipeline', '--no-check-observability', '--no-check-iam',
         '--no-check-source', '--no-check-lockfile', '--no-check-signed',
         '--no-check-drift'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert relaxed.returncode == 0, relaxed.stderr
    assert json.loads(relaxed.stdout)['decision'] == {
        'gate': 'PASS', 'issues': [],
    }


def test_feature_flag_help_and_analysis_namespace_document_cloud():
    status = feature_status('sector.cloud_pack')
    assert status.stability == Stability.STABLE
    assert status.since == '3.1.61'
    text = pea_help('cloud-pack')
    assert 'pea cloud-pack' in text
    assert 'CloudProfileV2 ->' in text
    assert 'cloud_pack_gate(report)' in text
    namespace = build_cloud_pack_namespace()
    assert namespace['CLOUD_PACK_VERSION'] == '3.1.61'
    assert namespace['build_cloud_pack_namespace'] is build_cloud_pack_namespace
    analysis = build_analysis_namespace()
    for name in ('CloudProfileV2', 'CloudIssueV2', 'CloudAppV2',
                 'CloudPackPlanV2', 'PlanCloudPack', 'CloudStateV2',
                 'WriteCloudStateV2', 'CloudCapabilitiesV2', 'CloudReportV2',
                 'CloudGateV2', 'CloudNamespaceV2'):
        assert name in analysis
    assert analysis['CloudGateV2'] is gate_v2


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.14.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.14.0'
    assert manifest['previous_version'] == '5.13.0'
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
