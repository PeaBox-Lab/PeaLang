# PeaLang 0.99.4 Security Closure

- Replaced MD5-derived CycloneDX serial generation with deterministic UUIDv5.
- Added AST-based local checks for Python dynamic eval/exec, os.system, tempfile.mktemp, weak hashes and embedded key markers.
- Added GitHub Actions jobs for Bandit, pip-audit, Semgrep and Trivy vulnerability/secret/misconfiguration scans.
- External scanner results remain fail-closed until the workflow runs and all High/Critical findings are resolved or explicitly reviewed.
