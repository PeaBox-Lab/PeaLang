# PeaLang Revised Foundational Roadmap

The original roadmap goal is not yet complete. The implementation has covered much of the VM, embedding and integration work, but foundational maturity still requires specification completion, standard-library stabilization, deeper type semantics, structured concurrency, complete resource accounting, native language testing, larger conformance coverage, migration tooling, cross-platform CI evidence and production pilots.

## 0.34 - Specification and compatibility foundation - delivered
- Normative specification directory and EBNF grammar
- Feature stability registry
- Compatibility/deprecation rules
- Spec verification command

## 0.35 - Standard library stabilization
- `std.collections`, `std.string`, `std.math`, `std.datetime`, `std.json`, `std.csv`, `std.regex`, `std.file`, `std.path`, `std.http`, `std.crypto`, `std.logging`, `std.testing`, `std.concurrent`
- Permission declarations on sensitive modules
- Standard-library compatibility tests

## 0.36 - Type system completion
- Generic functions and substitution
- Protocols/interfaces
- Cross-module type checking
- Exhaustive flow/null narrowing
- Result/Option/Future semantics

## 0.37 - Runtime resource and concurrency completion
- Memory accounting and limits
- Collection/output/file/HTTP quotas
- recursion and call-depth enforcement everywhere
- task groups, spawn, cancellation propagation and structured concurrency

## 0.38 - Native testing and migration
- `test`, `describe`, `before_each`, `expect`
- `pea test --filter`, `--coverage`, `--watch`
- `pea migrate`
- compatibility/deprecation warnings

## 0.39 - Cross-runtime portability
- WebAssembly VM prototype
- browser-safe PEAC runtime
- Python VM/WASM differential fixtures
- Node/browser host capability ABI

## 0.40 - Conformance and platform gate - implementation delivered; CI evidence pending
- 500+ conformance tests
- parser/VM >=90% coverage target
- security-boundary 100% coverage target
- lexer/parser/compiler fuzzing
- Windows/Linux/macOS CI definitions
- Python 3.10-3.13 matrix or documented supported matrix

## 0.41 - Beta/pilot gate - tooling/evidence framework delivered; real pilot validation pending
- Two real application pilots
- three stable host integrations
- performance baselines and regression thresholds
- external security review preparation
- 1.0 migration report

## 1.0 gate
Grammar, type system, standard library, embedding API, package format and PEAC compatibility policy must be Stable; security must be reviewed; LSP/DAP workflows and documentation must be complete; real applications must run without runtime forks.

## 0.99.6 - Security hardening baseline - delivered
- Unknown SSH host keys rejected by default
- Legacy HMAC secret removed from trust-store metadata
- Type-system ReDoS protections
- 611-test regression baseline

## 1.0.0 - Comprehensive experience release (new)
### Product goal
Make PeaLang the default extension language for:
- web applications and APIs
- data analysis and notebooks
- cross-language embedding and interop

### Workstreams
1. Web application experience
   - `web.app()`, routing, middleware, static files, request/response helpers
   - `pea init --template webapp`
   - FastAPI/React SDK alignment
   - browser/WASM loader improvements
2. Data analysis experience
   - `analysis.profile`, `describe`, `correlation`, `outliers`, `clean_missing`, `normalize`, `pivot`
   - Markdown/HTML reporting
   - notebook-rich display hooks
   - SQL/dataframe interop
   - native `stats` / `std.stats` numerics layer (v114)
   - statistical inference, regression diagnostics and time-series analysis (v115)
   - generalized linear models, regularized regression, survival analysis and ARIMA (v116)
   - propensity scores, IPW/AIPW, matching, difference-in-differences, instrumental variables and regression discontinuity (v117)
   - train/test splits, k-fold cross-validation, classification and regression metrics, ROC/AUC, calibration and feature preparation (v118)
   - CART decision trees and bagged random forests with feature importance and out-of-bag scoring (v119)
   - gradient boosted trees for regression, binary and multiclass classification, with shrinkage and subsampling (v120)
   - cross-validation, grid search and random search over tree, forest and boosting estimators (v121)
   - permutation importance and partial dependence for fitted tree, forest and boosting models (v122)
   - class-balance reporting, random oversampling/undersampling and SMOTE (v123)
   - composable imputation, encoding and scaling pipelines with end-to-end model wrappers (v124)
   - versioned JSON model persistence with summaries and compact documents (v125)
   - calendar feature extraction and a pipeline date step (v126)
3. Cross-language experience
   - Python bridge: `interop.call_python`
   - native bridge: `interop.call_native`
   - process bridge: `interop.run`
   - HTTP bridge and generated TypeScript/Java/Python clients
4. Developer experience
   - `pea doctor`, `pea templates`
   - improved error suggestions
   - project templates
   - stable std.web/std.analysis/std.interop/std.ux namespaces
5. Quality gates
   - unit tests for every new namespace
   - conformance fixtures for web/data/interop
   - documentation and examples

### Delivered (v114 - native data science toolkit)
- `stats` / `std.stats`: dependency-free descriptive statistics, linear algebra, probability distributions, hypothesis tests, regression, k-means, PCA, interpolation, and resampling
- pandas-class additions to `analysis`: quantile binning, rolling/expanding variants, interpolation, factorize, masking, dtype selection, frame introspection, pivot tables, index helpers, multi-key grouping/merging, missing summaries, winsorizing, Spearman correlation, and date ranges
- Runnable use cases for statistical analysis, matrix regression, and customer segmentation
- `docs/DATA_SCIENCE.md` and `help/NUMERICS.md` with a Python/Go/PeaLang capability map

### Delivered (v113 - data and polyglot use cases)
- SQL over in-memory records (`analysis.sql`, `analysis.sql_value`) including grouping and window functions
- File-based data IO for CSV/JSON/JSONL (`analysis.read_*_file` / `analysis.write_*_file`)
- Go interoperability and client generation (`interop.go_run`, `interop.go_available`, `interop.go_version`, `interop.generate_go`)
- `data` and `polyglot` project templates
- Runnable use cases in `examples/use_cases/` with regression coverage and `docs/USE_CASES.md`

### Exit criteria
- New namespaces are exported and documented.
- Web, analysis, and interop smoke tests pass.
- Existing 611-test baseline remains green.
- Roadmap and changelog describe the 1.0.0 experience layer.