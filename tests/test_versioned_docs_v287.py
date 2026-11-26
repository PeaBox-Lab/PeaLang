"""Phase 87: deterministic versioned documentation inventory with stable gates."""

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
from pealang.versioned_docs import (DEFAULT_DOCS_PROFILE,
                                   VERSIONED_DOCS_FORMAT,
                                   VERSIONED_DOCS_VERSION,
                                   DocsProfileV2 as ProfileV2,
                                   VersionedDocsError as DocsErrorV2,
                                   build_versioned_docs_namespace,
                                   docs_v2_gate as gate_v2,
                                   docs_v2_report as report_v2,
                                   load_docs_state_v2 as load_state_v2,
                                   plan_docs_v2 as plan_v2,
                                   versioned_docs_capabilities as capabilities_v2,
                                   write_docs_state_v2 as write_state_v2)


def _write_docs(root: Path) -> None:
    (root / 'docs').mkdir(parents=True, exist_ok=True)
    (root / 'docs' / 'api.md').write_text('# API 3.1.50\n', encoding='utf-8')
    (root / 'docs' / 'guide.md').write_text(
        '# Guide 3.1.50\n\nSee [api](api.md) and '
        '[external](https://example.com).\n',
        encoding='utf-8',
    )


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert VERSIONED_DOCS_VERSION == pealang.VERSIONED_DOCS_VERSION == '3.1.50'
    assert VERSIONED_DOCS_FORMAT == pealang.VERSIONED_DOCS_FORMAT == 'pea-docs-v2'
    assert caps == capabilities_v2()
    assert caps['version'] == '3.1.50'
    assert caps['source_filter'] == '*.md'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert DEFAULT_DOCS_PROFILE.digest() == ProfileV2().digest()
    assert DEFAULT_DOCS_PROFILE.effective_version() == '3.1.50'
    assert ProfileV2(current_version='9.9.9').effective_version() == '9.9.9'
    with pytest.raises(DocsErrorV2):
        ProfileV2(max_files=0)
    with pytest.raises(DocsErrorV2):
        ProfileV2(current_version=1)


def test_plan_discovers_versions_links_and_orders_entries(tmp_path):
    _write_docs(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.entries] == [
        'docs/api.md', 'docs/guide.md',
    ]
    assert plan.entries[0].versions == ('3.1.50',)
    assert plan.entries[1].links == ('api.md',)
    assert plan.drift == ('docs/api.md', 'docs/guide.md')
    assert all(item.state == 'stale' for item in plan.entries)
    assert plan.gate == 'PASS'
    assert plan.issues == ()
    assert plan.current_version == '3.1.50'
    assert len(plan.digest) == 64
    assert all(len(item.fingerprint()) == 64 for item in plan.entries)
    assert all('\\' not in item.path and ':' not in item.path
               for item in plan.entries)


def test_state_round_trip_and_digest_ignores_host_root(tmp_path):
    _write_docs(tmp_path)
    plan = plan_v2(tmp_path)
    state_path = write_state_v2(tmp_path, plan)
    state = load_state_v2(state_path)
    clean = plan_v2(tmp_path, state=state)
    assert clean.drift == ()
    assert all(item.state == 'current' for item in clean.entries)
    assert clean.gate == 'PASS'
    copy_root = tmp_path / 'copy'
    _write_docs(copy_root)
    assert plan_v2(copy_root).digest == plan.digest
    payload = json.loads(state_path.read_text(encoding='utf-8'))
    assert payload['version'] == '3.1.50'
    assert set(payload['state']) == {'docs/api.md', 'docs/guide.md'}


def test_changed_doc_is_drift_and_strict_gate_fails(tmp_path):
    _write_docs(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'docs' / 'api.md').write_text('# API 3.1.50 changed\n',
                                             encoding='utf-8')
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.entries if item.state == 'stale'] == [
        'docs/api.md',
    ]
    assert plan.drift == ('docs/api.md',)
    assert gate_v2(report_v2([plan])) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_drift=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['drift']}


