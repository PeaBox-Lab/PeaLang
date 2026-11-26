"""Phase 75: deterministic WASM backend for portable PeaLang bytecode.

This phase lowers the fast-interpreter bytecode subset to a compact WebAssembly
IR and wraps it in a standard WebAssembly custom-section module. Unlike the
earlier PEAC carrier, the artifact carries typed operation records that a host
loader can inspect or execute directly.

The backend is conservative: modules outside the supported instruction set, or
with constants that cannot be represented in the IR, are left on the standard
virtual machine. ``verify_wasm_backend_parity()`` requires identical VM and
backend output and results before a host adopts the artifact.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import time
from dataclasses import asdict, dataclass, replace
from typing import Any, Callable

from .bytecode import BytecodeModule
from .fast_interpreter import BINARY_OPS, fast_path_supported
from .wasm import MAGIC as WASM_MAGIC, VERSION as WASM_VERSION

WASM_BACKEND_VERSION = '3.1.42'
WASM_BACKEND_FORMAT = 'pea-wasm-backend-v1'
WASM_BACKEND_MANIFEST_SECTION = 'pealang.wasm_backend.manifest'
WASM_BACKEND_IR_SECTION = 'pealang.wasm_backend.ir'
MAX_WASM_INSTRUCTIONS = 100_000

WASM_BACKEND_OPS = (
    'CONST', 'NULL', 'TRUE', 'FALSE', 'LOAD', 'STORE', 'POP', 'PRINT',
    'NEG', 'NOT', 'HALT', 'JUMP', 'JUMP_IF_FALSE', *BINARY_OPS,
)
WASM_OP_IDS = {name: index + 1 for index, name in enumerate(WASM_BACKEND_OPS)}
WASM_VALUE_OPS = frozenset({'LOAD', 'STORE', 'JUMP', 'JUMP_IF_FALSE'})


class WasmBackendError(Exception):
    """Raised when WASM backend IR cannot be lowered, read, or executed."""


@dataclass(frozen=True)
class WasmBackendInstruction:
    """One lowered instruction with a stable operation record."""

    op: str
    arg: Any
    line: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WasmBackendModule:
    """A WASM IR artifact with binary and reviewable text representations."""

    source_name: str
    format: str
    instructions: tuple[WasmBackendInstruction, ...]
    constants: tuple[dict[str, Any], ...]
    digest: str
    supported: bool
    wasm: bytes
    wat: str

    def manifest(self) -> dict[str, Any]:
        return {
            'format': 'PEAWASMBACKEND',
            'version': WASM_BACKEND_VERSION,
            'abi': WASM_BACKEND_FORMAT,
            'source_name': self.source_name,
            'digest': self.digest,
            'supported': self.supported,
            'instructions': len(self.instructions),
        }

    def ir_dict(self) -> dict[str, Any]:
        return {
            'format': self.format,
            'source_name': self.source_name,
            'instructions': [item.to_dict() for item in self.instructions],
            'constants': list(self.constants),
            'digest': self.digest,
            'supported': self.supported,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            'manifest': self.manifest(),
            'ir': self.ir_dict(),
            'wat': self.wat,
        }

    def dumps(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, default=str)

    def to_bytes(self) -> bytes:
        manifest = json.dumps(self.manifest(), sort_keys=True,
                              separators=(',', ':')).encode('utf-8')
        ir = json.dumps(self.ir_dict(), sort_keys=True,
                        separators=(',', ':')).encode('utf-8')
        return (WASM_MAGIC + WASM_VERSION
                + _custom_section(WASM_BACKEND_MANIFEST_SECTION, manifest)
                + _custom_section(WASM_BACKEND_IR_SECTION, ir))

    def save(self, path) -> None:
        from pathlib import Path

        Path(path).write_bytes(self.to_bytes())

    def save_wat(self, path) -> None:
        from pathlib import Path

        Path(path).write_text(self.wat, encoding='utf-8')


def _uleb(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 127
        value >>= 7
        if value:
            byte |= 128
        out.append(byte)
        if not value:
            return bytes(out)


def _custom_section(name: str, payload: bytes) -> bytes:
    encoded_name = name.encode('utf-8')
    body = _uleb(len(encoded_name)) + encoded_name + payload
    return b'\x00' + _uleb(len(body)) + body


def _wasm_constant(value: Any) -> dict[str, Any] | None:
    if value is None:
        return {'tag': 0, 'value': None}
    if type(value) is bool:
        return {'tag': 3, 'value': value}
    if type(value) is int:
        return {'tag': 1, 'value': value}
    if type(value) is float:
        return {'tag': 2, 'value': value}
    if isinstance(value, str):
        return {'tag': 4, 'value': value}
    return None


def _decode_constant(encoded: dict[str, Any]) -> Any:
    return encoded.get('value')


def wasm_backend_supported(module: BytecodeModule) -> bool:
    """Return whether *module* can be lowered to WASM backend IR."""

    if not fast_path_supported(module):
        return False
    return all(_wasm_constant(value) is not None for value in module.constants)


def _ir_digest(source_name: str, instructions: tuple[WasmBackendInstruction, ...],
               constants: tuple[dict[str, Any], ...]) -> str:
    payload = {
        'format': WASM_BACKEND_FORMAT,
        'source_name': source_name,
        'instructions': [item.to_dict() for item in instructions],
        'constants': list(constants),
    }
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


def _wat_source(artifact: WasmBackendModule) -> str:
    lines = [
        ';; PeaLang WASM backend ' + WASM_BACKEND_VERSION,
        ';; digest: ' + artifact.digest,
        '(module',
        '  (func $pea_run',
    ]
    for index, instruction in enumerate(artifact.instructions):
        operand = json.dumps(instruction.arg, sort_keys=True, default=str)
        lines.append(
            f'    ;; {index:04d} {instruction.op} {operand} (line {instruction.line})')
    lines.extend(['  )', '  (export "pea_run" (func $pea_run))', ')', ''])
    return '\n'.join(lines)


def compile_wasm_backend(module: BytecodeModule) -> WasmBackendModule:
    """Lower *module* to WASM backend IR, or return an unsupported artifact."""

    if not wasm_backend_supported(module):
        digest = _ir_digest(module.source_name, (), ())
        unsupported = WasmBackendModule(
            source_name=module.source_name, format=WASM_BACKEND_FORMAT,
            instructions=(), constants=(), digest=digest, supported=False,
            wasm=b'', wat='',
        )
        return replace(unsupported, wasm=unsupported.to_bytes(),
                       wat=_wat_source(unsupported))
    instructions: list[WasmBackendInstruction] = []
    constants: list[dict[str, Any]] = []
    for value in module.constants:
        encoded = _wasm_constant(value)
        assert encoded is not None
        constants.append(encoded)
    for instruction in module.code.instructions:
        if instruction.op == 'CONST':
            arg: Any = _wasm_constant(module.constants[instruction.arg])
        elif instruction.op in WASM_VALUE_OPS:
            arg = instruction.arg
        else:
            arg = None
        instructions.append(WasmBackendInstruction(
            instruction.op, arg, instruction.line))
    ir = tuple(instructions)
    encoded_constants = tuple(constants)
    artifact = WasmBackendModule(
        source_name=module.source_name, format=WASM_BACKEND_FORMAT,
        instructions=ir, constants=encoded_constants,
        digest=_ir_digest(module.source_name, ir, encoded_constants),
        supported=True, wasm=b'', wat='',
    )
    return replace(artifact, wasm=artifact.to_bytes(), wat=_wat_source(artifact))


def inspect_wasm_backend(value: str | Path | bytes | bytearray) -> dict[str, Any]:
    """Read a WASM backend artifact and return its manifest and IR."""

    from pathlib import Path

    data = (Path(value).read_bytes() if isinstance(value, (str, Path))
            else bytes(value))
    if not data.startswith(WASM_MAGIC + WASM_VERSION):
        raise WasmBackendError('Not a WebAssembly v1 module')
    position = 8
    sections: dict[str, bytes] = {}

    def read_uleb() -> int:
        nonlocal position
        out = shift = 0
        while True:
            if position >= len(data):
                raise WasmBackendError('Truncated WebAssembly LEB128 value')
            byte = data[position]
            position += 1
            out |= (byte & 127) << shift
            if not byte & 128:
                return out
            shift += 7

    while position < len(data):
        kind = data[position]
        position += 1
        size = read_uleb()
        end = position + size
        if end > len(data):
            raise WasmBackendError('Truncated WebAssembly section')
        if kind == 0:
            name_size = read_uleb()
            name_end = position + name_size
            if name_end > len(data):
                raise WasmBackendError('Truncated custom section name')
            name = data[position:name_end].decode('utf-8')
            position = name_end
            sections[name] = data[position:end]
        position = end
    try:
        manifest = json.loads(sections[WASM_BACKEND_MANIFEST_SECTION])
        ir = json.loads(sections[WASM_BACKEND_IR_SECTION])
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WasmBackendError('Not a PeaLang WASM backend artifact') from exc
    return {'manifest': manifest, 'ir': ir}


class _WasmBackendFrame:
    """Mutable execution state for one WASM backend run."""

    __slots__ = ('stack', 'env', 'ip', 'steps', 'halted')

    def __init__(self, env: dict[str, Any]):
        self.stack: list[Any] = []
        self.env = env
        self.ip = 0
        self.steps = 0
        self.halted = False


def _backend_binary(operation: str, left: Any, right: Any) -> Any:
    from .vm import VMError

    if operation == 'ADD' and isinstance(left, str) and isinstance(right, str):
        return left + right
    try:
        return BINARY_OPS[operation](left, right)
    except Exception as exc:
        raise VMError(str(exc)) from exc


def _execute_wasm_backend(artifact: WasmBackendModule, frame: _WasmBackendFrame,
                          max_instructions: int,
                          emit: Callable[[Any], Any]) -> None:
    from .vm import VMError

    count = len(artifact.instructions)
    while not frame.halted and frame.ip < count:
        if frame.steps >= max_instructions:
            raise VMError('VM instruction limit exceeded')
        frame.steps += 1
        instruction = artifact.instructions[frame.ip]
        op = instruction.op
        if op == 'CONST':
            frame.stack.append(_decode_constant(instruction.arg))
        elif op == 'NULL':
            frame.stack.append(None)
        elif op == 'TRUE':
            frame.stack.append(True)
        elif op == 'FALSE':
            frame.stack.append(False)
        elif op == 'LOAD':
            if instruction.arg not in frame.env:
                raise VMError(
                    f"Undefined variable '{instruction.arg}' at line {instruction.line}")
            frame.stack.append(frame.env[instruction.arg])
        elif op == 'STORE':
            frame.env[instruction.arg] = frame.stack.pop()
        elif op == 'POP':
            frame.stack.pop()
        elif op == 'PRINT':
            emit(frame.stack.pop())
        elif op in BINARY_OPS:
            right = frame.stack.pop()
            left = frame.stack.pop()
            frame.stack.append(_backend_binary(op, left, right))
        elif op == 'NEG':
            frame.stack.append(-frame.stack.pop())
        elif op == 'NOT':
            frame.stack.append(not bool(frame.stack.pop()))
        elif op == 'JUMP':
            frame.ip = instruction.arg
            continue
        elif op == 'JUMP_IF_FALSE':
            if not bool(frame.stack.pop()):
                frame.ip = instruction.arg
                continue
        elif op == 'HALT':
            frame.halted = True
        else:
            raise WasmBackendError(f'unsupported WASM backend op: {op}')
        frame.ip += 1


class WasmBackendRuntime:
    """Execute WASM backend IR, falling back to the VM when lowering is unsafe."""

    def __init__(self, output=None,
                 max_instructions: int = MAX_WASM_INSTRUCTIONS):
        self.output = output or print
        self.max_instructions = max_instructions
        self.last_artifact: WasmBackendModule | None = None
        self.last_report: dict[str, Any] = {}

    def run(self, module: BytecodeModule,
            globals: dict[str, Any] | None = None) -> Any:
        from .vm import VirtualMachine

        artifact = compile_wasm_backend(module)
        self.last_artifact = artifact
        if not artifact.supported:
            result = VirtualMachine(
                self.output, max_instructions=self.max_instructions).run(
                    module, globals)
            mode = 'vm'
        else:
            frame = _WasmBackendFrame(dict(globals or {}))
            _execute_wasm_backend(
                artifact, frame, self.max_instructions, self.output)
            result = None
            mode = 'wasm'
        self.last_report = {
            'mode': mode,
            'supported': artifact.supported,
            'instructions': len(artifact.instructions),
            'digest': artifact.digest,
            'source_name': module.source_name,
        }
        return result


def _standard_run(module: BytecodeModule) -> dict[str, Any]:
    from .vm import VirtualMachine

    output: list[Any] = []
    machine = VirtualMachine(output.append, max_instructions=MAX_WASM_INSTRUCTIONS)
    result = machine.run(module)
    return {'output': output, 'result': result, 'instructions': machine.instructions}


def verify_wasm_backend_parity(module: BytecodeModule, **kwargs: Any) -> dict[str, Any]:
    """Require identical VM and WASM backend output and results."""

    baseline = _standard_run(module)
    output: list[Any] = []
    runtime = WasmBackendRuntime(output.append, **kwargs)
    result = runtime.run(module)
    candidate = {'output': output, 'result': result, 'report': runtime.last_report}
    ok = baseline['output'] == candidate['output'] and baseline['result'] == candidate['result']
    return {
        'ok': ok,
        'baseline': baseline,
        'wasm': candidate,
        'output_match': baseline['output'] == candidate['output'],
        'result_match': baseline['result'] == candidate['result'],
    }


def benchmark_wasm_backend(module: BytecodeModule,
                           iterations: int = 25) -> dict[str, Any]:
    """Compare median wall-clock time of the VM and WASM backend runtime."""

    def sample(run: Callable[[], Any]) -> list[float]:
        times: list[float] = []
        for _ in range(max(1, iterations)):
            start = time.perf_counter()
            try:
                run()
            except Exception:
                pass
            times.append(time.perf_counter() - start)
        return times

    baseline = sample(lambda: _standard_run(module))
    wasm = sample(lambda: WasmBackendRuntime(lambda _value: None).run(module))
    base_time = statistics.median(baseline)
    wasm_time = statistics.median(wasm)
    return {
        'iterations': iterations,
        'vm_median_ms': round(base_time * 1000, 4),
        'wasm_median_ms': round(wasm_time * 1000, 4),
        'speedup': round(base_time / wasm_time, 3) if wasm_time else None,
    }


def wasm_backend_report(module: BytecodeModule, *, verify: bool = False,
                        benchmark: bool = False) -> dict[str, Any]:
    """Return a deterministic report covering WASM lowering and safety."""

    artifact = compile_wasm_backend(module)
    output: list[Any] = []
    runtime = WasmBackendRuntime(output.append)
    result = runtime.run(module)
    report: dict[str, Any] = {
        'version': WASM_BACKEND_VERSION,
        'module_digest': hashlib.sha256(
            module.dumps().encode('utf-8')).hexdigest(),
        'format': WASM_BACKEND_FORMAT,
        'mode': runtime.last_report['mode'],
        'wasm_backend_supported': artifact.supported,
        'artifact_digest': artifact.digest,
        'instructions': len(artifact.instructions),
        'module_bytes': len(artifact.to_bytes()),
        'wat_bytes': len(artifact.wat.encode('utf-8')),
        'output': [str(value) for value in output],
        'result': str(result),
        'gate': 'PASS',
    }
    if verify:
        report['parity'] = verify_wasm_backend_parity(module)
    if benchmark:
        report['benchmark'] = benchmark_wasm_backend(module)
    return report


def wasm_backend_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Reduce a WASM backend report to a deterministic PASS/FAIL gate."""

    issues: list[str] = []
    if report.get('mode') not in ('wasm', 'vm'):
        issues.append('mode')
    if report.get('gate') != 'PASS':
        issues.append('compilation')
    parity = report.get('parity')
    if parity is not None and not parity.get('ok'):
        issues.append('parity')
    return {'gate': 'PASS' if not issues else 'FAIL', 'issues': issues}


