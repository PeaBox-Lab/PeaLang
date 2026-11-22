"""Regression coverage for v1.2.0 formatter and linter."""

from pealang.formatter import (
    build_formatter_namespace,
    PeaFormatter,
    FormatConfig,
    format_source_ast,
    PeaLinter,
    LintConfig,
    lint_source_ast,
    codemod_remove_unused_imports,
    codemod_rename_variable,
    codemod_fix_naming,
    codemod_remove_unused_variables,
    codemod_simplify_returns,
    codemod_remove_debug_prints,
    codemod_organize_imports,
    apply_codemods,
    format_and_lint,
)


def test_format_source_ast():
    src = "let x=1\n"
    formatted = format_source_ast(src)
    assert isinstance(formatted, str)
    assert len(formatted) > 0


def test_pea_formatter():
    config = FormatConfig(indent_size=4)
    fmt = PeaFormatter(config=config)
    result = fmt.format("let x = 1")
    assert isinstance(result, str)
    assert len(result) > 0


def test_pea_formatter_with_config():
    config = FormatConfig(indent_size=2, brace_style="next_line")
    fmt = PeaFormatter(config=config)
    result = fmt.format("let x = 1")
    assert isinstance(result, str)
    assert len(result) > 0


def test_lint_source_ast():
    src = "let x = 1\nfunction foo() {\nlet y = 2\nreturn y\nlet z = 3\n}\n"
    issues = lint_source_ast(src)
    assert isinstance(issues, list)
    # Should detect unreachable code
    assert any("Unreachable" in i["message"] for i in issues)


def test_pea_linter_complexity():
    linter = PeaLinter()
    src = "function big() {\n" + "if (x > 0) { return 1 }\n" * 15 + "return 0\n}\n"
    issues = linter.lint(src)
    assert any("complexity" in i["message"].lower() or "long" in i["message"].lower() for i in issues)


def test_codemod_rename_variable():
    src = "let x = 1\nlet y = x + 2\n"
    result = codemod_rename_variable(src, "x", "z")
    assert "let z = 1" in result
    assert "let y = z + 2" in result


def test_codemod_fix_naming():
    src = "function MyFunc() { return 1 }\n"
    result = codemod_fix_naming(src)
    assert "my_func" in result


def test_codemod_remove_unused_imports():
    src = "import unused\nlet x = 1\n"
    result = codemod_remove_unused_imports(src)
    assert "import unused" not in result


def test_new_codemods():
    # Test new codemods are exported and work
    src = "let x = 1\nlet y = 2\nreturn x\n"
    result = apply_codemods(src, ["simplify_returns", "remove_debug_prints"])
    assert isinstance(result, str)


def test_format_and_lint():
    src = "let x=1\nfunction foo() { return 1 }\n"
    formatted, issues = format_and_lint(src)
    assert isinstance(formatted, str)
    assert isinstance(issues, list)


def test_build_formatter_namespace():
    ns = build_formatter_namespace()
    assert "PeaFormatter" in ns
    assert "format_source_ast" in ns
    assert "PeaLinter" in ns
    assert "lint_source_ast" in ns
    assert "FormatConfig" in ns
    assert "LintConfig" in ns
    assert "codemod_remove_unused_imports" in ns
    assert "codemod_fix_naming" in ns
    assert "codemod_simplify_returns" in ns
    assert "apply_codemods" in ns
    assert "format_and_lint" in ns
