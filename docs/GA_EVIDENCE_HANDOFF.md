# PeaLang GA evidence handoff

Phase 122 defines the handoff boundary between deterministic gates and real
external evidence. The gates already shipped in Phases 114-120 validate evidence
shape and fail closed; they do not produce evidence.

## Required retained evidence

- Full pytest report and 12-cell OS/Python matrix from `os-python-matrix.yml`.
- Java 17/21 and Node 20/22/24 reports from `java-node-matrix.yml`.
- Bandit, pip-audit, Semgrep, Trivy, and secret-scan reports.
- Wheel, sdist, container, SBOM, provenance, signature, and reproducibility
  records; clean/offline install, upgrade, and rollback drill records.
- Manual third-party license review, live integration results, independent
  security review and threat model, multi-hour soak/load report.
- Named release, security, and operations approvals with signatures.

## Validators to run

```bash
pea ci-evidence . --check
pea artifact-attestation . --check
pea license-review . --check
pea live-integration . --check
pea security-soak . --check
pea support-operations . --check
pea stable-declaration . --check
python -m pealang.final_release_gate_v099
python -m pealang.pre_v1_evidence_v0992
```

Status remains **NO-GO** until genuine evidence is retained. Do not create
synthetic PASS records; synthetic fixtures in tests validate gate logic only.

## Retained CI report contract

Wave 10 Phase 124 workflows retain `pytest-report.xml`, `perf_report.json`,
`conformance_report.json`, Java `surefire-reports`, `typescript-report.txt`,
`react-report.txt`, `bandit.json`, `pip-audit.json`, `semgrep.sarif`,
`trivy.sarif`, and `secrets.json`. These are genuine CI artifacts, never
synthetic PASS records. Manual evidence and named approvals are still required.
