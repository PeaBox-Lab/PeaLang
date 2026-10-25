# PeaLang v0.71 Unified Lineage, Observability and Dashboards

This release combines the former v0.71, v0.72 and v0.73 targets into one integrated governance and operational-intelligence release.

## Included targets
1. Dataset and column lineage, upstream/downstream traversal, impact analysis and JSON export.
2. Pipeline run metrics, SLA evaluation, alert routing and portable audit reports.
3. Declarative dashboard definitions and a safe React component renderer.

## Integrated example
```python
from pealang import DatasetRef, ColumnRef, LineageGraph
from pealang import RunMetric, SLAPolicy, SLAEvaluator, AuditReport
from pealang import Dashboard, render_react

raw = DatasetRef("employees_raw", "hr")
clean = DatasetRef("employees_clean", "hr")
lineage = LineageGraph().connect(raw, clean, "cleanse")
metric = RunMetric("daily_hr", "run-1", "start", "finish", 42, "success", 3)
alerts = SLAEvaluator().evaluate(metric, SLAPolicy(max_duration_seconds=60))
report = AuditReport.build(metric, alerts, lineage)
ui = render_react(Dashboard("HR Operations").add("metric", "Duration", source="run"))
```

