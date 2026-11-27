import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_performance_gate_uses_real_cli_and_retains_report():
    text = (ROOT / '.github/workflows/performance-gate.yml').read_text(encoding='utf-8')
    assert 'python -m pealang.benchmark' not in text
    assert 'python -m pealang.cli benchmark' in text
    assert '--save-baseline baseline.json' in text
    assert '--baseline baseline.json' in text
    assert 'perf_report.json' in text
    assert 'Upload Performance Report' in text


def test_python_matrix_pins_pytest_and_uploads_report():
    text = (ROOT / '.github/workflows/os-python-matrix.yml').read_text(encoding='utf-8')
    assert 'pytest==' in text
    assert '--junitxml=pytest-report.xml' in text
    assert 'pytest-report.xml' in text
    assert 'Upload pytest report' in text


def test_java_node_matrix_retains_reports_and_checks_browser_sdk():
    text = (ROOT / '.github/workflows/java-node-matrix.yml').read_text(encoding='utf-8')
    assert 'surefire-reports' in text
    assert 'typescript-report.txt' in text
    assert 'react-report.txt' in text
    assert 'browser-sdk/pealang-wasm.js' in text
    assert 'loadPeaWasm' in text
    for rel in ('typescript-sdk/package.json', 'react-sdk/package.json'):
        data = json.loads((ROOT / rel).read_text(encoding='utf-8'))
        dependencies = dict(data.get('devDependencies', {}))
        dependencies.update(data.get('peerDependencies', {}))
        assert all(not version.startswith('^') for version in dependencies.values()), rel


def test_security_workflow_retains_scanner_reports():
    text = (ROOT / '.github/workflows/security-scanners.yml').read_text(encoding='utf-8')
    for token in ('bandit.json', 'pip-audit.json', 'semgrep.sarif',
                  'trivy.sarif', 'secrets.json'):
        assert token in text
    for name in ('Bandit', 'pip-audit', 'Semgrep', 'Trivy', 'Secret scan'):
        assert name.lower() in text.lower()


def test_ga_handoff_stays_fail_closed():
    handoff = (ROOT / 'docs/GA_EVIDENCE_HANDOFF.md').read_text(encoding='utf-8')
    assert 'NO-GO' in handoff
    assert 'synthetic' in handoff.lower()
    assert 'pytest-report.xml' in handoff
    checklist = (ROOT / 'release-evidence/1.0/HANDOFF_CHECKLIST.md').read_text(
        encoding='utf-8')
    assert 'NO-GO' in checklist
    template = json.loads(
        (ROOT / 'release-evidence/1.0/EVIDENCE_TEMPLATE.json').read_text(
            encoding='utf-8'))
    assert template['status'].startswith('NO-GO')
