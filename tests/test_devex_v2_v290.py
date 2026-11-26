"""Phase 90: deterministic developer-experience evidence with stable gates."""

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
from pealang.devex_v2 import (DEFAULT_DEVEX_PROFILE, DEVEX_V2_FORMAT,
                              DEVEX_V2_VERSION, DevExProfileV2 as ProfileV2,
                              DevExV2Error, build_devex_v2_namespace,
                              devex_v2_capabilities as capabilities_v2,
                              devex_v2_gate as gate_v2,
                              devex_v2_report as report_v2,
                              load_devex_state_v2 as load_state_v2,
                              plan_devex_v2 as plan_v2,
                              write_devex_state_v2 as write_state_v2)


def _write_tools(root: Path) -> None:
    (root / 'tools').mkdir(parents=True, exist_ok=True)
    (root / 'evidence').mkdir(parents=True, exist_ok=True)
    (root / 'evidence' / 'base.txt').write_text('base evidence\n',
                                                encoding='utf-8')
    (root / 'evidence' / 'app.txt').write_text('app evidence\n',
                                               encoding='utf-8')
    (root / 'tools' / 'base.devx.json').write_text(json.dumps({
        'name': 'base', 'version': '1.0.0', 'format': 'pea-build',
        'evidence': ['evidence/base.txt'], 'requires': [], 'checks': ['parity'],
    }), encoding='utf-8')
    (root / 'tools' / 'app.devx.json').write_text(json.dumps({
        'name': 'app', 'version': '1.0.0', 'format': 'pea-test',
        'evidence': ['evidence/app.txt'], 'requires': ['base'], 'checks': ['gate'],
    }), encoding='utf-8')


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert DEVEX_V2_VERSION == pealang.DEVEX_V2_VERSION == '3.1.53'
    assert DEVEX_V2_FORMAT == pealang.DEVEX_V2_FORMAT == 'pea-devx-v2'
    assert caps == capabilities_v2()
    assert caps['version'] == '3.1.53'
    assert caps['source_filter'] == '*.devx.json'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert DEFAULT_DEVEX_PROFILE.digest() == ProfileV2().digest()
    assert DEFAULT_DEVEX_PROFILE.effective_version() == '3.1.53'
    assert ProfileV2(current_version='9.9.9').effective_version() == '9.9.9'
    with pytest.raises(DevExV2Error):
        ProfileV2(max_tools=0)
    with pytest.raises(DevExV2Error):
        ProfileV2(current_version=1)


def test_plan_discovers_tools_and_orders_dependencies(tmp_path):
    _write_tools(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.tools] == [
        'tools/app.devx.json', 'tools/base.devx.json',
    ]
    assert [item.name for item in plan.tools] == ['app', 'base']
    assert [item.format for item in plan.tools] == ['pea-test', 'pea-build']
    assert plan.tools[0].requires == ('base',)
    assert plan.tools[0].dependencies == ('tools/base.devx.json',)
    assert plan.tools[0].evidence == ('evidence/app.txt',)
    assert plan.tools[0].checks == ('gate',)
    assert plan.build_order == (
        'tools/base.devx.json', 'tools/app.devx.json',
    )
    assert len(plan.incomplete) == 2
    assert all(item.state == 'stale' for item in plan.tools)
    assert plan.gate == 'PASS'
    assert plan.issues == ()
    assert len(plan.digest) == 64
    assert all(len(item.fingerprint()) == 64 for item in plan.tools)
    assert all('\\' not in item.path and ':' not in item.path
               for item in plan.tools)


