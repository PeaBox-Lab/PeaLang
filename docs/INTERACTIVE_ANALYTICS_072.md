


# PeaLang v0.72 Interactive Analytics

v0.72 merges the former 0.74, 0.75 and 0.76 targets into one release.

## Interactive dashboards
Dashboard filters support select, multi-select, text, numeric/date equality and ranges. `DashboardState` tracks filters, selections and paging. `DataBinding` maps datasets to chart/table fields.

## Browser REPL and Dataset Inspector
`BrowserREPL` provides a JSON-friendly, transport-neutral protocol. The host supplies the executor so browser capability policy remains explicit. `DatasetInspector` exposes schema, bounded row preview and column profiles.

## Jupyter and rich output
`PeaKernel` implements the execution-result contract and kernel metadata. `RichDisplay` produces plain text, HTML tables and `application/vnd.pealang.dataframe+json`. `pealang.jupyter_kernel` is an optional ipykernel adapter; install `ipykernel` to launch it.



