# Code formatter, linter, and AST macros (v1.2.0)

PeaLang provides AST-based code formatting, static linting, and auto-fix codemods.

## Key functions

- `analysis.format_source_ast(source)` — AST-based formatting
- `analysis.PeaFormatter(indent_size)` — formatter class
- `analysis.lint_source_ast(source)` — static linting
- `analysis.PeaLinter()` — linter class
- `analysis.codemod_remove_unused_imports(source)` — remove unused imports
- `analysis.codemod_rename_variable(source, old, new)` — rename variable
- `analysis.codemod_fix_naming(source)` — fix naming conventions