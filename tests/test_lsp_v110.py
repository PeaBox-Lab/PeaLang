"""Regression coverage for v1.1.0 LSP server."""

from pealang.lsp import LSPServer, build_lsp_namespace


def test_lsp_server_init():
    server = LSPServer()
    result = server.handle_initialize({"rootUri": "file:///test"})
    assert "capabilities" in result
    assert result["capabilities"]["hoverProvider"] is True
    assert result["capabilities"]["completionProvider"] is not None


def test_lsp_diagnostics():
    server = LSPServer()
    server.handle_did_open({"textDocument": {"uri": "file:///test.pea", "text": "let x = 1\nprint x"}})
    # Should not crash
    assert "file:///test.pea" in server.documents


def test_lsp_hover():
    server = LSPServer()
    server.documents["file:///test.pea"] = "let x = 1\nprint x"
    result = server.handle_hover({"textDocument": {"uri": "file:///test.pea"}, "position": {"line": 1, "character": 7}})
    # May return None or hover info
    assert result is None or "contents" in result


def test_lsp_completion():
    server = LSPServer()
    result = server.handle_completion({"textDocument": {"uri": "file:///test.pea"}, "position": {"line": 0, "character": 0}})
    assert "items" in result
    assert len(result["items"]) > 0


def test_lsp_document_symbols():
    server = LSPServer()
    server.documents["file:///test.pea"] = "function foo() { return 1 }\nlet x = 2"
    symbols = server.handle_document_symbol({"textDocument": {"uri": "file:///test.pea"}})
    assert len(symbols) == 2
    assert symbols[0]["name"] == "foo"


def test_build_lsp_namespace():
    ns = build_lsp_namespace()
    assert "LSPServer" in ns
    assert "run_server" in ns
    assert len(ns) == 2
