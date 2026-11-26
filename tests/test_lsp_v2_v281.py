"""Phase 81: deterministic LSP v2 layer with reviewable editor features."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
import pytest
from pealang.analysis import build_analysis_namespace
from pealang.compatibility import Stability, feature_status
from pealang.core_freeze import core_freeze_report
from pealang.help import help as pea_help
from pealang.lsp_v2 import DocumentStore, LspV2Error, LspV2Server
from pealang.specification import SPEC_VERSION

SOURCE = 'function foo() { return 1 }\nlet x = 2\nprint x'


def server_with_source():
    server = LspV2Server()
    opened = server.handle_did_open({
        'textDocument': {'uri': 'file:///app.pea', 'text': SOURCE, 'version': 1},
    })
    return server, opened


def test_lsp_v2_constants_and_capabilities_are_versioned():
    caps = pealang.lsp_v2_capabilities()
    assert pealang.LSP_V2_VERSION == '3.1.44'
    assert pealang.LSP_V2_PROTOCOL_VERSION == '3.17.0'
    assert pealang.LSP_V2_FORMAT == 'pea-lsp-v2'
    assert caps == pealang.lsp_v2_capabilities()
    assert caps['serverInfo'] == {'name': 'pealang-lsp-v2', 'version': '3.1.44'}
    capabilities = caps['capabilities']
    assert capabilities['textDocumentSync']['change'] == 2
    for name in ('hoverProvider', 'definitionProvider', 'referencesProvider',
                 'renameProvider', 'documentSymbolProvider',
                 'workspaceSymbolProvider', 'documentFormattingProvider',
                 'inlayHintProvider', 'foldingRangeProvider'):
        assert capabilities[name] is True
    assert capabilities['semanticTokensProvider']['legend']['tokenTypes'][0] == 'keyword'


def test_document_store_supports_full_and_incremental_changes():
    store = DocumentStore()
    original = store.open('file:///a.pea', 'let x = 1\nprint x')
    assert original.version == 1
    assert original.digest == store.get('file:///a.pea').digest
    updated = store.change('file:///a.pea', [{
        'range': {'start': {'line': 0, 'character': 8},
                  'end': {'line': 0, 'character': 9}},
        'newText': '42',
    }])
    assert updated.text == 'let x = 42\nprint x'
    assert updated.version == 2
    assert updated.digest != original.digest
    replaced = store.change('file:///a.pea', [{'text': 'print 7\n'}], version=9)
    assert replaced.text == 'print 7\n'
    assert replaced.version == 9
    assert store.digest() == store.digest()
    assert store.close('file:///a.pea') is True
    assert store.close('file:///a.pea') is False
    with pytest.raises(LspV2Error):
        store.get('file:///a.pea')
    with pytest.raises(LspV2Error):
        store.change('file:///missing.pea', [{'text': 'x'}])


def test_server_diagnostics_symbols_and_workspace_symbols():
    server, opened = server_with_source()
    assert opened['version'] == 1
    assert opened['diagnostics'] == []
    symbols = server.document_symbols('file:///app.pea')
    assert [item['name'] for item in symbols] == ['foo', 'x']
    assert symbols[0]['kind'] == 12
    assert symbols[1]['kind'] == 13
    workspace = server.workspace_symbols('fo')
    assert len(workspace) == 1
    assert workspace[0]['name'] == 'foo'
    assert workspace[0]['location']['uri'] == 'file:///app.pea'


def test_hover_definition_references_and_rename_are_deterministic():
    server, _ = server_with_source()
    position = {'line': 2, 'character': 6}
    hover = server.hover('file:///app.pea', position)
    assert hover is not None
    assert '`x`' in hover['contents']['value']
    assert hover == server.hover('file:///app.pea', position)
    definition = server.definition('file:///app.pea', position)
    assert definition['range'] == server.document_symbols('file:///app.pea')[1]['range']
    references = server.references('file:///app.pea', position)
    assert references == server.references('file:///app.pea', position)
    assert [(item['range']['start']['line'], item['range']['start']['character'])
            for item in references] == [(1, 4), (2, 6)]
    renamed = server.rename('file:///app.pea', position, 'value')
    edits = renamed['changes']['file:///app.pea']
    assert len(edits) == 2
    assert all(edit['newText'] == 'value' for edit in edits)
    assert server.hover('file:///app.pea', {'line': 0, 'character': 0}) is None
    with pytest.raises(LspV2Error):
        server.rename('file:///app.pea', position, 'not valid')


def test_completion_formatting_folding_and_semantic_tokens_are_reviewable():
    server, _ = server_with_source()
    completion = server.completion('file:///app.pea')
    labels = [item['label'] for item in completion['items']]
    assert completion['isIncomplete'] is False
    assert labels == sorted(labels)
    assert 'function' in labels and 'foo' in labels and 'x' in labels
    assert server.formatting('file:///app.pea') == []
    assert server.folding_ranges('file:///app.pea') == [
        {'startLine': 0, 'endLine': 0, 'kind': 'region'}]
    assert server.inlay_hints('file:///app.pea') == []
    tokens = server.semantic_tokens('file:///app.pea')['data']
    assert tokens and len(tokens) % 5 == 0
    assert tokens == server.semantic_tokens('file:///app.pea')['data']


def test_json_rpc_dispatch_covers_requests_notifications_and_shutdown():
    server = LspV2Server()
    init = server.handle_message({
        'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
        'params': {'rootUri': 'file:///workspace'},
    })
    assert init['id'] == 1
    assert init['result']['serverInfo']['version'] == '3.1.44'
    assert server.initialized is True
    assert server.handle_message({'jsonrpc': '2.0', 'method': 'initialized'}) is None
    assert server.handle_message({
        'jsonrpc': '2.0', 'method': 'textDocument/didOpen',
        'params': {'textDocument': {'uri': 'file:///app.pea', 'text': SOURCE}},
    }) is None
    symbols = server.handle_message({
        'jsonrpc': '2.0', 'id': 2, 'method': 'textDocument/documentSymbol',
        'params': {'textDocument': {'uri': 'file:///app.pea'}},
    })
    assert [item['name'] for item in symbols['result']] == ['foo', 'x']
    assert server.handle_message({
        'jsonrpc': '2.0', 'method': 'textDocument/didChange',
        'params': {'textDocument': {'uri': 'file:///app.pea', 'version': 2},
                   'contentChanges': [{'text': 'print 1\n'}]},
    }) is None
    assert server.store.get('file:///app.pea').version == 2
    assert server.handle_message({'jsonrpc': '2.0', 'id': 3,
                                  'method': 'shutdown'})['result'] is None
    assert server.shutdown is True
    assert server.handle_message({'jsonrpc': '2.0', 'method': 'exit'}) is None


def test_report_and_gate_are_deterministic_and_enforced():
    server, _ = server_with_source()
    first = pealang.lsp_v2_report(server)
    second = pealang.lsp_v2_report(server)
    assert first == second
    assert first['version'] == pealang.LSP_V2_VERSION == '3.1.44'
    assert first['format'] == pealang.LSP_V2_FORMAT
    assert first['protocol_version'] == '3.17.0'
    assert first['document_count'] == 1
    assert len(first['digest']) == 64
    assert first['diagnostics'] == {'file:///app.pea': []}
    assert pealang.lsp_v2_gate(first) == {'gate': 'PASS', 'issues': []}
    assert 'version' in pealang.lsp_v2_gate({'version': 'old'})['issues']
    assert 'capabilities' in pealang.lsp_v2_gate({
        'version': '3.1.44', 'format': 'pea-lsp-v2', 'gate': 'PASS',
        'capabilities': {}, 'digest': 'x' * 64,
    })['issues']


def test_cli_capabilities_and_check_report(tmp_path):
    root = Path(__file__).resolve().parent.parent
    caps_result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'lsp', '--capabilities'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert caps_result.returncode == 0, caps_result.stderr
    assert json.loads(caps_result.stdout)['serverInfo']['version'] == '3.1.44'
    source = tmp_path / 'app.pea'
    report_path = tmp_path / 'lsp.json'
    source.write_text(SOURCE + '\n', encoding='utf-8')
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'lsp', str(source), '--check',
         '--symbols', '--emit', str(report_path)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['version'] == '3.1.44'
    assert report['diagnostics'] == []
    assert [item['name'] for item in report['symbols']] == ['foo', 'x']
    assert report['gate'] == 'PASS'
    assert len(report['report_digest']) == 64
    assert json.loads(report_path.read_text(encoding='utf-8')) == report


def test_feature_flag_help_and_analysis_namespace_document_lsp_v2():
    assert feature_status('editor.lsp_v2').stability == Stability.STABLE
    text = pea_help('lsp')
    assert 'pea lsp' in text
    assert 'DocumentStore ->' in text
    namespace = build_analysis_namespace()
    for name in ('LspV2Server', 'DocumentStoreV2', 'LspV2Capabilities',
                 'LspV2Report', 'LspV2Gate', 'LspV2Namespace'):
        assert name in namespace


def test_release_metadata_is_aligned():
    assert pealang.__version__ == SPEC_VERSION == '5.11.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.11.0'
    assert manifest['previous_version'] == '5.10.0'
    assert pealang.LSP_V2_VERSION == '3.1.44'
    assert pealang.PARALLEL_RUNTIME_VERSION == '3.1.43'
    assert pealang.RUNTIME_PROFILER_VERSION == '3.1.43'
    assert pealang.WASM_BACKEND_VERSION == '3.1.42'
    assert pealang.NATIVE_BACKEND_VERSION == '3.1.41'
    assert pealang.BYTECODE_JIT_VERSION == '3.1.40'
    assert pealang.FAST_INTERPRETER_VERSION == '3.1.39'
    assert pealang.OPTIMIZER_VERSION == '3.1.38'
    assert pealang.CORE_RELEASE_FROZEN_AT == '3.1.37'


def test_frozen_core_gate_still_passes():
    report = core_freeze_report()
    assert report['release'] == '3.1.37'
    assert report['freeze']['gate'] == 'PASS'
    assert report['freeze']['digest'] == (
        '2e9f93e8506331d00131a33c3b99d799c3893d5f3ea1680acd3d2458327d461d')
