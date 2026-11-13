# Conformance and quality gates (v133)

PeaLang provides tools for running conformance checks, validating API stability,
and generating quality-gate reports for the final 1.0 release certification.

## Key functions

- `run_conformance_suite(cases)` — run conformance test cases
- `check_api_stability(current, baseline)` — compare API surfaces
- `check_doc_coverage(modules, documented)` — documentation coverage
- `environment_check()` — runtime environment validation
- `generate_quality_report(checks)` — markdown quality report
- `hash_source_tree(root)` — deterministic source hash