def test_stale_version_broken_link_and_file_limit_are_stable_errors(tmp_path):
    _write_docs(tmp_path)
    (tmp_path / 'docs' / 'guide.md').write_text(
        '# Guide 3.1.49\n\nSee [missing](missing.md).\n', encoding='utf-8',
    )
    broken = plan_v2(tmp_path)
    assert [item.code for item in broken.issues] == ['D201', 'D202']
    assert '3.1.50' in broken.issues[0].message
    assert 'missing.md' in broken.issues[1].message
    assert broken.issues[0].path == 'docs/guide.md'
    assert broken.gate == 'FAIL'
    no_links = plan_v2(tmp_path, ProfileV2(check_links=False))
    assert [item.code for item in no_links.issues] == ['D201']
    history_root = tmp_path / 'history'
    (history_root / 'releases').mkdir(parents=True)
    (history_root / 'releases' / 'old.md').write_text('# Old 3.1.49\n',
                                                     encoding='utf-8')
    assert plan_v2(history_root).entries == ()
    included = plan_v2(history_root, ProfileV2(include_release_notes=True))
    assert [item.path for item in included.entries] == ['releases/old.md']
    limited = plan_v2(tmp_path, ProfileV2(max_files=1))
    assert 'D203' in [item.code for item in limited.issues]
    assert limited.gate == 'FAIL'


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_docs(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '3.1.50'
    assert report['format'] == 'pea-docs-v2'
    assert report['plan_count'] == 1
    assert report['doc_count'] == 2
    assert report['drift_count'] == 2
    assert report['gate'] == 'PASS'
    assert len(report['digest']) == 64
    assert gate_v2(report) == {'gate': 'PASS', 'issues': []}
    assert 'version' in gate_v2({**report, 'version': 'old'})['issues']
    assert 'format' in gate_v2({**report, 'format': 'old'})['issues']
    assert 'digest' in gate_v2({**report, 'digest': '0' * 64})['issues']
    assert 'counts' in gate_v2({**report, 'doc_count': 99})['issues']
    tampered = json.loads(json.dumps(report))
    tampered['plans'][0]['entries'][0]['fingerprint'] = '0' * 64
    assert 'entry_fingerprint' in gate_v2(tampered)['issues']


def test_cli_capabilities_check_emit_state_and_strict_gate(tmp_path):
    root = Path(__file__).resolve().parent.parent
    caps = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'docs-v2', '--capabilities'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '3.1.50'
    project = tmp_path / 'project'
    _write_docs(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'docs.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'docs-v2', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '3.1.50'
    assert report['doc_count'] == 2
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'docs-v2', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['drift_count'] == 0
    (project / 'docs' / 'api.md').write_text('# API 3.1.50 changed\n',
                                            encoding='utf-8')
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'docs-v2', str(project),
         '--check', '--state', str(state_path), '--fail-on-drift'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['drift']


def test_feature_flag_help_and_analysis_namespace_document_versioned_docs():
    assert feature_status('devx.versioned_docs').stability == Stability.STABLE
    text = pea_help('docs-v2')
    assert 'pea docs-v2' in text
    assert 'DocsProfileV2 ->' in text
    namespace = build_versioned_docs_namespace()
    assert namespace['VERSIONED_DOCS_VERSION'] == '3.1.50'
    assert namespace['build_versioned_docs_namespace'] is build_versioned_docs_namespace
    analysis = build_analysis_namespace()
    for name in ('DocsProfileV2', 'DocEntryV2', 'DocsIssueV2', 'DocsPlanV2',
                 'PlanDocsV2', 'DocsStateV2', 'WriteDocsStateV2',
                 'VersionedDocsCapabilitiesV2', 'VersionedDocsReportV2',
                 'VersionedDocsGateV2', 'VersionedDocsNamespaceV2'):
        assert name in analysis


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '3.1.56'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '3.1.56'
    assert manifest['previous_version'] == '3.1.55'
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
