# Notebook-rich display hooks (v129)

PeaLang provides rich display helpers for Jupyter notebooks and other
interactive environments.  Each helper returns a ``RichResult`` carrying
multiple MIME bundles (``text/plain``, ``text/html``, ``text/markdown``,
``application/json``) so the notebook can pick the best representation.

## Available helpers

- ``analysis.display_records(rows)`` - Rich table for a list of record dicts
- ``analysis.display_profile(profile)`` - Rich card for a data profile
- ``analysis.display_model(model)`` - Rich card for a fitted model
- ``analysis.display_evaluation(eval)`` - Rich card for an evaluation result
- ``analysis.display_chart(chart)`` - Rich rendering of a chart spec
- ``analysis.display_report(report)`` - Rich rendering of a report

All helpers are also available through ``stats`` / ``std.stats``.

## RichResult

Each helper returns a ``pealang.jupyter.RichResult`` with a ``data`` dict
mapping MIME types to rendered content and a ``metadata`` dict.