def build_wasm_backend_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'WASM_BACKEND_VERSION': WASM_BACKEND_VERSION,
        'WASM_BACKEND_FORMAT': WASM_BACKEND_FORMAT,
        'WasmBackendError': WasmBackendError,
        'WasmBackendInstruction': WasmBackendInstruction,
        'WasmBackendModule': WasmBackendModule,
        'wasm_backend_supported': wasm_backend_supported,
        'compile_wasm_backend': compile_wasm_backend,
        'inspect_wasm_backend': inspect_wasm_backend,
        'WasmBackendRuntime': WasmBackendRuntime,
        'verify_wasm_backend_parity': verify_wasm_backend_parity,
        'benchmark_wasm_backend': benchmark_wasm_backend,
        'wasm_backend_report': wasm_backend_report,
        'wasm_backend_gate': wasm_backend_gate,
        'build_wasm_backend_namespace': build_wasm_backend_namespace,
    }


__all__ = [
    'WASM_BACKEND_VERSION', 'WASM_BACKEND_FORMAT',
    'WASM_BACKEND_MANIFEST_SECTION', 'WASM_BACKEND_IR_SECTION',
    'WasmBackendError', 'WasmBackendInstruction', 'WasmBackendModule',
    'wasm_backend_supported', 'compile_wasm_backend', 'inspect_wasm_backend',
    'WasmBackendRuntime', 'verify_wasm_backend_parity',
    'benchmark_wasm_backend', 'wasm_backend_report', 'wasm_backend_gate',
    'build_wasm_backend_namespace',
]