def test_state_round_trip_and_digest_ignores_host_root(tmp_path):
    _write_tools(tmp_path)
    plan = plan_v2(tmp_path)
    state_path = write_state_v2(tmp_path, plan)
    state = load_state_v2(state_path)
    clean = plan_v2(tmp_path, state=state)
    assert clean.incomplete == ()
    assert all(item.state == 'current' for item in clean.tools)
    assert all(item.reasons == () for item in clean.tools)
    assert clean.gate == 'PASS'
    copy_root = tmp_path / 'copy'
    _write_tools(copy_root)
    assert plan_v2(copy_root).digest == plan.digest
    payload = json.loads(state_path.read_text(encoding='utf-8'))
    assert payload['version'] == '3.1.53'
    assert payload['format'] == 'pea-devx-v2'
    assert set(payload['state']) == {
        'tools/app.devx.json', 'tools/base.devx.json',
    }


def test_changed_tool_is_incomplete_and_propagates_to_dependents(tmp_path):
    _write_tools(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'tools' / 'base.devx.json').write_text(json.dumps({
        'name': 'base', 'version': '1.0.0', 'format': 'pea-build',
        'evidence': ['evidence/base.txt'], 'requires': [],
        'checks': ['parity'], 'extra': 'changed',
    }), encoding='utf-8')
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.tools if item.state == 'stale'] == [
        'tools/app.devx.json', 'tools/base.devx.json',
    ]
    assert [item.reasons for item in plan.tools] == [
        ('dependency',), ('changed',),
    ]
    assert plan.incomplete == (
        'tools/app.devx.json', 'tools/base.devx.json',
    )
    assert gate_v2(report_v2([plan])) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_incomplete=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['incomplete']}


def test_missing_dependency_cycle_limit_manifest_and_evidence_issues(tmp_path):
    missing_root = tmp_path / 'missing'
    (missing_root / 'evidence').mkdir(parents=True)
    (missing_root / 'evidence' / 'root.txt').write_text('ok\n',
                                                        encoding='utf-8')
    (missing_root / 'orphan.devx.json').write_text(json.dumps({
        'name': 'orphan', 'version': '1.0.0', 'format': 'pea-test',
        'evidence': ['evidence/root.txt'], 'requires': ['absent'], 'checks': [],
    }), encoding='utf-8')
    broken = plan_v2(missing_root)
    assert [item.code for item in broken.issues] == ['D201']
    assert 'absent' in broken.issues[0].message
    assert broken.gate == 'FAIL'
    no_check = plan_v2(missing_root, ProfileV2(check_evidence=False))
    assert no_check.issues == ()
    assert no_check.gate == 'PASS'

    cycle_root = tmp_path / 'cycle'
    (cycle_root / 'tools').mkdir(parents=True)
    (cycle_root / 'evidence').mkdir(parents=True)
    (cycle_root / 'evidence' / 'root.txt').write_text('ok\n',
                                                      encoding='utf-8')
    (cycle_root / 'tools' / 'a.devx.json').write_text(json.dumps({
        'name': 'a', 'version': '1.0.0', 'format': 'pea-test',
        'evidence': ['evidence/root.txt'], 'requires': ['b'], 'checks': [],
    }), encoding='utf-8')
    (cycle_root / 'tools' / 'b.devx.json').write_text(json.dumps({
        'name': 'b', 'version': '1.0.0', 'format': 'pea-test',
        'evidence': ['evidence/root.txt'], 'requires': ['a'], 'checks': [],
    }), encoding='utf-8')
    cyclic = plan_v2(cycle_root)
    assert [item.code for item in cyclic.issues] == ['D202']
    assert cyclic.gate == 'FAIL'

    limited = plan_v2(cycle_root, ProfileV2(max_tools=1))
    assert 'D203' in [item.code for item in limited.issues]
    assert limited.gate == 'FAIL'

    invalid_root = tmp_path / 'invalid'
    invalid_root.mkdir()
    (invalid_root / 'bad.devx.json').write_text('{}', encoding='utf-8')
    assert [item.code for item in plan_v2(invalid_root).issues] == ['D204']

    evidence_root = tmp_path / 'evidence-root'
    evidence_root.mkdir()
    (evidence_root / 'app.devx.json').write_text(json.dumps({
        'name': 'app', 'version': '1.0.0', 'format': 'pea-test',
        'evidence': ['evidence/missing.txt'], 'requires': [], 'checks': [],
    }), encoding='utf-8')
    missing_evidence = plan_v2(evidence_root)
    assert [item.code for item in missing_evidence.issues] == ['D205']


