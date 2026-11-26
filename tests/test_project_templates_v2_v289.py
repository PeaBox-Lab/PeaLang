"""Phase 89: deterministic project template catalogs with stable gates."""

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
from pealang.specification import SPEC_VERSION
from pealang.project_templates_v2 import (DEFAULT_TEMPLATE_PROFILE,
                                          PROJECT_TEMPLATES_V2_FORMAT,
                                          PROJECT_TEMPLATES_V2_VERSION,
                                          TemplateProfileV2 as ProfileV2,
                                          ProjectTemplatesV2Error as TplErrorV2,
                                          build_project_templates_v2_namespace,
                                          templates_v2_gate as gate_v2,
                                          templates_v2_report as report_v2,
                                          load_template_state_v2 as load_state_v2,
                                          plan_project_templates_v2 as plan_v2,
                                          project_templates_v2_capabilities as capabilities_v2,
                                          write_template_state_v2 as write_state_v2)


def _write_templates(root: Path) -> None:
    (root / 'templates').mkdir(parents=True, exist_ok=True)
    (root / 'templates' / 'base.template.json').write_text(json.dumps({
        'name': 'base', 'version': '1.0.0',
        'files': ['main.pea', 'pea.toml'], 'requires': [],
        'entrypoints': ['main.pea'],
    }), encoding='utf-8')
    (root / 'templates' / 'app.template.json').write_text(json.dumps({
        'name': 'app', 'version': '1.0.0',
        'files': ['app.pea'], 'requires': ['base'],
        'entrypoints': ['app.pea'],
    }), encoding='utf-8')


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert (PROJECT_TEMPLATES_V2_VERSION
            == pealang.PROJECT_TEMPLATES_V2_VERSION == '3.1.52')
    assert (PROJECT_TEMPLATES_V2_FORMAT
            == pealang.PROJECT_TEMPLATES_V2_FORMAT == 'pea-templates-v2')
    assert caps == capabilities_v2()
    assert caps['version'] == '3.1.52'
    assert caps['source_filter'] == '*.template.json'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert DEFAULT_TEMPLATE_PROFILE.digest() == ProfileV2().digest()
    assert DEFAULT_TEMPLATE_PROFILE.effective_version() == '3.1.52'
    assert ProfileV2(current_version='9.9.9').effective_version() == '9.9.9'
    with pytest.raises(TplErrorV2):
        ProfileV2(max_templates=0)
    with pytest.raises(TplErrorV2):
        ProfileV2(current_version=1)


def test_plan_discovers_templates_and_orders_dependencies(tmp_path):
    _write_templates(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.nodes] == [
        'templates/app.template.json', 'templates/base.template.json',
    ]
    assert [item.name for item in plan.nodes] == ['app', 'base']
    assert [item.version for item in plan.nodes] == ['1.0.0', '1.0.0']
    assert plan.nodes[0].requires == ('base',)
    assert plan.nodes[0].dependencies == ('templates/base.template.json',)
    assert plan.nodes[0].entrypoints == ('app.pea',)
    assert plan.build_order == (
        'templates/base.template.json', 'templates/app.template.json',
    )
    assert len(plan.drift) == 2
    assert all(item.state == 'stale' for item in plan.nodes)
    assert plan.gate == 'PASS'
    assert plan.issues == ()
    assert len(plan.digest) == 64
    assert all(len(item.fingerprint()) == 64 for item in plan.nodes)
    assert all('\\' not in item.path and ':' not in item.path
               for item in plan.nodes)


def test_state_round_trip_and_digest_ignores_host_root(tmp_path):
    _write_templates(tmp_path)
    plan = plan_v2(tmp_path)
    state_path = write_state_v2(tmp_path, plan)
    state = load_state_v2(state_path)
    clean = plan_v2(tmp_path, state=state)
    assert clean.drift == ()
    assert all(item.state == 'current' for item in clean.nodes)
    assert all(item.reasons == () for item in clean.nodes)
    assert clean.gate == 'PASS'
    copy_root = tmp_path / 'copy'
    _write_templates(copy_root)
    assert plan_v2(copy_root).digest == plan.digest
    payload = json.loads(state_path.read_text(encoding='utf-8'))
    assert payload['version'] == '3.1.52'
    assert payload['format'] == 'pea-templates-v2'
    assert set(payload['state']) == {
        'templates/app.template.json', 'templates/base.template.json',
    }


def test_changed_template_is_drifted_and_propagates_to_dependents(tmp_path):
    _write_templates(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'templates' / 'base.template.json').write_text(json.dumps({
        'name': 'base', 'version': '1.0.0',
        'files': ['main.pea', 'pea.toml'], 'requires': [],
        'entrypoints': ['main.pea'], 'extra': 'changed',
    }), encoding='utf-8')
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.nodes if item.state == 'stale'] == [
        'templates/app.template.json', 'templates/base.template.json',
    ]
    assert [item.reasons for item in plan.nodes] == [
        ('dependency',), ('changed',),
    ]
    assert plan.drift == (
        'templates/app.template.json', 'templates/base.template.json',
    )
    assert gate_v2(report_v2([plan])) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_drift=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['drift']}


