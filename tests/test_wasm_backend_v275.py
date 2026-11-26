"""Phase 75: deterministic WASM backend with artifact inspection and parity."""

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
STRING_ADD = 'print "pea" + "wasm"'
FUNCTION = 'function f(a) { return a + 1 }\nprint f(3)'


def test_wasm_backend_supported_and_lowering_is_deterministic():
    module = compile_source_to_bytecode(INT_LOOP)
    assert pealang.wasm_backend_supported(module)
    first = pealang.compile_wasm_backend(module)
    second = pealang.compile_wasm_backend(module)
    assert first == second
    assert first.format == pealang.WASM_BACKEND_FORMAT == 'pea-wasm-backend-v1'
    assert first.supported
    assert first.digest == second.digest
    assert first.instructions
    assert all(isinstance(item, pealang.WasmBackendInstruction)
               for item in first.instructions)
    assert first.to_bytes().startswith(b'\x00asm\x01\x00\x00\x00')
    assert 'PeaLang WASM backend 3.1.42' in first.wat
    assert '(export "pea_run" (func $pea_run))' in first.wat


def test_wasm_artifact_roundtrip_and_validation(tmp_path):
    module = compile_source_to_bytecode(INT_LOOP)
    artifact = pealang.compile_wasm_backend(module)
    binary = tmp_path / 'app.wasm'
    wat = tmp_path / 'app.wat'
    artifact.save(binary)
    artifact.save_wat(wat)
    assert wat.read_text(encoding='utf-8') == artifact.wat
    inspected = pealang.inspect_wasm_backend(binary)
    manifest = inspected['manifest']
    assert manifest['format'] == 'PEAWASMBACKEND'
    assert manifest['abi'] == pealang.WASM_BACKEND_FORMAT
    assert manifest['version'] == pealang.WASM_BACKEND_VERSION == '3.1.42'
    assert manifest['digest'] == artifact.digest
    assert inspected['ir']['instructions']
    inspected_bytes = pealang.inspect_wasm_backend(artifact.to_bytes())
    assert inspected_bytes == inspected
    with pytest.raises(pealang.WasmBackendError):
        pealang.inspect_wasm_backend(b'bad')


def test_wasm_backend_runtime_matches_vm_for_int_loop():
    module = compile_source_to_bytecode(INT_LOOP)
    output = []
    runtime = pealang.WasmBackendRuntime(output.append)
    assert runtime.run(module) is None
    assert output == [0, 1, 2]
    assert runtime.last_report['mode'] == 'wasm'
    assert runtime.last_report['supported']
    assert runtime.last_report['instructions'] > 0
    assert runtime.last_report['digest'] == pealang.compile_wasm_backend(module).digest


def test_wasm_backend_runtime_handles_float_and_string_values():
    for source, expected in ((FLOAT_LOOP, [0.0, 1.0, 2.0]),
                             (STRING_ADD, ['peawasm'])):
        output = []
        runtime = pealang.WasmBackendRuntime(output.append)
        runtime.run(compile_source_to_bytecode(source))
        assert output == expected
        assert runtime.last_report['mode'] == 'wasm'


def test_unsupported_modules_fall_back_to_vm():
    module = compile_source_to_bytecode(FUNCTION)
    assert not pealang.wasm_backend_supported(module)
    artifact = pealang.compile_wasm_backend(module)
    assert not artifact.supported
    assert artifact.instructions == ()
    assert artifact.to_bytes().startswith(b'\x00asm\x01\x00\x00\x00')
    output = []
    runtime = pealang.WasmBackendRuntime(output.append)
    runtime.run(module)
    assert output == [4]
    assert runtime.last_report['mode'] == 'vm'
    assert runtime.last_report['digest'] == artifact.digest


def test_wasm_backend_runtime_enforces_global_instruction_limit():
    module = compile_source_to_bytecode(INT_LOOP)
    with pytest.raises(pealang.VMError):
        pealang.WasmBackendRuntime(
            lambda _value: None, max_instructions=1).run(module)