def test_experimental_tools_are_skipped_until_enabled(tmp_path):
    experimental_root = tmp_path / 'experimental-root'
    (experimental_root / 'experimental').mkdir(parents=True)
    (experimental_root / 'evidence').mkdir(parents=True)
    (experimental_root / 'evidence' / 'root.txt').write_text('ok\n',
                                                             encoding='utf-8')
    (experimental_root / 'experimental' / 'old.devx.json').write_text(
        json.dumps({
            'name': 'old', 'version': '1.0.0', 'format': 'pea-test',
            'evidence': ['evidence/root.txt'], 'requires': [], 'checks': [],
        }), encoding='utf-8',
    )
    assert plan_v2(experimental_root).tools == ()
    included = plan_v2(experimental_root,
                       ProfileV2(include_experimental=True))
    assert [item.path for item in included.tools] == [
        'experimental/old.devx.json',
    ]


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_tools(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '3.1.53'
    assert report['format'] == 'pea-devx-v2'
    assert report['plan_count'] == 1
    assert report['tool_count'] == 2
    assert report['incomplete_count'] == 2
    assert report['error_count'] == 0
    assert report['gate'] == 'PASS'
    assert len(report['digest']) == 64
    assert gate_v2(report) == {'gate': 'PASS', 'issues': []}
    assert 'version' in gate_v2({**report, 'version': 'old'})['issues']
    assert 'format' in gate_v2({**report, 'format': 'old'})['issues']
    assert 'digest' in gate_v2({**report, 'digest': '0' * 64})['issues']
    assert 'counts' in gate_v2({**report, 'tool_count': 99})['issues']
    tampered = json.loads(json.dumps(report))
    tampered['plans'][0]['tools'][0]['fingerprint'] = '0' * 64
    assert 'tool_fingerprint' in gate_v2(tampered)['issues']


def test_cli_capabilities_check_emit_state_and_strict_gate(tmp_path):
    root = Path(__file__).resolve().parent.parent
    caps = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'devex-v2', '--capabilities'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '3.1.53'
    project = tmp_path / 'project'
    _write_tools(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'devex.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'devex-v2', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '3.1.53'
    assert report['tool_count'] == 2
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'devex-v2', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['incomplete_count'] == 0
    (project / 'tools' / 'base.devx.json').write_text(json.dumps({
        'name': 'base', 'version': '1.0.0', 'format': 'pea-build',
        'evidence': ['evidence/base.txt'], 'requires': [],
        'checks': ['parity'], 'extra': 'changed',
    }), encoding='utf-8')
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'devex-v2', str(project),
         '--check', '--state', str(state_path), '--fail-on-incomplete'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['incomplete']


def test_feature_flag_help_and_analysis_namespace_document_devex():
    status = feature_status('devx.devex_v2')
    assert status.stability == Stability.STABLE
    assert status.since == '3.1.53'
    text = pea_help('devex-v2')
    assert 'pea devex-v2' in text
    assert 'DevExProfileV2 ->' in text
    assert 'devex_v2_gate(report)' in text
    namespace = build_devex_v2_namespace()
    assert namespace['DEVEX_V2_VERSION'] == '3.1.53'
    assert namespace['build_devex_v2_namespace'] is build_devex_v2_namespace
    analysis = build_analysis_namespace()
    for name in ('DevExProfileV2', 'DevExIssueV2', 'DevExToolV2',
                 'DevExPlanV2', 'PlanDevExV2', 'DevExStateV2',
                 'WriteDevExStateV2', 'DevExCapabilitiesV2',
                 'DevExReportV2', 'DevExGateV2', 'DevExNamespaceV2'):
        assert name in analysis
    assert analysis['DevExGateV2'] is gate_v2


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.0.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.0.0'
    assert manifest['previous_version'] == '3.1.62'
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
