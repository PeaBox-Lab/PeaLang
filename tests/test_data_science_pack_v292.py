"""Phase 92: deterministic Data Science / AI / ML sector-pack evidence."""

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
from pealang.data_science_pack import (DATA_KINDS, DATA_PACK_FORMAT,
                                       DATA_PACK_VERSION, DataPackError,
                                       DEFAULT_DATA_PROFILE,
                                       DataProfileV2 as ProfileV2,
                                       build_data_pack_namespace,
                                       data_pack_capabilities as capabilities_v2,
                                       data_pack_gate as gate_v2,
                                       data_pack_report as report_v2,
                                       load_data_state_v2 as load_state_v2,
                                       plan_data_pack as plan_v2,
                                       write_data_state_v2 as write_state_v2)


def _workflow(name, kind, evidence, requires=(), metrics=()):
    return {
        'name': name, 'version': '1.0.0', 'kind': kind,
        'evidence': list(evidence), 'requires': list(requires),
        'metrics': list(metrics),
    }


def _write_pack(root: Path) -> None:
    for folder in ('workflows', 'evidence'):
        (root / folder).mkdir(parents=True, exist_ok=True)
    for name in ('base.txt', 'series.txt', 'model.txt'):
        (root / 'evidence' / name).write_text(name + '\n', encoding='utf-8')
    items = {
        'workflows/bench.ds.json': _workflow(
            'bench', 'benchmark', ['evidence/model.txt'], [], ['latency<50ms']),
        'workflows/forecast.ds.json': _workflow(
            'forecast', 'pipeline', ['evidence/series.txt'],
            ['series', 'parity'], ['mape<=0.1']),
        'workflows/model.ds.json': _workflow(
            'model', 'model', ['evidence/model.txt'], ['forecast', 'bench'],
            ['auc>=0.9']),
        'workflows/parity.ds.json': _workflow(
            'parity', 'parity-suite', ['evidence/base.txt'], [], ['rows=1000']),
        'workflows/series.ds.json': _workflow(
            'series', 'dataset', ['evidence/base.txt'], [], ['rows=10000']),
        'workflows/serve.ds.json': _workflow(
            'serve', 'serving-endpoint', ['evidence/base.txt'], ['model']),
    }
    for rel, payload in items.items():
        (root / rel).write_text(json.dumps(payload), encoding='utf-8')


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert DATA_PACK_VERSION == pealang.DATA_PACK_VERSION == '3.1.55'
    assert DATA_PACK_FORMAT == pealang.DATA_PACK_FORMAT == 'pea-ds-pack'
    assert caps == capabilities_v2()
    assert caps['version'] == '3.1.55'
    assert caps['source_filter'] == '*.ds.json'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert caps['kinds'] == sorted(DATA_KINDS)
    assert DEFAULT_DATA_PROFILE.digest() == ProfileV2().digest()
    assert DEFAULT_DATA_PROFILE.effective_version() == '3.1.55'
    assert ProfileV2(current_version='9.9.9').effective_version() == '9.9.9'
    with pytest.raises(DataPackError):
        ProfileV2(max_workflows=0)
    with pytest.raises(DataPackError):
        ProfileV2(current_version=1)


def test_plan_discovers_workflows_and_orders_dependencies(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.workflows] == [
        'workflows/bench.ds.json',
        'workflows/forecast.ds.json',
        'workflows/model.ds.json',
        'workflows/parity.ds.json',
        'workflows/series.ds.json',
        'workflows/serve.ds.json',
    ]
    assert [item.kind for item in plan.workflows] == [
        'benchmark', 'pipeline', 'model', 'parity-suite', 'dataset',
        'serving-endpoint',
    ]
    assert plan.workflows[1].requires == ('parity', 'series')
    assert plan.workflows[1].dependencies == (
        'workflows/parity.ds.json', 'workflows/series.ds.json',
    )
    assert plan.workflows[0].metrics == ('latency<50ms',)
    assert plan.build_order == (
        'workflows/bench.ds.json',
        'workflows/parity.ds.json',
        'workflows/series.ds.json',
        'workflows/forecast.ds.json',
        'workflows/model.ds.json',
        'workflows/serve.ds.json',
    )
    assert len(plan.incomplete) == 6
    assert all(item.state == 'stale' for item in plan.workflows)
    assert plan.gate == 'PASS'
    assert plan.issues == ()
    assert len(plan.digest) == 64
    assert all(len(item.fingerprint()) == 64 for item in plan.workflows)
    assert all('\\' not in item.path and ':' not in item.path
               for item in plan.workflows)


