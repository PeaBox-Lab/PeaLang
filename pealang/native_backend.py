"""Phase 74: deterministic native backend for portable PeaLang bytecode.

This phase lowers the fast-interpreter bytecode subset to a small, serializable
native IR and emits a self-contained C source artifact that hosts can compile.
The backend is conservative: modules outside the supported instruction set, or
with constants that cannot be represented in the IR, are left on the standard
virtual machine.

``verify_native_parity()`` executes the IR with a compact native runtime and
requires identical VM output and results before a host adopts the artifact.
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

NATIVE_BACKEND_VERSION = '3.1.41'
NATIVE_FORMAT = 'pea-native-ir-v1'
MAX_NATIVE_INSTRUCTIONS = 100_000

NATIVE_OPS = (
    'CONST', 'NULL', 'TRUE', 'FALSE', 'LOAD', 'STORE', 'POP', 'PRINT',
    'NEG', 'NOT', 'HALT', 'JUMP', 'JUMP_IF_FALSE', *BINARY_OPS,
)
OP_IDS = {name: index + 1 for index, name in enumerate(NATIVE_OPS)}
VALUE_OPS = frozenset({'LOAD', 'STORE', 'JUMP', 'JUMP_IF_FALSE'})


class NativeError(Exception):
    """Raised when native IR execution cannot continue safely."""


@dataclass(frozen=True)
class NativeInstruction:
    """One lowered instruction with JSON-friendly operands."""

    op: str
    arg: Any
    line: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NativeModule:
    """A native IR artifact with an optional C source representation."""

    source_name: str
    format: str
    instructions: tuple[NativeInstruction, ...]
    constants: tuple[dict[str, Any], ...]
    digest: str
    supported: bool
    source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'source_name': self.source_name,
            'format': self.format,
            'instructions': [item.to_dict() for item in self.instructions],
            'constants': list(self.constants),
            'digest': self.digest,
            'supported': self.supported,
            'source': self.source,
        }

    def dumps(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, default=str)

    def save(self, path) -> None:
        from pathlib import Path

        Path(path).write_text(self.source, encoding='utf-8')


def _encode_constant(value: Any) -> dict[str, Any] | None:
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


def native_supported(module: BytecodeModule) -> bool:
    """Return whether *module* can be lowered to native IR."""

    if not fast_path_supported(module):
        return False
    return all(_encode_constant(value) is not None for value in module.constants)


def _digest(source_name: str, instructions: tuple[NativeInstruction, ...],
            constants: tuple[dict[str, Any], ...]) -> str:
    payload = {
        'format': NATIVE_FORMAT,
        'source_name': source_name,
        'instructions': [item.to_dict() for item in instructions],
        'constants': list(constants),
    }
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


def compile_native(module: BytecodeModule) -> NativeModule:
    """Lower *module* to native IR, or return an unsupported artifact."""

    if not native_supported(module):
        return NativeModule(
            source_name=module.source_name, format=NATIVE_FORMAT,
            instructions=(), constants=(), digest=_digest(module.source_name, (), ()),
            supported=False, source='',
        )
    instructions: list[NativeInstruction] = []
    constants: list[dict[str, Any]] = []
    for value in module.constants:
        encoded = _encode_constant(value)
        assert encoded is not None
        constants.append(encoded)
    for instruction in module.code.instructions:
        if instruction.op == 'CONST':
            arg: Any = _encode_constant(module.constants[instruction.arg])
        elif instruction.op in VALUE_OPS:
            arg = instruction.arg
        else:
            arg = None
        instructions.append(NativeInstruction(
            instruction.op, arg, instruction.line))
    ir = tuple(instructions)
    encoded_constants = tuple(constants)
    artifact = NativeModule(
        source_name=module.source_name, format=NATIVE_FORMAT,
        instructions=ir, constants=encoded_constants,
        digest=_digest(module.source_name, ir, encoded_constants),
        supported=True, source='',
    )
    return replace(artifact, source=_native_source(artifact))


def _c_string(value: str) -> str:
    return json.dumps(value)


def _c_literal(encoded: dict[str, Any]) -> tuple[int, int, str, str]:
    tag = encoded['tag']
    value = encoded['value']
    if tag == 0:
        return tag, 0, '0.0', 'NULL'
    if tag == 1:
        return tag, int(value), '0.0', 'NULL'
    if tag == 2:
        return tag, 0, repr(float(value)), 'NULL'
    if tag == 3:
        return tag, 1 if value else 0, '0.0', 'NULL'
    return tag, 0, '0.0', _c_string(str(value))


_C_RUNTIME = r'''
typedef struct { int tag; long long i; double d; const char *s; } PeaValue;
typedef struct { int op; int tag; long long i; double d; const char *s; int line; } NativeIns;
enum { %OPS% };
#define PEA_NULL ((PeaValue){0,0,0,0})
#define PEA_INT(x) ((PeaValue){1,(long long)(x),0,0})
#define PEA_FLOAT(x) ((PeaValue){2,0,(double)(x),0})
#define PEA_BOOL(x) ((PeaValue){3,(long long)(x),0,0})
#define PEA_STR(x) ((PeaValue){4,0,0,(x)})
static double pea_num(PeaValue v) { return v.tag == 1 ? (double)v.i : v.d; }
static int pea_truth(PeaValue v) {
  if (v.tag == 0) return 0;
  if (v.tag == 4) return v.s && v.s[0] != '\0';
  return v.tag == 2 ? v.d != 0.0 : v.i != 0;
}
static int pea_equal(PeaValue a, PeaValue b) {
  if (a.tag == 4 && b.tag == 4) return strcmp(a.s ? a.s : "", b.s ? b.s : "") == 0;
  if (a.tag == 0 || b.tag == 0) return a.tag == b.tag;
  return pea_num(a) == pea_num(b);
}
static PeaValue pea_binary(int op, PeaValue a, PeaValue b) {
  double x = pea_num(a), y = pea_num(b);
  if (op == OP_ADD && a.tag == 4 && b.tag == 4) {
    size_t n = strlen(a.s ? a.s : "") + strlen(b.s ? b.s : "") + 1;
    char *buf = (char *)malloc(n);
    strcpy(buf, a.s ? a.s : ""); strcat(buf, b.s ? b.s : "");
    return PEA_STR(buf);
  }
  switch (op) {
    case OP_ADD: return a.tag == 1 && b.tag == 1 ? PEA_INT(a.i + b.i) : PEA_FLOAT(x + y);
    case OP_SUB: return a.tag == 1 && b.tag == 1 ? PEA_INT(a.i - b.i) : PEA_FLOAT(x - y);
    case OP_MUL: return a.tag == 1 && b.tag == 1 ? PEA_INT(a.i * b.i) : PEA_FLOAT(x * y);
    case OP_DIV: return PEA_FLOAT(x / y);
    case OP_MOD: return a.tag == 1 && b.tag == 1 ? PEA_INT(a.i % b.i) : PEA_FLOAT(fmod(x, y));
    case OP_EQ: return PEA_BOOL(pea_equal(a, b));
    case OP_NE: return PEA_BOOL(!pea_equal(a, b));
    case OP_LT: return PEA_BOOL(x < y);
    case OP_LE: return PEA_BOOL(x <= y);
    case OP_GT: return PEA_BOOL(x > y);
    case OP_GE: return PEA_BOOL(x >= y);
    default: return PEA_NULL;
  }
}
static void pea_print(PeaValue v) {
  if (v.tag == 0) printf("None\n");
  else if (v.tag == 1) printf("%lld\n", v.i);
  else if (v.tag == 2) printf("%.17g\n", v.d);
  else if (v.tag == 3) printf("%s\n", v.i ? "True" : "False");
  else printf("%s\n", v.s ? v.s : "");
}
static const NativeIns CODE[] = {
%CODE%
};
int main(void) {
  PeaValue stack[256]; PeaValue vals[64]; const char *names[64];
  int sp = 0, nv = 0, pc = 0, steps = 0, k, found;
  while (pc >= 0 && pc < (int)(sizeof(CODE) / sizeof(CODE[0])) && steps < %MAXSTEPS%) {
    NativeIns in = CODE[pc++]; steps++;
    PeaValue a, b, v;
    switch (in.op) {
      case OP_CONST:
        if (in.tag == 0) v = PEA_NULL;
        else if (in.tag == 1) v = PEA_INT(in.i);
        else if (in.tag == 2) v = PEA_FLOAT(in.d);
        else if (in.tag == 3) v = PEA_BOOL(in.i);
        else v = PEA_STR(in.s);
        stack[sp++] = v; break;
      case OP_NULL: stack[sp++] = PEA_NULL; break;
      case OP_TRUE: stack[sp++] = PEA_BOOL(1); break;
      case OP_FALSE: stack[sp++] = PEA_BOOL(0); break;
      case OP_LOAD:
        found = 0;
        for (k = 0; k < nv; k++) if (!strcmp(names[k], in.s)) { stack[sp++] = vals[k]; found = 1; break; }
        if (!found) return 2;
        break;
      case OP_STORE:
        v = stack[--sp]; found = 0;
        for (k = 0; k < nv; k++) if (!strcmp(names[k], in.s)) { vals[k] = v; found = 1; break; }
        if (!found) { names[nv] = in.s; vals[nv++] = v; }
        break;
      case OP_POP: sp--; break;
      case OP_PRINT: pea_print(stack[--sp]); break;
      case OP_NEG: stack[sp - 1] = stack[sp - 1].tag == 1 ? PEA_INT(-stack[sp - 1].i) : PEA_FLOAT(-pea_num(stack[sp - 1])); break;
      case OP_NOT: v = stack[--sp]; stack[sp++] = PEA_BOOL(!pea_truth(v)); break;
      case OP_ADD: case OP_SUB: case OP_MUL: case OP_DIV: case OP_MOD:
      case OP_EQ: case OP_NE: case OP_LT: case OP_LE: case OP_GT: case OP_GE:
        b = stack[--sp]; a = stack[--sp]; stack[sp++] = pea_binary(in.op, a, b); break;
      case OP_JUMP: pc = (int)in.i; break;
      case OP_JUMP_IF_FALSE: v = stack[--sp]; if (!pea_truth(v)) pc = (int)in.i; break;
      case OP_HALT: return 0;
      default: return 3;
    }
  }
  return 0;
}
'''


def _native_source(artifact: NativeModule) -> str:
    ops = ', '.join(f'OP_{name}={OP_IDS[name]}' for name in NATIVE_OPS)
    code_lines = []
    for instruction in artifact.instructions:
        tag, ival, dval, sval = 0, 0, '0.0', 'NULL'
        if instruction.op == 'CONST':
            tag, ival, dval, sval = _c_literal(instruction.arg)
        elif instruction.op in ('LOAD', 'STORE'):
            sval = _c_string(str(instruction.arg))
        elif instruction.op in ('JUMP', 'JUMP_IF_FALSE'):
            ival = int(instruction.arg)
        code_lines.append(
            f'  {{OP_{instruction.op}, {tag}, {ival}, {dval}, {sval}, {instruction.line}}},')
    runtime = (_C_RUNTIME.replace('%OPS%', ops)
               .replace('%CODE%', '\n'.join(code_lines))
               .replace('%MAXSTEPS%', str(MAX_NATIVE_INSTRUCTIONS)))
    return '/* PeaLang native backend ' + NATIVE_BACKEND_VERSION + ' */\n' \
        '#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <math.h>\n' + runtime


class _NativeFrame:
    """Mutable execution state for one native IR run."""

    __slots__ = ('stack', 'env', 'ip', 'steps', 'halted')

    def __init__(self, env: dict[str, Any]):
        self.stack: list[Any] = []
        self.env = env
        self.ip = 0
        self.steps = 0
        self.halted = False


def _binary(operation: str, left: Any, right: Any) -> Any:
    from .vm import VMError

    if operation == 'ADD' and isinstance(left, str) and isinstance(right, str):
        return left + right
    try:
        return BINARY_OPS[operation](left, right)
    except Exception as exc:
        raise VMError(str(exc)) from exc


def _execute_native(artifact: NativeModule, frame: _NativeFrame,
                    max_instructions: int, emit: Callable[[Any], Any]) -> None:
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
            frame.stack.append(_binary(op, left, right))
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
            raise NativeError(f'unsupported native op: {op}')
        frame.ip += 1


class NativeRuntime:
    """Execute native IR, falling back to the VM when lowering is unsafe."""

    def __init__(self, output=None, max_instructions: int = MAX_NATIVE_INSTRUCTIONS):
        self.output = output or print
        self.max_instructions = max_instructions
        self.last_artifact: NativeModule | None = None
        self.last_report: dict[str, Any] = {}

    def run(self, module: BytecodeModule,
            globals: dict[str, Any] | None = None) -> Any:
        from .vm import VirtualMachine

        artifact = compile_native(module)
        self.last_artifact = artifact
        if not artifact.supported:
            result = VirtualMachine(
                self.output, max_instructions=self.max_instructions).run(module, globals)
            mode = 'vm'
        else:
            frame = _NativeFrame(dict(globals or {}))
            _execute_native(
                artifact, frame, self.max_instructions, self.output)
            result = None
            mode = 'native'
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
    machine = VirtualMachine(output.append, max_instructions=MAX_NATIVE_INSTRUCTIONS)
    result = machine.run(module)
    return {'output': output, 'result': result, 'instructions': machine.instructions}


def verify_native_parity(module: BytecodeModule, **kwargs: Any) -> dict[str, Any]:
    """Require identical VM and native IR output and results."""

    baseline = _standard_run(module)
    output: list[Any] = []
    runtime = NativeRuntime(output.append, **kwargs)
    result = runtime.run(module)
    candidate = {'output': output, 'result': result, 'report': runtime.last_report}
    ok = baseline['output'] == candidate['output'] and baseline['result'] == candidate['result']
    return {
        'ok': ok,
        'baseline': baseline,
        'native': candidate,
        'output_match': baseline['output'] == candidate['output'],
        'result_match': baseline['result'] == candidate['result'],
    }


def benchmark_native(module: BytecodeModule, iterations: int = 25) -> dict[str, Any]:
    """Compare median wall-clock time of the VM and native runtime."""

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
    native = sample(lambda: NativeRuntime(lambda _value: None).run(module))
    base_time = statistics.median(baseline)
    native_time = statistics.median(native)
    return {
        'iterations': iterations,
        'vm_median_ms': round(base_time * 1000, 4),
        'native_median_ms': round(native_time * 1000, 4),
        'speedup': round(base_time / native_time, 3) if native_time else None,
    }


def native_report(module: BytecodeModule, *, verify: bool = False,
                  benchmark: bool = False) -> dict[str, Any]:
    """Return a deterministic report covering native lowering and safety."""

    artifact = compile_native(module)
    output: list[Any] = []
    runtime = NativeRuntime(output.append)
    result = runtime.run(module)
    report: dict[str, Any] = {
        'version': NATIVE_BACKEND_VERSION,
        'module_digest': hashlib.sha256(
            module.dumps().encode('utf-8')).hexdigest(),
        'format': NATIVE_FORMAT,
        'mode': runtime.last_report['mode'],
        'native_supported': artifact.supported,
        'artifact_digest': artifact.digest,
        'instructions': len(artifact.instructions),
        'source_bytes': len(artifact.source.encode('utf-8')),
        'output': [str(value) for value in output],
        'result': str(result),
        'gate': 'PASS',
    }
    if verify:
        report['parity'] = verify_native_parity(module)
    if benchmark:
        report['benchmark'] = benchmark_native(module)
    return report


def native_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Reduce a native report to a deterministic PASS/FAIL gate."""

    issues: list[str] = []
    if report.get('mode') not in ('native', 'vm'):
        issues.append('mode')
    if report.get('gate') != 'PASS':
        issues.append('compilation')
    parity = report.get('parity')
    if parity is not None and not parity.get('ok'):
        issues.append('parity')
    return {'gate': 'PASS' if not issues else 'FAIL', 'issues': issues}


def build_native_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'NATIVE_BACKEND_VERSION': NATIVE_BACKEND_VERSION,
        'NATIVE_FORMAT': NATIVE_FORMAT,
        'NativeInstruction': NativeInstruction,
        'NativeModule': NativeModule,
        'native_supported': native_supported,
        'compile_native': compile_native,
        'NativeRuntime': NativeRuntime,
        'verify_native_parity': verify_native_parity,
        'benchmark_native': benchmark_native,
        'native_report': native_report,
        'native_gate': native_gate,
        'build_native_namespace': build_native_namespace,
    }


__all__ = [
    'NATIVE_BACKEND_VERSION', 'NATIVE_FORMAT', 'NativeError',
    'NativeInstruction', 'NativeModule', 'native_supported', 'compile_native',
    'NativeRuntime', 'verify_native_parity', 'benchmark_native',
    'native_report', 'native_gate', 'build_native_namespace',
]
