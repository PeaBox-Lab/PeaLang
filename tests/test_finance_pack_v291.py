"""Phase 91: deterministic Enterprise/Finance/Banking sector-pack evidence."""

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
from pealang.finance_pack import (DEFAULT_FINANCE_PROFILE, FINANCE_KINDS,
                                  FINANCE_PACK_FORMAT, FINANCE_PACK_VERSION,
                                  FinancePackError,
                                  FinanceProfileV2 as ProfileV2,
                                  build_finance_pack_namespace,
                                  finance_pack_capabilities as capabilities_v2,
                                  finance_pack_gate as gate_v2,
                                  finance_pack_report as report_v2,
                                  load_finance_state_v2 as load_state_v2,
                                  plan_finance_pack as plan_v2,
                                  write_finance_state_v2 as write_state_v2)


def _artifact(path, name, kind, evidence, requires=(), contracts=()):
    return {
        'name': name, 'version': '1.0.0', 'kind': kind,
        'evidence': list(evidence), 'requires': list(requires),
        'contracts': list(contracts),
    }


def _write_pack(root: Path) -> None:
    for folder in ('models', 'contracts', 'apps', 'evidence'):
        (root / folder).mkdir(parents=True, exist_ok=True)
    for name in ('base.txt', 'ledger.txt', 'audit.txt'):
        (root / 'evidence' / name).write_text(name + '\n', encoding='utf-8')
    items = {
        'models/ledger.finance.json': _artifact(
            'models/ledger.finance.json', 'ledger', 'domain-model',
            ['evidence/base.txt']),
        'contracts/payments.finance.json': _artifact(
            'contracts/payments.finance.json', 'payments',
            'transaction-contract', ['evidence/ledger.txt'], ['ledger'], ['P1']),
        'contracts/audit.finance.json': _artifact(
            'contracts/audit.finance.json', 'audit', 'audit-rule',
            ['evidence/audit.txt'], [], ['A1']),
        'apps/portal.finance.json': _artifact(
            'apps/portal.finance.json', 'portal', 'reference-app',
            ['evidence/base.txt'], ['payments', 'audit']),
    }
    for rel, payload in items.items():
        (root / rel).write_text(json.dumps(payload), encoding='utf-8')


def test_constants_capabilities_and_profile_validation():
    caps = capabilities_v2()
    assert FINANCE_PACK_VERSION == pealang.FINANCE_PACK_VERSION == '3.1.54'
    assert FINANCE_PACK_FORMAT == pealang.FINANCE_PACK_FORMAT == 'pea-finance-pack'
    assert caps == capabilities_v2()
    assert caps['version'] == '3.1.54'
    assert caps['source_filter'] == '*.finance.json'
    assert caps['stable_order'] is True
    assert caps['wall_clock_excluded'] is True
    assert caps['host_paths_excluded'] is True
    assert caps['recomputed_gate'] is True
    assert caps['kinds'] == sorted(FINANCE_KINDS)
    assert DEFAULT_FINANCE_PROFILE.digest() == ProfileV2().digest()
    assert DEFAULT_FINANCE_PROFILE.effective_version() == '3.1.54'
    assert ProfileV2(current_version='9.9.9').effective_version() == '9.9.9'
    with pytest.raises(FinancePackError):
        ProfileV2(max_artifacts=0)
    with pytest.raises(FinancePackError):
        ProfileV2(current_version=1)