def test_state_round_trip_and_digest_ignores_host_root(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    state_path = write_state_v2(tmp_path, plan)
    state = load_state_v2(state_path)
    clean = plan_v2(tmp_path, state=state)
    assert clean.incomplete == ()
    assert all(item.state == 'current' for item in clean.workflows)
    assert all(item.reasons == () for item in clean.workflows)
    assert clean.gate == 'PASS'
    copy_root = tmp_path / 'copy'
    _write_pack(copy_root)
    assert plan_v2(copy_root).digest == plan.digest
    payload = json.loads(state_path.read_text(encoding='utf-8'))
    assert payload['version'] == '3.1.55'
    assert payload['format'] == 'pea-ds-pack'
    assert len(payload['state']) == 6


def test_changed_workflow_is_incomplete_and_propagates_to_dependents(tmp_path):
    _write_pack(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'workflows' / 'series.ds.json').write_text(json.dumps(
        _workflow('series', 'dataset', ['evidence/base.txt'], [],
                  ['rows=20000']),
    ), encoding='utf-8')
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.workflows if item.state == 'stale'] == [
        'workflows/forecast.ds.json',
        'workflows/model.ds.json',
        'workflows/series.ds.json',
        'workflows/serve.ds.json',
    ]
    reasons = {item.path: item.reasons for item in plan.workflows}
    assert reasons['workflows/series.ds.json'] == ('changed',)
    assert reasons['workflows/forecast.ds.json'] == ('dependency',)
    assert reasons['workflows/model.ds.json'] == ('dependency',)
    assert reasons['workflows/serve.ds.json'] == ('dependency',)
    assert reasons['workflows/parity.ds.json'] == ()
    assert gate_v2(report_v2([plan])) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_incomplete=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['incomplete']}


