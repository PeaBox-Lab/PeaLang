"""Phase 88: deterministic migration assistants with stable gates."""

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
from pealang.migration_assistants import (DEFAULT_MIGRATION_PROFILE,
                                          MIGRATION_ASSISTANTS_FORMAT,
                                          MIGRATION_ASSISTANTS_VERSION,
                                          MigrationProfileV2 as ProfileV2,
                                          MigrationAssistantError as MigErrorV2,
                                          build_migration_assistants_namespace,
                                          migration_v2_gate as gate_v2,
                                          migration_v2_report as report_v2,
                                          load_migration_state_v2 as load_state_v2,
                                          plan_migration_v2 as plan_v2,
                                          migration_assistants_capabilities as capabilities_v2,
                                          write_migration_state_v2 as write_state_v2)


def _write_migrations(root: Path) -> None:
    (root / 'migrations').mkdir(parents=True, exist_ok=True)
    (root / 'migrations' / 'base.migration').write_text(
        'def base() { print "base" }\n', encoding='utf-8',
    )
    (root / 'migrations' / 'app.migration').write_text(
        'import "base"\ndef app() { print "app" }\n', encoding='utf-8',
    )


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert (MIGRATION_ASSISTANTS_VERSION
            == pealang.MIGRATION_ASSISTANTS_VERSION == '3.1.51')
    assert (MIGRATION_ASSISTANTS_FORMAT
            == pealang.MIGRATION_ASSISTANTS_FORMAT == 'pea-migrate-v2')
    assert caps == capabilities_v2()
    assert caps['version'] == '3.1.51'
    assert caps['source_filter'] == '*.migration'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert DEFAULT_MIGRATION_PROFILE.digest() == ProfileV2().digest()
    assert DEFAULT_MIGRATION_PROFILE.effective_version() == '3.1.51'
    assert ProfileV2(current_version='9.9.9').effective_version() == '9.9.9'
    with pytest.raises(MigErrorV2):
        ProfileV2(max_migrations=0)
    with pytest.raises(MigErrorV2):
        ProfileV2(current_version=1)


def test_plan_discovers_scripts_and_orders_migrations(tmp_path):
    _write_migrations(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.nodes] == [
        'migrations/app.migration', 'migrations/base.migration',
    ]
    assert [item.scripts for item in plan.nodes] == [('app',), ('base',)]
    assert plan.nodes[0].imports == ('base',)
    assert plan.nodes[0].dependencies == ('migrations/base.migration',)
    assert plan.build_order == (
        'migrations/base.migration', 'migrations/app.migration',
    )
    assert len(plan.dirty) == 2
    assert all(item.state == 'stale' for item in plan.nodes)
    assert plan.gate == 'PASS'
    assert plan.issues == ()
    assert len(plan.digest) == 64
    assert all(len(item.fingerprint()) == 64 for item in plan.nodes)
    assert all('\\' not in item.path and ':' not in item.path
               for item in plan.nodes)


def test_state_round_trip_and_digest_ignores_host_root(tmp_path):
    _write_migrations(tmp_path)
    plan = plan_v2(tmp_path)
    state_path = write_state_v2(tmp_path, plan)
    state = load_state_v2(state_path)
    clean = plan_v2(tmp_path, state=state)
    assert clean.dirty == ()
    assert all(item.state == 'current' for item in clean.nodes)
    assert all(item.reasons == () for item in clean.nodes)
    assert clean.gate == 'PASS'
    copy_root = tmp_path / 'copy'
    _write_migrations(copy_root)
    assert plan_v2(copy_root).digest == plan.digest
    payload = json.loads(state_path.read_text(encoding='utf-8'))
    assert payload['version'] == '3.1.51'
    assert payload['format'] == 'pea-migrate-v2'
    assert set(payload['state']) == {
        'migrations/app.migration', 'migrations/base.migration',
    }


def test_changed_migration_is_dirty_and_propagates_to_dependents(tmp_path):
    _write_migrations(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'migrations' / 'base.migration').write_text(
        'def base() { print "changed" }\n', encoding='utf-8',
    )
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.nodes if item.state == 'stale'] == [
        'migrations/app.migration', 'migrations/base.migration',
    ]
    assert [item.reasons for item in plan.nodes] == [
        ('dependency',), ('changed',),
    ]
    assert plan.dirty == (
        'migrations/app.migration', 'migrations/base.migration',
    )
    assert gate_v2(report_v2([plan])) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_dirty=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['dirty']}