def test_verify_wasm_backend_parity_passes_on_supported_and_fallback_paths():
    for source in (INT_LOOP, FLOAT_LOOP, STRING_ADD, FUNCTION):
        parity = pealang.verify_wasm_backend_parity(
            compile_source_to_bytecode(source))
        assert parity['ok'], (source, parity)
        assert parity['output_match'] and parity['result_match']


def test_wasm_backend_report_is_stable_and_gated():
    module = compile_source_to_bytecode(INT_LOOP)
    first = pealang.wasm_backend_report(module, verify=True)
    second = pealang.wasm_backend_report(module, verify=True)
    assert first == second
    assert first['version'] == pealang.WASM_BACKEND_VERSION == '3.1.42'
    assert first['format'] == pealang.WASM_BACKEND_FORMAT
    assert first['mode'] == 'wasm'
    assert first['wasm_backend_supported']
    assert first['module_bytes'] > 0 and first['wat_bytes'] > 0
    assert first['output'] == ['0', '1', '2']
    assert first['parity']['ok']
    benchmarked = pealang.wasm_backend_report(module, benchmark=True)
    assert benchmarked['benchmark']['iterations'] == 25
    assert benchmarked['benchmark']['vm_median_ms'] >= 0
    assert benchmarked['benchmark']['wasm_median_ms'] >= 0
    assert pealang.wasm_backend_gate(first) == {'gate': 'PASS', 'issues': []}


def test_gate_rejects_invalid_mode_compilation_and_failed_parity():
    assert pealang.wasm_backend_gate({'mode': 'unknown'})['gate'] == 'FAIL'
    broken = pealang.wasm_backend_gate({'mode': 'wasm', 'gate': 'FAIL'})
    assert 'compilation' in broken['issues']
    failed = pealang.wasm_backend_gate(
        {'mode': 'wasm', 'gate': 'PASS', 'parity': {'ok': False}})
    assert failed['gate'] == 'FAIL'
    assert 'parity' in failed['issues']


def test_cli_wasm_backend_command_passes_with_parity_and_emit(tmp_path):
    source = tmp_path / 'app.pea'
    binary = tmp_path / 'app.wasm'
    wat = tmp_path / 'app.wat'
    source.write_text(INT_LOOP + '\n', encoding='utf-8')
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'wasm-backend', str(source),
         '--verify', '--emit', str(binary), '--wat', str(wat)],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['mode'] == 'wasm'
    assert report['parity']['ok']
    assert report['version'] == '3.1.42'
    assert report['instructions'] > 0
    assert binary.read_bytes().startswith(b'\x00asm\x01\x00\x00\x00')
    assert 'PeaLang WASM backend 3.1.42' in wat.read_text(encoding='utf-8')


def test_cli_wasm_backend_fallback_and_optimize_flag(tmp_path):
    source = tmp_path / 'app.pea'
    source.write_text(FUNCTION + '\n', encoding='utf-8')
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'wasm-backend', str(source),
         '--verify', '--optimize'],
        capture_output=True, text=True, cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['mode'] == 'vm'
    assert report['parity']['ok']


def test_feature_flag_help_and_analysis_namespace_document_wasm_backend():
    assert feature_status('runtime.wasm_backend_v3').stability == Stability.STABLE
    text = pea_help('wasm-backend')
    assert 'pea wasm-backend' in text
    assert 'verify_wasm_backend_parity()' in text
    namespace = build_analysis_namespace()
    for name in ('WasmBackendRuntime', 'CompileWasmBackend',
                 'InspectWasmBackend', 'VerifyWasmBackendParity',
                 'BenchmarkWasmBackend', 'WasmBackendReport',
                 'WasmBackendNamespace'):
        assert name in namespace


def test_release_metadata_is_aligned():
    assert pealang.__version__ == SPEC_VERSION == '5.7.0'
    manifest = json.loads((Path(__file__).resolve().parent.parent
                           / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '5.7.0'
    assert manifest['previous_version'] == '5.6.0'
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
