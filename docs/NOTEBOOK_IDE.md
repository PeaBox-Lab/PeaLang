# Interactive Web Data IDE and reactive notebook server (v1.8.0)

PeaLang provides a self-hosted Web Data IDE with reactive cell execution.

## Reactive notebook

- `ReactiveCell(cell_id, source, dependencies)` — reactive cell
- `ReactiveNotebook()` — reactive notebook with dependency tracking
- `.add_cell(id, source, deps)` — add cell
- `.remove_cell(id)` — remove cell
- `.update_cell(id, source)` — update cell
- `.execution_order()` — topological sort
- `.mark_dirty(id)` — mark cell and dependents dirty

## Visual inspectors

- `inspect_dataframe(data)` — visual DataFrame inspection
- `inspect_sql_result(query, result)` — visual SQL result inspection

## Web app publishing

- `publish_as_webapp(source, title, template)` — generate web app from .pea script
- `generate_notebook_html(cells)` — generate HTML notebook