def test_missing_dependency_cycle_limit_and_manifest_issues_are_stable(tmp_path):
    missing_root = tmp_path / 'missing'
    missing_root.mkdir()
    (missing_root / 'orphan.template.json').write_text(json.dumps({
        'name': 'orphan', 'version': '1.0.0',
        'files': ['orphan.pea'], 'requires': ['absent'],
        'entrypoints': [],
    }), encoding='utf-8')
    broken = plan_v2(missing_root)
    assert [item.code for item in broken.issues] == ['T201']
    assert 'absent' in broken.issues[0].message
    assert broken.gate == 'FAIL'
    no_check = plan_v2(missing_root, ProfileV2(check_dependencies=False))
    assert no_check.issues == ()
    assert no_check.gate == 'PASS'

    cycle_root = tmp_path / 'cycle'
    (cycle_root / 'templates').mkdir(parents=True)
    (cycle_root / 'templates' / 'a.template.json').write_text(json.dumps({
        'name': 'a', 'version': '1.0.0',
        'files': ['a.pea'], 'requires': ['b'], 'entrypoints': [],
    }), encoding='utf-8')
    (cycle_root / 'templates' / 'b.template.json').write_text(json.dumps({
        'name': 'b', 'version': '1.0.0',
        'files': ['b.pea'], 'requires': ['a'], 'entrypoints': [],
    }), encoding='utf-8')
    cyclic = plan_v2(cycle_root)
    assert [item.code for item in cyclic.issues] == ['T202']
    assert cyclic.gate == 'FAIL'

    limited = plan_v2(cycle_root, ProfileV2(max_templates=1))
    assert 'T203' in [item.code for item in limited.issues]
    assert limited.gate == 'FAIL'

    invalid_root = tmp_path / 'invalid'
    invalid_root.mkdir()
    (invalid_root / 'bad.template.json').write_text('{}', encoding='utf-8')
    invalid = plan_v2(invalid_root)
    assert [item.code for item in invalid.issues] == ['T204']

    entry_root = tmp_path / 'entry'
    entry_root.mkdir()
    (entry_root / 'app.template.json').write_text(json.dumps({
        'name': 'app', 'version': '1.0.0',
        'files': ['app.pea'], 'requires': [],
        'entrypoints': ['missing.pea'],
    }), encoding='utf-8')
    bad_entry = plan_v2(entry_root)
    assert [item.code for item in bad_entry.issues] == ['T205']


def test_community_templates_are_skipped_until_enabled(tmp_path):
    community_root = tmp_path / 'community-root'
    (community_root / 'community').mkdir(parents=True)
    (community_root / 'community' / 'old.template.json').write_text(json.dumps({
        'name': 'old', 'version': '1.0.0',
        'files': ['old.pea'], 'requires': [], 'entrypoints': [],
    }), encoding='utf-8')
    assert plan_v2(community_root).nodes == ()
    included = plan_v2(community_root, ProfileV2(include_community=True))
    assert [item.path for item in included.nodes] == [
        'community/old.template.json',
    ]


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_templates(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '3.1.52'
    assert report['format'] == 'pea-templates-v2'
    assert report['plan_count'] == 1
    assert report['template_count'] == 2
    assert report['drift_count'] == 2
    assert report['error_count'] == 0
    assert report['gate'] == 'PASS'
    assert len(report['digest']) == 64
    assert gate_v2(report) == {'gate': 'PASS', 'issues': []}
    assert 'version' in gate_v2({**report, 'version': 'old'})['issues']
    assert 'format' in gate_v2({**report, 'format': 'old'})['issues']
    assert 'digest' in gate_v2({**report, 'digest': '0' * 64})['issues']
    assert 'counts' in gate_v2({**report, 'template_count': 99})['issues']
    tampered = json.loads(json.dumps(report))
    tampered['plans'][0]['nodes'][0]['fingerprint'] = '0' * 64
    assert 'node_fingerprint' in gate_v2(tampered)['issues']


def test_cli_capabilities_check_emit_state_and_strict_gate(tmp_path):
    root = Path(__file__).resolve().parent.parent
    caps = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'templates-v2', '--capabilities'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '3.1.52'
    project = tmp_path / 'project'
    _write_templates(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'templates.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'templates-v2', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '3.1.52'
    assert report['template_count'] == 2
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'templates-v2', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['drift_count'] == 0
    (project / 'templates' / 'base.template.json').write_text(json.dumps({
        'name': 'base', 'version': '1.0.0',
        'files': ['main.pea', 'pea.toml'], 'requires': [],
        'entrypoints': ['main.pea'], 'extra': 'changed',
    }), encoding='utf-8')
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'templates-v2', str(project),
         '--check', '--state', str(state_path), '--fail-on-drift'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['drift']


def test_feature_flag_help_and_analysis_namespace_document_templates():
    status = feature_status('devx.project_templates_v2')
    assert status.stability == Stability.STABLE
    assert status.since == '3.1.52'
    text = pea_help('templates-v2')
    assert 'pea templates-v2' in text
    assert 'TemplateProfileV2 ->' in text
    assert 'templates_v2_gate(report)' in text
    namespace = build_project_templates_v2_namespace()
    assert namespace['PROJECT_TEMPLATES_V2_VERSION'] == '3.1.52'
    assert (namespace['build_project_templates_v2_namespace']
            is build_project_templates_v2_namespace)
    analysis = build_analysis_namespace()
    for name in ('TemplateProfileV2', 'TemplateIssueV2', 'TemplateNodeV2',
                 'TemplatePlanV2', 'PlanProjectTemplatesV2',
                 'TemplateStateV2', 'WriteTemplateStateV2',
                 'TemplateCapabilitiesV2', 'TemplateReportV2',
                 'TemplateGateV2', 'TemplateNamespaceV2'):
        assert name in analysis
    assert analysis['TemplateGateV2'] is gate_v2


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.5.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.5.0'
    assert manifest['previous_version'] == '5.4.0'
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
