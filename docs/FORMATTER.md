# Code formatter, linter, and AST macros (v1.2.0)

PeaLang provides AST-based code formatting, static linting, and auto-fix codemods.

## Formatter

- `format_source_ast(source)` — AST-based code formatting
- `PeaFormatter(indent_size)` — configurable formatter class

## Linter

- `lint_source_ast(source)` — static linting (dead code, complexity, naming, style)
- `PeaLinter()` — configurable linter class

## Codemods

- `codemod_remove_unused_imports(source)` — remove unused imports
- `codemod_rename_variable(source, old_name, new_name)` — rename variable
- `codemod_fix_naming(source)` — fix naming conventions (camelCase to snake_case)