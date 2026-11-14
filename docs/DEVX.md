# Developer experience (v137)

PeaLang provides developer experience and tooling enhancements.

## Error suggestions

- `analysis.suggest_fix(error_msg)` — suggest fixes for an error
- `analysis.explain_error_detailed(error, source, line)` — detailed error explanation with context

## Project scaffolding

- `analysis.project_scaffold(name, template, target_dir)` — scaffold a new project

## Code metrics

- `analysis.code_metrics(source)` — compute code metrics (lines, functions, variables, comments)

## Linting

- `analysis.lint_source(source)` — basic linting (trailing whitespace, long lines, TODOs)

## Formatting

- `analysis.format_source(source)` — basic source formatting (indentation)

## Dependency check

- `analysis.dependency_check(manifest_path)` — check project dependencies