def test_missing_dependency_cycle_limit_and_invalid_manifest_issues(tmp_path):
    missing_root = tmp_path / 'missing'
    (missing_root / 'evidence').mkdir(parents=True)
    (missing_root / 'evidence' / 'root.txt').write_text('ok\n',
                                                        encoding='utf-8')
    (missing_root / 'orphan.ds.json').write_text(json.dumps(_workflow(
        'orphan', 'dataset', ['evidence/root.txt'], ['absent'],
    )), encoding='utf-8')
    broken = plan_v2(missing_root)
    assert [item.code for item in broken.issues] == ['S201']
    assert 'absent' in broken.issues[0].message
    assert broken.gate == 'FAIL'

    cycle_root = tmp_path / 'cycle'
    (cycle_root / 'evidence').mkdir(parents=True)
    (cycle_root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    for name, requires in (('a', ['b']), ('b', ['a'])):
        (cycle_root / f'{name}.ds.json').write_text(json.dumps(_workflow(
            name, 'dataset', ['evidence/root.txt'], requires,
        )), encoding='utf-8')
    cyclic = plan_v2(cycle_root)
    assert [item.code for item in cyclic.issues] == ['S202']
    assert cyclic.gate == 'FAIL'
    limited = plan_v2(cycle_root, ProfileV2(max_workflows=1))
    assert 'S203' in [item.code for item in limited.issues]

    invalid_root = tmp_path / 'invalid'
    invalid_root.mkdir()
    (invalid_root / 'bad.ds.json').write_text('{}', encoding='utf-8')
    assert [item.code for item in plan_v2(invalid_root).issues] == ['S204']


def test_missing_evidence_issue(tmp_path):
    root = tmp_path / 'evidence-root'
    root.mkdir()
    (root / 'app.ds.json').write_text(json.dumps(_workflow(
        'app', 'dataset', ['evidence/missing.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == ['S205']
    assert plan.gate == 'FAIL'


def test_parity_and_benchmark_governance_issues_and_toggles(tmp_path):
    root = tmp_path / 'governance-root'
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'flow.ds.json').write_text(json.dumps(_workflow(
        'flow', 'pipeline', ['evidence/root.txt'],
    )), encoding='utf-8')
    (root / 'net.ds.json').write_text(json.dumps(_workflow(
        'net', 'model', ['evidence/root.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == ['S206', 'S207']
    assert plan.gate == 'FAIL'
    relaxed = plan_v2(root, ProfileV2(check_parity=False,
                                      check_benchmarks=False))
    assert relaxed.issues == ()
    assert relaxed.gate == 'PASS'
    parity_off = plan_v2(root, ProfileV2(check_parity=False))
    assert [item.code for item in parity_off.issues] == ['S207']
    benchmark_off = plan_v2(root, ProfileV2(check_benchmarks=False))
    assert [item.code for item in benchmark_off.issues] == ['S206']


def test_preview_workflows_are_skipped_until_enabled(tmp_path):
    root = tmp_path / 'preview-root'
    (root / 'preview').mkdir(parents=True)
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'preview' / 'old.ds.json').write_text(json.dumps(_workflow(
        'old', 'dataset', ['evidence/root.txt'],
    )), encoding='utf-8')
    assert plan_v2(root).workflows == ()
    included = plan_v2(root, ProfileV2(include_preview=True))
    assert [item.path for item in included.workflows] == [
        'preview/old.ds.json',
    ]


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '3.1.55'
    assert report['format'] == 'pea-ds-pack'
    assert report['plan_count'] == 1
    assert report['workflow_count'] == 6
    assert report['incomplete_count'] == 6
    assert report['error_count'] == 0
    assert report['gate'] == 'PASS'
    assert len(report['digest']) == 64
    assert gate_v2(report) == {'gate': 'PASS', 'issues': []}
    assert 'version' in gate_v2({**report, 'version': 'old'})['issues']
    assert 'format' in gate_v2({**report, 'format': 'old'})['issues']
    assert 'digest' in gate_v2({**report, 'digest': '0' * 64})['issues']
    assert 'counts' in gate_v2({**report, 'workflow_count': 99})['issues']
    tampered = json.loads(json.dumps(report))
    tampered['plans'][0]['workflows'][0]['fingerprint'] = '0' * 64
    assert 'workflow_fingerprint' in gate_v2(tampered)['issues']


def test_cli_capabilities_check_emit_state_and_strict_gate(tmp_path):
    project_root = Path(__file__).resolve().parent.parent
    caps = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'data-pack', '--capabilities'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '3.1.55'
    project = tmp_path / 'project'
    _write_pack(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'data.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'data-pack', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '3.1.55'
    assert report['workflow_count'] == 6
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'data-pack', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['incomplete_count'] == 0
    (project / 'workflows' / 'series.ds.json').write_text(json.dumps(
        _workflow('series', 'dataset', ['evidence/base.txt'], [],
                  ['rows=20000']),
    ), encoding='utf-8')
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'data-pack', str(project),
         '--check', '--state', str(state_path), '--fail-on-incomplete'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['incomplete']


def test_feature_flag_help_and_analysis_namespace_document_data():
    status = feature_status('sector.data_science_pack')
    assert status.stability == Stability.STABLE
    assert status.since == '3.1.55'
    text = pea_help('data-pack')
    assert 'pea data-pack' in text
    assert 'DataProfileV2 ->' in text
    assert 'data_pack_gate(report)' in text
    namespace = build_data_pack_namespace()
    assert namespace['DATA_PACK_VERSION'] == '3.1.55'
    assert namespace['build_data_pack_namespace'] is build_data_pack_namespace
    analysis = build_analysis_namespace()
    for name in ('DataProfileV2', 'DataIssueV2', 'DataWorkflowV2',
                 'DataPackPlanV2', 'PlanDataPack', 'DataStateV2',
                 'WriteDataStateV2', 'DataCapabilitiesV2', 'DataReportV2',
                 'DataGateV2', 'DataNamespaceV2'):
        assert name in analysis
    assert analysis['DataGateV2'] is gate_v2


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.4.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.4.0'
    assert manifest['previous_version'] == '5.3.0'
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
