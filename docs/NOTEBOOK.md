# Notebook-rich display hooks (v129)

PeaLang provides rich display helpers for Jupyter notebooks and other
interactive environments.  Each helper returns a ``RichResult`` carrying
multiple MIME bundles (``text/plain``, ``text/html``, ``text/markdown``,
``application/json``) so the notebook can pick the best representation.

## Available helpers

| Helper | Description |
|--------|-------------|
| ``analysis.display_records(rows)`` | Rich table for a list of record dicts |
| ``analysis.display_profile(profile)`` | Rich card for a data profile |
| ``analysis.display_model(model)`` | Rich card for a fitted model |
| ``analysis.display_evaluation(eval)`` | Rich card for an evaluation result |
| ``analysis.display_chart(chart)`` | Rich rendering of a chart spec |
| ``analysis.display_report(report)`` | Rich rendering of a report |

All helpers are also available through ``stats`` / ``std.stats``.

## Example

```python
from pealang.analysis import display_records, display_profile

rows = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
rich = display_records(rows, title="People")
print(rich.data["text/markdown"])
```

## RichResult

Each helper returns a ``pealang.jupyter.RichResult`` with a ``data`` dict
mapping MIME types to rendered content and a ``metadata`` dict.
