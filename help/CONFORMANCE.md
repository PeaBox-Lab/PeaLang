# Conformance and quality gates (v133)

PeaLang provides tools for running conformance checks, validating API stability,
and generating quality-gate reports for the final 1.0 release certification.

## Key functions

- `analysis.run_conformance_suite(cases)` — run conformance test cases
- `analysis.check_api_stability(current, baseline)` — compare API surfaces
- `analysis.check_doc_coverage(modules, documented)` — documentation coverage
- `analysis.environment_check()` — runtime environment validation
- `analysis.generate_quality_report(checks)` — markdown quality report
- `analysis.hash_source_tree(root)` — deterministic source hash