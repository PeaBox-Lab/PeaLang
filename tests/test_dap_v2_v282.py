"""Phase 82: deterministic DAP v2 debugger with reproducible VM sessions."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
import pytest
from pealang.analysis import build_analysis_namespace
from pealang.compatibility import Stability, feature_status
from pealang.core_freeze import core_freeze_report
from pealang.dap_v2 import (DAP_V2_COMMANDS, DAP_V2_FORMAT,
                            DAP_V2_PROTOCOL_VERSION, DAP_V2_VERSION,
                            DapV2Error, DapV2Session, build_dap_v2_namespace,
                            dap_v2_capabilities, dap_v2_gate, dap_v2_report)
from pealang.help import help as pea_help
from pealang.specification import SPEC_VERSION

SOURCE = 'let x = 5\nprint x\n'


def run_to_termination(session, *, first=True, limit=20):
    status = (session.configuration_done() if first
              else session.continue_run())
    while (not session.terminated
           and status.get('reason') == 'breakpoint' and limit > 0):
        status = session.continue_run()
        limit -= 1
    return status


def test_dap_v2_constants_and_capabilities_are_versioned():
    caps = dap_v2_capabilities()
    assert DAP_V2_VERSION == pealang.DAP_V2_VERSION == '3.1.45'
    assert DAP_V2_PROTOCOL_VERSION == pealang.DAP_V2_PROTOCOL_VERSION == '1.68.0'
    assert DAP_V2_FORMAT == pealang.DAP_V2_FORMAT == 'pea-dap-v2'
    assert caps == dap_v2_capabilities()
    assert caps['supportsConfigurationDoneRequest'] is True
    assert caps['supportsConditionalBreakpoints'] is True
    assert caps['supportsHitConditionalBreakpoints'] is True
    assert caps['supportsSetVariable'] is True
    assert caps['supportsStepBack'] is False
    assert caps['supportsStepInTargetsRequest'] is False
    assert DAP_V2_COMMANDS == tuple(sorted(DAP_V2_COMMANDS))
    for name in ('initialize', 'launch', 'setBreakpoints', 'continue',
                 'next', 'stackTrace', 'scopes', 'variables', 'disconnect'):
        assert name in DAP_V2_COMMANDS


def test_launch_breakpoints_resume_and_events_are_reproducible():
    with pytest.raises(DapV2Error):
        DapV2Session().set_breakpoints(None, [{'line': 1}])
    session = DapV2Session()
    session.initialize()
    launch = session.launch(source=SOURCE)
    assert launch['verified'] is True
    assert launch['lines'] == [1, 2]
    assert session.launched is True
    result = session.set_breakpoints(None,
                                     [{'line': 2}, {'line': 999}])
    assert len(result['breakpoints']) == 1
    assert result['breakpoints'][0] == {
        'id': 1, 'verified': True, 'line': 2, 'source': '<input>',
    }
    assert session.breakpoints[0].condition is None
    assert session.configuration_done()['line'] == 2
    assert session.continue_run()['reason'] == 'breakpoint'
    status = run_to_termination(session, first=False)
    assert status == {'reason': 'terminated'}
    assert session.terminated is True
    assert session.output == ('5',)
    events = [event['event'] for event in session.events]
    assert events[0] == 'initialized'
    assert 'breakpoint' in events
    assert 'stopped' in events
    assert events[-1] == 'terminated'
    assert [event['seq'] for event in session.events] == list(
        range(1, len(session.events) + 1))
    assert all('/' not in str(event['body'].get('source', ''))
               for event in session.events)


def test_conditional_and_hit_conditional_breakpoints_are_stable():
    skipped = DapV2Session()
    skipped.initialize()
    skipped.launch(source=SOURCE)
    skipped.set_breakpoints(None, [{'line': 2, 'condition': 'x == 1'}])
    assert skipped.configuration_done() == {'reason': 'terminated'}
    assert skipped.terminated is True
    assert skipped.output == ('5',)
    assert skipped.breakpoints[0].hits >= 1
    assert any(event['body'].get('reason') == 'conditionNotMet'
               for event in skipped.events)

    counted = DapV2Session()
    counted.initialize()
    counted.launch(source=SOURCE)
    counted.set_breakpoints(None, [{'line': 2, 'hitCondition': 'hits == 1'}])
    assert counted.configuration_done()['reason'] == 'breakpoint'
    assert counted.breakpoints[0].hits >= 1
    assert run_to_termination(counted, first=False) == {'reason': 'terminated'}
    assert counted.output == ('5',)


def test_stack_scopes_variables_and_evaluation_are_reviewable():
    session = DapV2Session()
    session.initialize()
    session.launch(source=SOURCE)
    session.set_breakpoints(None, [{'line': 2}])
    assert session.configuration_done()['reason'] == 'breakpoint'
    frames = session.stack_trace()
    assert len(frames) == 1
    assert frames[0]['id'] == 1001
    assert frames[0]['name'] == '<module>'
    assert frames[0]['source'] == {'name': '<input>', 'path': '<input>'}
    scopes = session.scopes(1001)['scopes']
    assert [item['name'] for item in scopes] == ['Locals', 'Globals']
    assert [item['variablesReference'] for item in scopes] == [1001, 2000]
    variables = session.variables(1001)['variables']
    assert variables == [{'name': 'x', 'value': '5', 'type': 'int',
                          'variablesReference': 0}]
    assert session.variables(2000)['variables'] == variables
    assert session.evaluate('x', 1001) == {
        'result': '5', 'variablesReference': 0,
    }
    assert session.evaluate('7') == {'result': '7', 'variablesReference': 0}
    assert session.threads()['threads'] == [
        {'id': 1, 'name': 'PeaLang main', 'running': True},
    ]
    assert session.exception_info() == {
        'exceptionId': 'PeaLangVMError', 'breakMode': 'unhandled',
        'description': 'VM exception',
    }
    assert session.disconnect() == {}
    assert session.terminated is True


def test_json_rpc_dispatch_returns_ordered_responses_and_errors():
    session = DapV2Session()
    requests = [
        {'seq': 1, 'command': 'initialize'},
        {'seq': 2, 'command': 'launch', 'arguments': {'source': SOURCE}},
        {'seq': 3, 'command': 'setBreakpoints',
         'arguments': {'breakpoints': [{'line': 2}]}},
        {'seq': 4, 'command': 'configurationDone'},
        {'seq': 5, 'command': 'stackTrace'},
        {'seq': 6, 'command': 'scopes', 'arguments': {'frameId': 1001}},
        {'seq': 7, 'command': 'variables',
         'arguments': {'variablesReference': 1001}},
        {'seq': 8, 'command': 'evaluate',
         'arguments': {'expression': 'x', 'frameId': 1001}},
        {'seq': 9, 'command': 'next'},
        {'seq': 10, 'command': 'continue'},
    ]
    for request in requests:
        response = session.handle_message(request)
        assert response['success'] is True
        assert response['request_seq'] == request['seq']
        assert response['command'] == request['command']
    assert [response['seq'] for response in [
        session.handle_message({'seq': 11, 'command': 'threads'}),
        session.handle_message({'seq': 12, 'command': 'exceptionInfo'}),
        session.handle_message({'seq': 13, 'command': 'disconnect'}),
    ]] == [11, 12, 13]
    assert session.terminated is True
    for name in ('initialize', 'launch', 'setBreakpoints', 'continue', 'next',
                 'stackTrace', 'scopes', 'variables', 'disconnect'):
        assert name in session.handled_commands
    bad = DapV2Session().handle_message({'seq': 1, 'command': 'next'})
    assert bad['success'] is False
    assert 'launch the program' in bad['message']


def test_report_and_gate_ignore_host_paths_and_enforce_shape():
    first_session = DapV2Session(source_name='C:\\work\\app.pea')
    first_session.initialize()
    first_session.launch(source=SOURCE)
    first_session.set_breakpoints('C:\\work\\app.pea', [{'line': 2}])
    run_to_termination(first_session)
    second_session = DapV2Session(source_name='/other/app.pea')
    second_session.initialize()
    second_session.launch(source=SOURCE)
    second_session.set_breakpoints('/other/app.pea', [{'line': 2}])
    run_to_termination(second_session)
    first = dap_v2_report(first_session)
    second = dap_v2_report(second_session)
    assert first == dap_v2_report(first_session)
    assert first['version'] == DAP_V2_VERSION == '3.1.45'
    assert first['format'] == DAP_V2_FORMAT
    assert first['protocol_version'] == DAP_V2_PROTOCOL_VERSION
    assert first['conformance'] == {'passed': True, 'missing': []}
    assert first['output'] == ['5']
    assert len(first['digest']) == len(first['snapshot_fingerprint']) == 64
    assert first['source_name'] != second['source_name']
    assert first['digest'] == second['digest']
    assert dap_v2_gate(first) == {'gate': 'PASS', 'issues': []}
    assert 'version' in dap_v2_gate({**first, 'version': 'old'})['issues']
    assert 'conformance' in dap_v2_gate({
        **first, 'conformance': {'passed': False, 'missing': ['launch']},
    })['issues']
    assert 'digest' in dap_v2_gate({**first, 'digest': 'short'})['issues']


def test_cli_capabilities_and_check_report(tmp_path):
    root = Path(__file__).resolve().parent.parent
    caps_result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'dap-v2', '--capabilities'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert caps_result.returncode == 0, caps_result.stderr
    caps = json.loads(caps_result.stdout)
    assert caps['supportsConfigurationDoneRequest'] is True
    assert caps['supportsConditionalBreakpoints'] is True
    source = tmp_path / 'app.pea'
    report_path = tmp_path / 'dap.json'
    source.write_text(SOURCE, encoding='utf-8')
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'dap-v2', str(source),
         '--breakpoint', '2', '--check', '--emit', str(report_path)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['version'] == '3.1.45'
    assert report['verified'] is True
    assert report['stops'][-1]['reason'] == 'terminated'
    assert report['output'] == ['5']
    assert report['gate'] == 'PASS'
    assert len(report['report_digest']) == 64
    assert json.loads(report_path.read_text(encoding='utf-8')) == report


def test_feature_flag_help_and_analysis_namespace_document_dap_v2():
    assert feature_status('debug.dap_v2').stability == Stability.STABLE
    text = pea_help('dap-v2')
    assert 'pea dap-v2' in text
    assert 'DapV2Session ->' in text
    namespace = build_dap_v2_namespace()
    assert namespace['DAP_V2_VERSION'] == '3.1.45'
    assert namespace['build_dap_v2_namespace'] is build_dap_v2_namespace
    analysis = build_analysis_namespace()
    for name in ('DapV2Session', 'DapBreakpoint', 'DapV2Capabilities',
                 'DapV2Report', 'DapV2Gate', 'DapV2Namespace'):
        assert name in analysis


def test_release_metadata_is_aligned_and_component_pins_hold():
    assert pealang.__version__ == SPEC_VERSION == '5.26.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.26.0'
    assert manifest['previous_version'] == '5.25.0'
    assert pealang.DAP_V2_VERSION == '3.1.45'
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
