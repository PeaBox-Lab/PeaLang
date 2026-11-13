# PeaLang Markdown/HTML Reporting (v128)

PeaLang renders in-memory tables, fitted models and evaluation results to
Markdown and HTML, and writes them to disk alongside JSON — without any
third-party packages.

Everything below runs in plain PeaLang and is covered by the regression suite
(`examples/use_cases/24_reporting.pea`, tested in `tests/test_reporting_v128.py`
and `tests/test_use_cases_v128.py`).

## Reporting API

All reporting functions live in the `analysis` namespace:

| Function | Purpose |
|---|---|
| `analysis.profile_markdown(data)` | Markdown table profile of a dataset |
| `analysis.profile_html(data)` | HTML page wrapping the Markdown profile |
| `analysis.report_markdown(data, kind)` | Auto-detect report kind (`profile`, `model`, `evaluation`, `summary`) |
| `analysis.report_html(data, kind)` | HTML page wrapping any report kind |
| `analysis.model_markdown(model)` | Model summary: estimator, task, features, importance, accuracy |
| `analysis.model_html(model)` | HTML page wrapping the model report |
| `analysis.evaluation_markdown(evaluation)` | Evaluation metrics as Markdown bold lines |
| `analysis.evaluation_html(evaluation)` | HTML page wrapping the evaluation report |
| `analysis.write_report_markdown(path, report)` | Write a Markdown report to disk (kind auto-detected) |
| `analysis.write_report_html(path, report)` | Write an HTML report to disk (kind auto-detected) |
| `analysis.write_report_json(path, report)` | Write a JSON document to disk |

PeaLang has no keyword arguments, so reporting calls use positional arguments:
`analysis.write_report_markdown(path, report)`. The report kind is detected
from the record shape:

- record containing `fields` → `profile` (pass raw data directly)
- record containing `estimator` → `model`
- record containing `accuracy` → `evaluation`
- anything else → `profile`

`analysis.report_markdown(data)` / `analysis.report_html(data)` with no `kind`
argument auto-detect the same way and wrap raw Markdown in the HTML page.

Markdown content (tables, lists, bold text) is rendered inline in HTML — it is
not dumped into `<pre>` as JSON — and angle brackets are escaped so markup
inside report text does not break the page.

## Quick start

```pea
let rows = [
    { "category": "A", "value": 10 },
    { "category": "B", "value": 20 },
    { "category": "A", "value": 30 }
]

let profile_md = analysis.profile_markdown(rows)
let profile_html = analysis.profile_html(rows)

let model = {
    "estimator": "random_forest",
    "task": "classification",
    "n_rows": 100,
    "n_features": 3,
    "importance": [
        { "feature": "value", "importance": 0.5 },
        { "feature": "category", "importance": 0.3 }
    ],
    "train_accuracy": 0.85,
    "classes": ["low", "high"]
}

let model_md = analysis.model_markdown(model)
let model_html = analysis.model_html(model)

let evaluation = { "accuracy": 0.88, "precision": 0.82 }
let eval_md = analysis.evaluation_markdown(evaluation)
let eval_html = analysis.evaluation_html(evaluation)

analysis.write_report_markdown("reports/profile_report.md", rows)
analysis.write_report_html("reports/profile_report.html", rows)
analysis.write_report_markdown("reports/model_report.md", model)
analysis.write_report_html("reports/model_report.html", model)
analysis.write_report_markdown("reports/evaluation_report.md", evaluation)
analysis.write_report_html("reports/evaluation_report.html", evaluation)
analysis.write_report_json("reports/evaluation_report.json", evaluation)

print "Reports written to reports/"
```

Each call writes deterministically: same input always produces the same file
contents, so generated reports can be compared across runs.

## How reporting fits into a pipeline

A typical analysis program profiles, cleans, models, evaluates and reports —
all in PeaLang:

```pea
let clean = analysis.dropna(analysis.read_csv_file("sales.csv"))
let profile_md = analysis.profile_markdown(clean)
let features = analysis.group_by(clean, "region", "amount", "sum")
let model = analysis.forest_report(clean, "churn", ["region", "amount"], "classification", 100, 6, 2, 7)
let evaluation = stats.accuracy_score(actual, predicted)

analysis.write_report_markdown("reports/profile.md", clean)
analysis.write_report_html("reports/profile.html", clean)
analysis.write_report_markdown("reports/model.md", model)
analysis.write_report_html("reports/model.html", model)
analysis.write_report_markdown("reports/evaluation.md", evaluation)
analysis.write_report_html("reports/evaluation.html", evaluation)
analysis.write_report_json("reports/evaluation.json", evaluation)
```

Profiles carry field types, missing counts and distinct counts. Model reports
carry the estimator name, task, row/column counts, feature importance, accuracy,
R² and RMSE when available, plus a JSON snapshot of the model. Evaluation
reports list each numeric metric to four decimal places.

## Design notes

- Pure Python: reporting imports only the standard library (`html`, `json`,
  `pathlib`).
- Markdown is rendered directly into the HTML body (`<pre>{markdown}</pre>`),
  not pretty-printed JSON, so it reads naturally on the page.
- HTML pages embed minimal CSS for readable tables and monospace blocks.
- `kind` defaults to auto-detection, which works from PeaLang because positional
  arguments are the only call style.

## See also

- `examples/use_cases/24_reporting.pea` — runnable end-to-end example.
- `docs/DATA_SCIENCE.md`, `docs/STATISTICAL_INFERENCE.md`,
  `docs/FEATURE_PIPELINES.md` — how reporting plugs into cleaning and modeling.
- `tests/test_reporting_v128.py` and `tests/test_use_cases_v128.py` — regression
  coverage.
