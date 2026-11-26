"""Phase 96: deterministic Game Development sector-pack evidence."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
import pytest
from pealang.analysis import build_analysis_namespace
from pealang.compatibility import Stability, feature_status
from pealang.core_freeze import core_freeze_report
from pealang.game_pack import (GAME_KINDS, GAME_PACK_FORMAT, GAME_PACK_VERSION,
                               DEFAULT_GAME_PROFILE, GamePackError,
                               GameProfileV2 as ProfileV2,
                               build_game_pack_namespace,
                               game_pack_capabilities as capabilities_v2,
                               game_pack_gate as gate_v2,
                               game_pack_report as report_v2,
                               load_game_state_v2 as load_state_v2,
                               plan_game_pack as plan_v2,
                               write_game_state_v2 as write_state_v2)
from pealang.help import help as pea_help
from pealang.specification import SPEC_VERSION


def _game(name, kind, evidence, requires=(), bindings=()):
    return {
        'name': name, 'version': '1.0.0', 'kind': kind,
        'evidence': list(evidence), 'requires': list(requires),
        'bindings': list(bindings),
    }


def _write_pack(root: Path) -> None:
    for folder in ('apps', 'evidence'):
        (root / folder).mkdir(parents=True, exist_ok=True)
    for name in ('base.txt', 'engine.txt'):
        (root / 'evidence' / name).write_text(name + '\n', encoding='utf-8')
    items = {
        'apps/demo.game.json': _game(
            'demo', 'sample-game', ['evidence/base.txt'],
            ['ecs', 'hot', 'input', 'render', 'runtime', 'unity'],
            ['ecs', 'hot', 'input', 'native', 'render', 'unity', 'wasm']),
        'apps/ecs.game.json': _game(
            'ecs', 'ecs', ['evidence/base.txt'], [], ['ecs']),
        'apps/hot.game.json': _game(
            'hot', 'hot-reload', ['evidence/base.txt'], [], ['hot']),
        'apps/input.game.json': _game(
            'input', 'input-api', ['evidence/base.txt'], [], ['input']),
        'apps/level.game.json': _game(
            'level', 'resource', ['evidence/base.txt']),
        'apps/render.game.json': _game(
            'render', 'render-api', ['evidence/base.txt'], [], ['render']),
        'apps/runtime.game.json': _game(
            'runtime', 'runtime', ['evidence/base.txt'], [],
            ['native', 'wasm']),
        'apps/unity.game.json': _game(
            'unity', 'unity-bridge', ['evidence/engine.txt'], [], ['unity']),
    }
    for rel, payload in items.items():
        (root / rel).write_text(json.dumps(payload), encoding='utf-8')


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert GAME_PACK_VERSION == pealang.GAME_PACK_VERSION == '3.1.59'
    assert GAME_PACK_FORMAT == pealang.GAME_PACK_FORMAT == 'pea-game-pack'
    assert caps == capabilities_v2()
    assert caps['version'] == '3.1.59'
    assert caps['source_filter'] == '*.game.json'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert caps['kinds'] == sorted(GAME_KINDS)
    assert caps['options'] == [
        'max_games', 'include_preview', 'check_runtime', 'check_ecs',
        'check_engine', 'check_hot_reload', 'check_input', 'check_render',
        'fail_on_incomplete', 'current_version',
    ]
    assert DEFAULT_GAME_PROFILE.digest() == ProfileV2().digest()
    assert DEFAULT_GAME_PROFILE.effective_version() == '3.1.59'
    assert ProfileV2(current_version='9.9.9').effective_version() == '9.9.9'
    with pytest.raises(GamePackError):
        ProfileV2(max_games=0)
    with pytest.raises(GamePackError):
        ProfileV2(current_version=1)


def test_plan_discovers_games_and_orders_dependencies(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.apps] == [
        'apps/demo.game.json',
        'apps/ecs.game.json',
        'apps/hot.game.json',
        'apps/input.game.json',
        'apps/level.game.json',
        'apps/render.game.json',
        'apps/runtime.game.json',
        'apps/unity.game.json',
    ]
    assert [item.kind for item in plan.apps] == [
        'sample-game', 'ecs', 'hot-reload', 'input-api', 'resource',
        'render-api', 'runtime', 'unity-bridge',
    ]
    sample = plan.apps[0]
    assert sample.requires == (
        'ecs', 'hot', 'input', 'render', 'runtime', 'unity',
    )
    assert sample.dependencies == (
        'apps/ecs.game.json', 'apps/hot.game.json', 'apps/input.game.json',
        'apps/render.game.json', 'apps/runtime.game.json',
        'apps/unity.game.json',
    )
    assert sample.bindings == (
        'ecs', 'hot', 'input', 'native', 'render', 'unity', 'wasm',
    )
    assert plan.build_order == (
        'apps/ecs.game.json',
        'apps/hot.game.json',
        'apps/input.game.json',
        'apps/level.game.json',
        'apps/render.game.json',
        'apps/runtime.game.json',
        'apps/unity.game.json',
        'apps/demo.game.json',
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
    assert payload['version'] == '3.1.59'
    assert payload['format'] == 'pea-game-pack'
    assert len(payload['state']) == 8


def test_changed_game_is_incomplete_and_propagates_to_demo(tmp_path):
    _write_pack(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'apps' / 'ecs.game.json').write_text(json.dumps(
        _game('ecs', 'ecs', ['evidence/base.txt'], [], ['ecs', 'v2']),
    ), encoding='utf-8')
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.apps if item.state == 'stale'] == [
        'apps/demo.game.json', 'apps/ecs.game.json',
    ]
    reasons = {item.path: item.reasons for item in plan.apps}
    assert reasons['apps/ecs.game.json'] == ('changed',)
    assert reasons['apps/demo.game.json'] == ('dependency',)
    assert reasons['apps/runtime.game.json'] == ()
    assert gate_v2(report_v2([plan])) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_incomplete=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['incomplete']}


def test_missing_dependency_cycle_limit_and_invalid_manifest_issues(tmp_path):
    missing_root = tmp_path / 'missing'
    (missing_root / 'evidence').mkdir(parents=True)
    (missing_root / 'evidence' / 'root.txt').write_text('ok\n',
                                                        encoding='utf-8')
    (missing_root / 'orphan.game.json').write_text(json.dumps(_game(
        'orphan', 'resource', ['evidence/root.txt'], ['absent'],
    )), encoding='utf-8')
    broken = plan_v2(missing_root)
    assert [item.code for item in broken.issues] == ['G201']
    assert 'absent' in broken.issues[0].message
    assert broken.gate == 'FAIL'

    cycle_root = tmp_path / 'cycle'
    (cycle_root / 'evidence').mkdir(parents=True)
    (cycle_root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    for name, requires in (('a', ['b']), ('b', ['a'])):
        (cycle_root / f'{name}.game.json').write_text(json.dumps(_game(
            name, 'resource', ['evidence/root.txt'], requires,
        )), encoding='utf-8')
    cyclic = plan_v2(cycle_root)
    assert [item.code for item in cyclic.issues] == ['G202']
    assert cyclic.gate == 'FAIL'
    limited = plan_v2(cycle_root, ProfileV2(max_games=1))
    assert 'G203' in [item.code for item in limited.issues]

    invalid_root = tmp_path / 'invalid'
    invalid_root.mkdir()
    (invalid_root / 'bad.game.json').write_text('{}', encoding='utf-8')
    assert [item.code for item in plan_v2(invalid_root).issues] == ['G204']


def test_missing_evidence_issue(tmp_path):
    root = tmp_path / 'evidence-root'
    root.mkdir()
    (root / 'app.game.json').write_text(json.dumps(_game(
        'app', 'resource', ['evidence/missing.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == ['G205']
    assert plan.gate == 'FAIL'


def test_runtime_ecs_engine_hot_input_and_render_governance_toggles(tmp_path):
    root = tmp_path / 'governance-root'
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'sample.game.json').write_text(json.dumps(_game(
        'sample', 'sample-game', ['evidence/root.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == [
        'G206', 'G207', 'G208', 'G209', 'G210', 'G211',
    ]
    assert plan.gate == 'FAIL'
    relaxed = plan_v2(root, ProfileV2(
        check_runtime=False, check_ecs=False, check_engine=False,
        check_hot_reload=False, check_input=False, check_render=False,
    ))
    assert relaxed.issues == ()
    assert relaxed.gate == 'PASS'
    runtime_off = plan_v2(root, ProfileV2(check_runtime=False))
    assert [item.code for item in runtime_off.issues] == [
        'G207', 'G208', 'G209', 'G210', 'G211',
    ]
    ecs_off = plan_v2(root, ProfileV2(check_ecs=False))
    assert [item.code for item in ecs_off.issues] == [
        'G206', 'G208', 'G209', 'G210', 'G211',
    ]
    engine_off = plan_v2(root, ProfileV2(check_engine=False))
    assert [item.code for item in engine_off.issues] == [
        'G206', 'G207', 'G209', 'G210', 'G211',
    ]
    hot_off = plan_v2(root, ProfileV2(check_hot_reload=False))
    assert [item.code for item in hot_off.issues] == [
        'G206', 'G207', 'G208', 'G210', 'G211',
    ]
    input_off = plan_v2(root, ProfileV2(check_input=False))
    assert [item.code for item in input_off.issues] == [
        'G206', 'G207', 'G208', 'G209', 'G211',
    ]
    render_off = plan_v2(root, ProfileV2(check_render=False))
    assert [item.code for item in render_off.issues] == [
        'G206', 'G207', 'G208', 'G209', 'G210',
    ]


def test_preview_games_are_skipped_until_enabled(tmp_path):
    root = tmp_path / 'preview-root'
    (root / 'preview').mkdir(parents=True)
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'preview' / 'old.game.json').write_text(json.dumps(_game(
        'old', 'resource', ['evidence/root.txt'],
    )), encoding='utf-8')
    assert plan_v2(root).apps == ()
    included = plan_v2(root, ProfileV2(include_preview=True))
    assert [item.path for item in included.apps] == ['preview/old.game.json']


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '3.1.59'
    assert report['format'] == 'pea-game-pack'
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
        [sys.executable, '-m', 'pealang.cli', 'game-pack', '--capabilities'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '3.1.59'
    project = tmp_path / 'project'
    _write_pack(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'game.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'game-pack', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '3.1.59'
    assert report['app_count'] == 8
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'game-pack', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['incomplete_count'] == 0
    (project / 'apps' / 'ecs.game.json').write_text(json.dumps(
        _game('ecs', 'ecs', ['evidence/base.txt'], [], ['ecs', 'v2']),
    ), encoding='utf-8')
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'game-pack', str(project),
         '--check', '--state', str(state_path), '--fail-on-incomplete'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['incomplete']
    minimal = tmp_path / 'minimal'
    (minimal / 'evidence').mkdir(parents=True)
    (minimal / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (minimal / 'sample.game.json').write_text(json.dumps(
        _game('sample', 'sample-game', ['evidence/root.txt']),
    ), encoding='utf-8')
    relaxed = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'game-pack', str(minimal),
         '--check', '--no-check-runtime', '--no-check-ecs',
         '--no-check-engine', '--no-check-hot-reload', '--no-check-input',
         '--no-check-render'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert relaxed.returncode == 0, relaxed.stderr
    assert json.loads(relaxed.stdout)['decision'] == {
        'gate': 'PASS', 'issues': [],
    }


def test_feature_flag_help_and_analysis_namespace_document_game():
    status = feature_status('sector.game_pack')
    assert status.stability == Stability.STABLE
    assert status.since == '3.1.59'
    text = pea_help('game-pack')
    assert 'pea game-pack' in text
    assert 'GameProfileV2 ->' in text
    assert 'game_pack_gate(report)' in text
    namespace = build_game_pack_namespace()
    assert namespace['GAME_PACK_VERSION'] == '3.1.59'
    assert namespace['build_game_pack_namespace'] is build_game_pack_namespace
    analysis = build_analysis_namespace()
    for name in ('GameProfileV2', 'GameIssueV2', 'GameAppV2',
                 'GamePackPlanV2', 'PlanGamePack', 'GameStateV2',
                 'WriteGameStateV2', 'GameCapabilitiesV2', 'GameReportV2',
                 'GameGateV2', 'GameNamespaceV2'):
        assert name in analysis
    assert analysis['GameGateV2'] is gate_v2


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.19.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.19.0'
    assert manifest['previous_version'] == '5.18.0'
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
