"""Phase 86: deterministic incremental build system with stable plans."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
import pytest
from pealang.analysis import build_analysis_namespace
from pealang.build_system_v2 import (
    BUILD_SYSTEM_V2_FORMAT, BUILD_SYSTEM_V2_VERSION, DEFAULT_BUILD_PROFILE,
    BuildProfileV2 as ProfileV2, BuildSystemV2Error as SystemErrorV2,
    build_build_system_v2_namespace,
    build_system_v2_capabilities as capabilities_v2,
    build_v2_gate as gate_v2, build_v2_report as report_v2,
    load_build_state_v2 as load_state_v2, plan_build_v2 as plan_v2,
    write_build_state_v2 as write_state_v2,
)
from pealang.compatibility import Stability, feature_status
from pealang.core_freeze import core_freeze_report
from pealang.help import help as pea_help
from pealang.specification import SPEC_VERSION


def _write_project(root: Path) -> None:
    (root / 'modules').mkdir(parents=True, exist_ok=True)
    (root / 'src').mkdir(parents=True, exist_ok=True)
    (root / 'modules' / 'util.pea').write_text('print "util"\n', encoding='utf-8')
    (root / 'src' / 'app.pea').write_text(
        'import "util" as util\nprint "app"\n', encoding='utf-8',
    )


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert BUILD_SYSTEM_V2_VERSION == pealang.BUILD_SYSTEM_V2_VERSION == '3.1.49'
    assert BUILD_SYSTEM_V2_FORMAT == pealang.BUILD_SYSTEM_V2_FORMAT == 'pea-build-v2'
    assert caps == capabilities_v2()
    assert caps['version'] == '3.1.49'
    assert caps['source_filter'] == '*.pea'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert DEFAULT_BUILD_PROFILE.digest() == ProfileV2().digest()
    with pytest.raises(SystemErrorV2):
        ProfileV2(max_files=0)


def test_plan_discovers_dependencies_and_orders_build(tmp_path):
    _write_project(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.nodes] == [
        'modules/util.pea', 'src/app.pea',
    ]
    assert plan.nodes[1].dependencies == ('modules/util.pea',)
    assert plan.build_order == ('modules/util.pea', 'src/app.pea')
    assert plan.dirty == ('modules/util.pea', 'src/app.pea')
    assert plan.nodes[0].reasons == ('new',)
    assert all(item.state == 'stale' for item in plan.nodes)
    assert plan.gate == 'PASS'
    assert plan.issues == ()
    assert len(plan.digest) == 64
    assert all(len(item.fingerprint()) == 64 for item in plan.nodes)
    assert all('\\' not in item.path and ':' not in item.path
               for item in plan.nodes)


def test_state_round_trip_and_digest_ignores_host_root(tmp_path):
    _write_project(tmp_path)
    plan = plan_v2(tmp_path)
    state_path = write_state_v2(tmp_path, plan)
    state = load_state_v2(state_path)
    clean = plan_v2(tmp_path, state=state)
    assert clean.dirty == ()
    assert all(item.state == 'current' for item in clean.nodes)
    assert clean.gate == 'PASS'
    copy_root = tmp_path / 'copy'
    _write_project(copy_root)
    assert plan_v2(copy_root).digest == plan.digest
    payload = json.loads(state_path.read_text(encoding='utf-8'))
    assert payload['version'] == '3.1.49'
    assert set(payload['state']) == {'modules/util.pea', 'src/app.pea'}


def test_changed_dependency_propagates_to_dependents(tmp_path):
    _write_project(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'modules' / 'util.pea').write_text(
        'print "util changed"\n', encoding='utf-8',
    )
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.nodes if item.state == 'stale'] == [
        'modules/util.pea', 'src/app.pea',
    ]
    assert plan.nodes[1].reasons == ('dependency',)
    assert plan.dirty == ('modules/util.pea', 'src/app.pea')


def test_missing_import_cycle_and_file_limit_are_stable_errors(tmp_path):
    _write_project(tmp_path)
    (tmp_path / 'src' / 'broken.pea').write_text(
        'import "missing" as m\nprint "broken"\n', encoding='utf-8',
    )
    broken = plan_v2(tmp_path)
    assert [item.code for item in broken.issues] == ['B201']
    assert 'missing' in broken.issues[0].message
    assert broken.issues[0].path == 'src/broken.pea'
    assert broken.gate == 'FAIL'
    cycle_root = tmp_path / 'cycle'
    (cycle_root / 'modules').mkdir(parents=True)
    (cycle_root / 'modules' / 'a.pea').write_text(
        'import "b" as b\nprint "a"\n', encoding='utf-8',
    )
    (cycle_root / 'modules' / 'b.pea').write_text(
        'import "a" as a\nprint "b"\n', encoding='utf-8',
    )
    cyclic = plan_v2(cycle_root)
    assert [item.code for item in cyclic.issues] == ['B202']
    assert cyclic.issues[0].message.startswith('Dependency cycle: ')
    limited = plan_v2(tmp_path, ProfileV2(max_files=1))
    assert 'B203' in [item.code for item in limited.issues]
    assert limited.gate == 'FAIL'


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_project(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '3.1.49'
    assert report['format'] == 'pea-build-v2'
    assert report['plan_count'] == 1
    assert report['node_count'] == 2
    assert report['dirty_count'] == 2
    assert report['gate'] == 'PASS'
    assert len(report['digest']) == 64
    assert gate_v2(report) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_dirty=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['dirty']}
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
        [sys.executable, '-m', 'pealang.cli', 'build-v2', '--capabilities'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '3.1.49'
    project = tmp_path / 'project'
    _write_project(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'build.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'build-v2', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '3.1.49'
    assert report['dirty_count'] == 2
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'build-v2', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['dirty_count'] == 0
    (project / 'modules' / 'util.pea').write_text(
        'print "changed"\n', encoding='utf-8',
    )
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'build-v2', str(project),
         '--check', '--state', str(state_path), '--fail-on-dirty'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['dirty']


def test_feature_flag_help_and_analysis_namespace_document_build_system_v2():
    assert feature_status('devx.incremental_build_v2').stability == Stability.STABLE
    text = pea_help('build-v2')
    assert 'pea build-v2' in text
    assert 'BuildProfileV2 ->' in text
    namespace = build_build_system_v2_namespace()
    assert namespace['BUILD_SYSTEM_V2_VERSION'] == '3.1.49'
    assert namespace['build_build_system_v2_namespace'] is build_build_system_v2_namespace
    analysis = build_analysis_namespace()
    for name in ('BuildProfileV2', 'BuildNodeV2', 'BuildIssueV2',
                 'BuildPlanV2', 'PlanBuildV2', 'BuildStateV2',
                 'WriteBuildStateV2', 'BuildSystemCapabilitiesV2',
                 'BuildSystemReportV2', 'BuildSystemGateV2',
                 'BuildSystemNamespaceV2'):
        assert name in analysis


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.26.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.26.0'
    assert manifest['previous_version'] == '5.25.0'
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
