import json
from pathlib import Path

import pealang

ROOT = Path(__file__).parents[1]

GATES = (
    ('pealang.ci_evidence', 'ci_evidence_capabilities', '5.14.0'),
    ('pealang.artifact_attestation', 'artifact_attestation_capabilities',
     '5.15.0'),
    ('pealang.license_review', 'license_review_capabilities', '5.16.0'),
    ('pealang.live_integration', 'live_integration_capabilities', '5.17.0'),
    ('pealang.security_soak', 'security_soak_capabilities', '5.18.0'),
    ('pealang.support_operations', 'support_operations_capabilities', '5.19.0'),
    ('pealang.stable_declaration', 'stable_declaration_capabilities', '5.20.0'),
)


def test_handoff_docs_exist_and_are_fail_closed():
    handoff = ROOT / 'docs' / 'GA_EVIDENCE_HANDOFF.md'
    checklist = ROOT / 'release-evidence' / '1.0' / 'HANDOFF_CHECKLIST.md'
    for path in (handoff, checklist):
        assert path.is_file()
        text = path.read_text(encoding='utf-8')
        assert 'NO-GO' in text
        assert 'synthetic' in text.lower()
    template = json.loads(
        (ROOT / 'release-evidence' / '1.0' / 'EVIDENCE_TEMPLATE.json').read_text(
            encoding='utf-8')
    )
    assert template['status'].startswith('NO-GO')


def test_handoff_mentions_all_existing_validators():
    text = (ROOT / 'docs' / 'GA_EVIDENCE_HANDOFF.md').read_text(encoding='utf-8')
    for command in (
        'pea ci-evidence', 'pea artifact-attestation', 'pea license-review',
        'pea live-integration', 'pea security-soak', 'pea support-operations',
        'pea stable-declaration', 'final_release_gate_v099',
        'pre_v1_evidence_v0992',
    ):
        assert command in text


def test_existing_gates_remain_the_only_validators():
    import importlib
    for module_name, fn_name, pinned in GATES:
        module = importlib.import_module(module_name)
        capabilities = getattr(module, fn_name)()
        assert capabilities['version'] == pinned