def test_plan_discovers_artifacts_and_orders_dependencies(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    assert [item.path for item in plan.artifacts] == [
        'apps/portal.finance.json',
        'contracts/audit.finance.json',
        'contracts/payments.finance.json',
        'models/ledger.finance.json',
    ]
    assert [item.kind for item in plan.artifacts] == [
        'reference-app', 'audit-rule', 'transaction-contract', 'domain-model',
    ]
    assert plan.artifacts[0].requires == ('audit', 'payments')
    assert plan.artifacts[0].dependencies == (
        'contracts/audit.finance.json', 'contracts/payments.finance.json',
    )
    assert plan.artifacts[2].contracts == ('P1',)
    assert plan.build_order == (
        'contracts/audit.finance.json',
        'models/ledger.finance.json',
        'contracts/payments.finance.json',
        'apps/portal.finance.json',
    )
    assert len(plan.incomplete) == 4
    assert all(item.state == 'stale' for item in plan.artifacts)
    assert plan.gate == 'PASS'
    assert plan.issues == ()
    assert len(plan.digest) == 64
    assert all(len(item.fingerprint()) == 64 for item in plan.artifacts)
    assert all('\\' not in item.path and ':' not in item.path
               for item in plan.artifacts)


def test_state_round_trip_and_digest_ignores_host_root(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    state_path = write_state_v2(tmp_path, plan)
    state = load_state_v2(state_path)
    clean = plan_v2(tmp_path, state=state)
    assert clean.incomplete == ()
    assert all(item.state == 'current' for item in clean.artifacts)
    assert all(item.reasons == () for item in clean.artifacts)
    assert clean.gate == 'PASS'
    copy_root = tmp_path / 'copy'
    _write_pack(copy_root)
    assert plan_v2(copy_root).digest == plan.digest
    payload = json.loads(state_path.read_text(encoding='utf-8'))
    assert payload['version'] == '3.1.54'
    assert payload['format'] == 'pea-finance-pack'
    assert len(payload['state']) == 4


def test_changed_artifact_is_incomplete_and_propagates_to_dependents(tmp_path):
    _write_pack(tmp_path)
    state = load_state_v2(write_state_v2(tmp_path, plan_v2(tmp_path)))
    (tmp_path / 'models' / 'ledger.finance.json').write_text(json.dumps(
        _artifact('models/ledger.finance.json', 'ledger', 'domain-model',
                  ['evidence/base.txt'], [], ['extra']),
    ), encoding='utf-8')
    plan = plan_v2(tmp_path, state=state)
    assert [item.path for item in plan.artifacts if item.state == 'stale'] == [
        'apps/portal.finance.json',
        'contracts/payments.finance.json',
        'models/ledger.finance.json',
    ]
    reasons = {item.path: item.reasons for item in plan.artifacts}
    assert reasons['models/ledger.finance.json'] == ('changed',)
    assert reasons['contracts/payments.finance.json'] == ('dependency',)
    assert reasons['apps/portal.finance.json'] == ('dependency',)
    assert reasons['contracts/audit.finance.json'] == ()
    assert gate_v2(report_v2([plan])) == {'gate': 'PASS', 'issues': []}
    strict = report_v2([plan], ProfileV2(fail_on_incomplete=True))
    assert gate_v2(strict) == {'gate': 'FAIL', 'issues': ['incomplete']}


def test_missing_dependency_cycle_limit_and_invalid_manifest_issues(tmp_path):
    missing_root = tmp_path / 'missing'
    (missing_root / 'evidence').mkdir(parents=True)
    (missing_root / 'evidence' / 'root.txt').write_text('ok\n',
                                                        encoding='utf-8')
    (missing_root / 'orphan.finance.json').write_text(json.dumps(_artifact(
        'orphan.finance.json', 'orphan', 'domain-model',
        ['evidence/root.txt'], ['absent'],
    )), encoding='utf-8')
    broken = plan_v2(missing_root)
    assert [item.code for item in broken.issues] == ['F201']
    assert 'absent' in broken.issues[0].message
    assert broken.gate == 'FAIL'

    cycle_root = tmp_path / 'cycle'
    (cycle_root / 'evidence').mkdir(parents=True)
    (cycle_root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    for name, requires in (('a', ['b']), ('b', ['a'])):
        (cycle_root / f'{name}.finance.json').write_text(json.dumps(_artifact(
            f'{name}.finance.json', name, 'domain-model',
            ['evidence/root.txt'], requires,
        )), encoding='utf-8')
    cyclic = plan_v2(cycle_root)
    assert [item.code for item in cyclic.issues] == ['F202']
    assert cyclic.gate == 'FAIL'
    limited = plan_v2(cycle_root, ProfileV2(max_artifacts=1))
    assert 'F203' in [item.code for item in limited.issues]

    invalid_root = tmp_path / 'invalid'
    invalid_root.mkdir()
    (invalid_root / 'bad.finance.json').write_text('{}', encoding='utf-8')
    assert [item.code for item in plan_v2(invalid_root).issues] == ['F204']


def test_missing_evidence_issue(tmp_path):
    root = tmp_path / 'evidence-root'
    root.mkdir()
    (root / 'app.finance.json').write_text(json.dumps(_artifact(
        'app.finance.json', 'app', 'domain-model',
        ['evidence/missing.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == ['F205']
    assert plan.gate == 'FAIL'


def test_interop_and_audit_contract_issues_and_toggles(tmp_path):
    root = tmp_path / 'contracts-root'
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'bridge.finance.json').write_text(json.dumps(_artifact(
        'bridge.finance.json', 'bridge', 'interop-binding',
        ['evidence/root.txt'],
    )), encoding='utf-8')
    (root / 'plain.finance.json').write_text(json.dumps(_artifact(
        'plain.finance.json', 'plain', 'reference-app',
        ['evidence/root.txt'],
    )), encoding='utf-8')
    plan = plan_v2(root)
    assert [item.code for item in plan.issues] == ['F206', 'F207']
    assert plan.gate == 'FAIL'
    relaxed = plan_v2(root, ProfileV2(check_interop=False, check_audit=False))
    assert relaxed.issues == ()
    assert relaxed.gate == 'PASS'
    interop_off = plan_v2(root, ProfileV2(check_interop=False))
    assert [item.code for item in interop_off.issues] == ['F207']
    audit_off = plan_v2(root, ProfileV2(check_audit=False))
    assert [item.code for item in audit_off.issues] == ['F206']


def test_sandbox_artifacts_are_skipped_until_enabled(tmp_path):
    root = tmp_path / 'sandbox-root'
    (root / 'sandbox').mkdir(parents=True)
    (root / 'evidence').mkdir(parents=True)
    (root / 'evidence' / 'root.txt').write_text('ok\n', encoding='utf-8')
    (root / 'sandbox' / 'old.finance.json').write_text(json.dumps(_artifact(
        'sandbox/old.finance.json', 'old', 'domain-model',
        ['evidence/root.txt'],
    )), encoding='utf-8')
    assert plan_v2(root).artifacts == ()
    included = plan_v2(root, ProfileV2(include_sandbox=True))
    assert [item.path for item in included.artifacts] == [
        'sandbox/old.finance.json',
    ]


def test_report_and_gate_are_recomputed_and_tamper_detecting(tmp_path):
    _write_pack(tmp_path)
    plan = plan_v2(tmp_path)
    report = report_v2([plan])
    assert report['version'] == '3.1.54'
    assert report['format'] == 'pea-finance-pack'
    assert report['plan_count'] == 1
    assert report['artifact_count'] == 4
    assert report['incomplete_count'] == 4
    assert report['error_count'] == 0
    assert report['gate'] == 'PASS'
    assert len(report['digest']) == 64
    assert gate_v2(report) == {'gate': 'PASS', 'issues': []}
    assert 'version' in gate_v2({**report, 'version': 'old'})['issues']
    assert 'format' in gate_v2({**report, 'format': 'old'})['issues']
    assert 'digest' in gate_v2({**report, 'digest': '0' * 64})['issues']
    assert 'counts' in gate_v2({**report, 'artifact_count': 99})['issues']
    tampered = json.loads(json.dumps(report))
    tampered['plans'][0]['artifacts'][0]['fingerprint'] = '0' * 64
    assert 'artifact_fingerprint' in gate_v2(tampered)['issues']


def test_cli_capabilities_check_emit_state_and_strict_gate(tmp_path):
    project_root = Path(__file__).resolve().parent.parent
    caps = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'finance-pack', '--capabilities'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert caps.returncode == 0, caps.stderr
    assert json.loads(caps.stdout)['version'] == '3.1.54'
    project = tmp_path / 'project'
    _write_pack(project)
    state_path = tmp_path / 'state.json'
    emit_path = tmp_path / 'finance.json'
    planned = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'finance-pack', str(project),
         '--check', '--state', str(state_path), '--emit', str(emit_path),
         '--write-state'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert planned.returncode == 0, planned.stderr
    report = json.loads(planned.stdout)
    assert report['version'] == '3.1.54'
    assert report['artifact_count'] == 4
    assert report['decision'] == {'gate': 'PASS', 'issues': []}
    assert json.loads(emit_path.read_text(encoding='utf-8')) == report
    assert state_path.is_file()
    clean = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'finance-pack', str(project),
         '--check', '--state', str(state_path)],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)['incomplete_count'] == 0
    (project / 'models' / 'ledger.finance.json').write_text(json.dumps(
        _artifact('models/ledger.finance.json', 'ledger', 'domain-model',
                  ['evidence/base.txt'], [], ['extra']),
    ), encoding='utf-8')
    strict = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'finance-pack', str(project),
         '--check', '--state', str(state_path), '--fail-on-incomplete'],
        capture_output=True, text=True, cwd=str(project_root),
    )
    assert strict.returncode == 1, strict.stderr
    assert json.loads(strict.stdout)['decision']['issues'] == ['incomplete']


def test_feature_flag_help_and_analysis_namespace_document_finance():
    status = feature_status('sector.finance_pack')
    assert status.stability == Stability.STABLE
    assert status.since == '3.1.54'
    text = pea_help('finance-pack')
    assert 'pea finance-pack' in text
    assert 'FinanceProfileV2 ->' in text
    assert 'finance_pack_gate(report)' in text
    namespace = build_finance_pack_namespace()
    assert namespace['FINANCE_PACK_VERSION'] == '3.1.54'
    assert namespace['build_finance_pack_namespace'] is build_finance_pack_namespace
    analysis = build_analysis_namespace()
    for name in ('FinanceProfileV2', 'FinanceIssueV2', 'FinanceArtifactV2',
                 'FinancePackPlanV2', 'PlanFinancePack', 'FinanceStateV2',
                 'WriteFinanceStateV2', 'FinanceCapabilitiesV2',
                 'FinanceReportV2', 'FinanceGateV2', 'FinanceNamespaceV2'):
        assert name in analysis
    assert analysis['FinanceGateV2'] is gate_v2


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.17.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.17.0'
    assert manifest['previous_version'] == '5.16.0'
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