def test_missing_script_cycle_history_and_file_limit_are_stable_errors(tmp_path):
    missing_root = tmp_path / 'missing'
    missing_root.mkdir()
    (missing_root / 'orphan.migration').write_text(
        'import "absent"\n', encoding='utf-8',
    )
    broken = plan_v2(missing_root)
    assert [item.code for item in broken.issues] == ['M201']
    assert 'absent' in broken.issues[0].message
    assert broken.gate == 'FAIL'
    no_check = plan_v2(missing_root, ProfileV2(check_imports=False))
    assert no_check.issues == ()
    assert no_check.gate == 'PASS'

    cycle_root = tmp_path / 'cycle'
    (cycle_root / 'migrations').mkdir(parents=True)
    (cycle_root / 'migrations' / 'a.migration').write_text(
        'import "b"\ndef a() { }\n', encoding='utf-8',
    )
    (cycle_root / 'migrations' / 'b.migration').write_text(
        'import "a"\ndef b() { }\n', encoding='utf-8',
    )
    cyclic = plan_v2(cycle_root)
    assert [item.code for item in cyclic.issues] == ['M202']
    assert cyclic.gate == 'FAIL'

    history_root = tmp_path / 'history'
    (history_root / 'releases').mkdir(parents=True)
    (history_root / 'releases' / 'old.migration').write_text(
        'def old() { }\n', encoding='utf-8',
    )
    assert plan_v2(history_root).nodes == ()
    included = plan_v2(history_root, ProfileV2(include_test_migrations=True))
    assert [item.path for item in included.nodes] == [
        'releases/old.migration',
    ]
    limited = plan_v2(cycle_root, ProfileV2(max_migrations=1))
    assert 'M203' in [item.code for item in limited.issues]
    assert limited.gate == 'FAIL'


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_migrations(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '3.1.51'
    assert report['format'] == 'pea-migrate-v2'
    assert report['plan_count'] == 1
    assert report['node_count'] == 2
    assert report['dirty_count'] == 2
    assert report['error_count'] == 0
    assert report['gate'] == 'PASS'
    assert len(report['digest']) == 64
    assert gate_v2(report) == {'gate': 'PASS', 'issues': []}
    assert 'version' in gate_v2({**report, 'version': 'old'})['issues']
    assert 'format' in gate_v2({**report, 'format': 'old'})['issues']
    assert 'digest' in gate_v2({**report, 'digest': '0' * 64})['issues']
    assert 'counts' in gate_v2({**report, 'node_count': 99})['issues']
    tampered = json.loads(json.dumps(report))
    tampered['plans'][0]['nodes'][0]['fingerprint'] = '0' * 64
    assert 'node_fingerprint' in gate_v2(tampered)['issues']


def test_cli_capabilities_check_emit_state_and_strict_gate(tmp_path):
    root = Path(__file__).resolve().parent.parent
    caps = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'migrate-v2', '--capabilities'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '3.1.51'
    project = tmp_path / 'project'
    _write_migrations(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'migrate.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'migrate-v2', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '3.1.51'
    assert report['node_count'] == 2
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'migrate-v2', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['dirty_count'] == 0
    (project / 'migrations' / 'base.migration').write_text(
        'def base() { print "changed" }\n', encoding='utf-8',
    )
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'migrate-v2', str(project),
         '--check', '--state', str(state_path), '--fail-on-dirty'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['dirty']


def test_feature_flag_help_and_analysis_namespace_document_migration_assistants():
    assert feature_status('devx.migration_assistants').stability == Stability.STABLE
    text = pea_help('migrate-v2')
    assert 'pea migrate-v2' in text
    assert 'MigrationProfileV2 ->' in text
    assert 'migration_v2_gate(report)' in text
    namespace = build_migration_assistants_namespace()
    assert namespace['MIGRATION_ASSISTANTS_VERSION'] == '3.1.51'
    assert (namespace['build_migration_assistants_namespace']
            is build_migration_assistants_namespace)
    analysis = build_analysis_namespace()
    for name in ('MigrationProfileV2', 'MigrationIssueV2', 'MigrationNodeV2',
                 'MigrationPlanV2', 'PlanMigrationV2', 'MigrationStateV2',
                 'WriteMigrationStateV2', 'MigrationCapabilitiesV2',
                 'MigrationReportV2', 'MigrationGateV2',
                 'MigrationNamespaceV2'):
        assert name in analysis
    assert analysis['MigrationGateV2'] is gate_v2


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.19.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.19.0'
    assert manifest['previous_version'] == '5.18.0'
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
