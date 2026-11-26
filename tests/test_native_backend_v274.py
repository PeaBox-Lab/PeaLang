"""Phase 74: deterministic native backend with VM parity and fallback."""

import json
import subprocess
import sys
from pathlib import Path

import pealang
import pytest
from pealang.analysis import build_analysis_namespace
from pealang.compatibility import Stability, feature_status
from pealang.compiler import compile_source_to_bytecode
from pealang.core_freeze import core_freeze_report
from pealang.help import help as pea_help
from pealang.specification import SPEC_VERSION


INT_LOOP = 'let i = 0\nwhile i < 3 { print i\n i = i + 1 }'
FLOAT_LOOP = 'let i = 0.0\nwhile i < 3 { print i\n i = i + 1.0 }'
STRING_ADD = 'print "pea" + "lang"'
FUNCTION = 'function f(a) { return a + 1 }\nprint f(3)'


def test_native_supported_and_lowering_is_deterministic():
    module = compile_source_to_bytecode(INT_LOOP)
    assert pealang.native_supported(module)
    first = pealang.compile_native(module)
    second = pealang.compile_native(module)
    assert first == second
    assert first.format == pealang.NATIVE_FORMAT == 'pea-native-ir-v1'
    assert first.supported
    assert first.digest == second.digest
    assert first.instructions
    assert all(isinstance(item, pealang.NativeInstruction)
               for item in first.instructions)
    assert '/* PeaLang native backend 3.1.41 */' in first.source
    assert '#include <stdio.h>' in first.source
    assert 'OP_JUMP_IF_FALSE' in first.source


def test_native_artifact_can_be_saved(tmp_path):
    module = compile_source_to_bytecode(INT_LOOP)
    target = tmp_path / 'app.c'
    artifact = pealang.compile_native(module)
    artifact.save(target)
    assert target.read_text(encoding='utf-8') == artifact.source


def test_native_runtime_matches_vm_for_int_loop():
    module = compile_source_to_bytecode(INT_LOOP)
    output = []
    runtime = pealang.NativeRuntime(output.append)
    assert runtime.run(module) is None
    assert output == [0, 1, 2]
    assert runtime.last_report['mode'] == 'native'
    assert runtime.last_report['supported']
    assert runtime.last_report['instructions'] > 0
    assert runtime.last_report['digest'] == pealang.compile_native(module).digest


def test_native_runtime_handles_float_and_string_values():
    for source, expected in ((FLOAT_LOOP, [0.0, 1.0, 2.0]),
                             (STRING_ADD, ['pealang'])):
        output = []
        runtime = pealang.NativeRuntime(output.append)
        runtime.run(compile_source_to_bytecode(source))
        assert output == expected
        assert runtime.last_report['mode'] == 'native'


def test_unsupported_modules_fall_back_to_vm():
    module = compile_source_to_bytecode(FUNCTION)
    assert not pealang.native_supported(module)
    artifact = pealang.compile_native(module)
    assert not artifact.supported
    assert artifact.instructions == ()
    output = []
    runtime = pealang.NativeRuntime(output.append)
    runtime.run(module)
    assert output == [4]
    assert runtime.last_report['mode'] == 'vm'
    assert runtime.last_report['digest'] == artifact.digest


def test_native_runtime_enforces_global_instruction_limit():
    module = compile_source_to_bytecode(INT_LOOP)
    with pytest.raises(pealang.VMError):
        pealang.NativeRuntime(lambda _value: None, max_instructions=1).run(module)


def test_verify_native_parity_passes_on_supported_and_fallback_paths():
    for source in (INT_LOOP, FLOAT_LOOP, STRING_ADD, FUNCTION):
        parity = pealang.verify_native_parity(compile_source_to_bytecode(source))
        assert parity['ok'], (source, parity)
        assert parity['output_match'] and parity['result_match']


def test_native_report_is_stable_and_gated():
    module = compile_source_to_bytecode(INT_LOOP)
    first = pealang.native_report(module, verify=True)
    second = pealang.native_report(module, verify=True)
    assert first == second
    assert first['version'] == pealang.NATIVE_BACKEND_VERSION == '3.1.41'
    assert first['format'] == pealang.NATIVE_FORMAT
    assert first['mode'] == 'native'
    assert first['native_supported']
    assert first['output'] == ['0', '1', '2']
    assert first['parity']['ok']
    benchmarked = pealang.native_report(module, benchmark=True)
    assert benchmarked['benchmark']['iterations'] == 25
    assert benchmarked['benchmark']['vm_median_ms'] >= 0
    assert benchmarked['benchmark']['native_median_ms'] >= 0
    assert pealang.native_gate(first) == {'gate': 'PASS', 'issues': []}


def test_gate_rejects_invalid_mode_compilation_and_failed_parity():
    assert pealang.native_gate({'mode': 'unknown'})['gate'] == 'FAIL'
    broken = pealang.native_gate({'mode': 'native', 'gate': 'FAIL'})
    assert 'compilation' in broken['issues']
    failed = pealang.native_gate(
        {'mode': 'native', 'gate': 'PASS', 'parity': {'ok': False}})
    assert failed['gate'] == 'FAIL'
    assert 'parity' in failed['issues']


def test_cli_native_command_passes_with_parity_and_emit(tmp_path):
    source = tmp_path / 'app.pea'
    artifact = tmp_path / 'app.c'
    source.write_text(INT_LOOP + '\n', encoding='utf-8')
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'native', str(source),
         '--verify', '--emit', str(artifact)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['mode'] == 'native'
    assert report['parity']['ok']
    assert report['version'] == '3.1.41'
    assert report['instructions'] > 0
    assert 'PeaLang native backend 3.1.41' in artifact.read_text(encoding='utf-8')


def test_cli_native_fallback_and_optimize_flag(tmp_path):
    source = tmp_path / 'app.pea'
    source.write_text(FUNCTION + '\n', encoding='utf-8')
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'native', str(source),
         '--verify', '--optimize'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['mode'] == 'vm'
    assert report['parity']['ok']


def test_feature_flag_help_and_analysis_namespace_document_native():
    assert feature_status('runtime.native_backend_v3').stability == Stability.STABLE
    text = pea_help('native')
    assert 'pea native' in text
    assert 'verify_native_parity()' in text
    namespace = build_analysis_namespace()
    for name in ('NativeRuntime', 'CompileNative', 'VerifyNativeParity',
                 'BenchmarkNative', 'NativeReport', 'NativeNamespace'):
        assert name in namespace


def test_release_metadata_is_aligned():
    assert pealang.__version__ == SPEC_VERSION == '3.1.57'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '3.1.57'
    assert manifest['previous_version'] == '3.1.56'
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
