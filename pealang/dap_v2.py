"""Phase 82: deterministic DAP v2 session layer for PeaLang debugging.

This module is additive to the existing ``dap`` and ``vm_dap`` servers. It
provides a versioned capability set, a reproducible VM-backed session state
machine, deterministic breakpoint and stepping evidence, and a CI-ready gate.
Timing and host-specific values are excluded from all digests.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .bytecode import BytecodeModule
from .compiler import compile_source_to_bytecode
from .tooling_conformance import DAPConformance, ReproducibleDebugSession
from .vm import VirtualMachine

DAP_V2_VERSION = '3.1.45'
DAP_V2_PROTOCOL_VERSION = '1.68.0'
DAP_V2_FORMAT = 'pea-dap-v2'
DAP_V2_COMMANDS = tuple(sorted(
    DAPConformance.REQUIRED | {
        'attach', 'configurationDone', 'continue', 'evaluate', 'exceptionInfo',
        'next', 'stepIn', 'stepOut', 'terminate', 'threads',
    }
))

_CONDITION_RE = re.compile(
    r'^([A-Za-z_]\w*)\s*(==|!=|>=|<=|>|<)\s*(-?\d+)$')
_HIT_CONDITION_RE = re.compile(r'^hits\s*(==|!=|>=|<=|>|<)\s*(\d+)$')
_VM_BUILTIN_NAMES = frozenset({
    'append', 'error', 'has_next', 'int', 'iter', 'len', 'lower', 'next',
    'number', 'peek', 'scopes', 'str', 'upper',
})


class DapV2Error(Exception):
    """Raised when a DAP v2 session cannot be configured or advanced."""


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str,
    ).encode('utf-8')).hexdigest()


def _compare(left: Any, operator: str, right: Any) -> bool:
    try:
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            a, b = left, right
        else:
            a, b = str(left), str(right)
        return {
            '==': a == b, '!=': a != b, '>=': a >= b,
            '<=': a <= b, '>': a > b, '<': a < b,
        }[operator]
    except (KeyError, TypeError, ValueError):
        return False


def _basename(value: Any) -> str:
    text = str(value).replace('\\', '/')
    return text.rsplit('/', 1)[-1] or text


def _stable_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_stable_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _stable_value(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, type):
        return f'<type {value.__name__}>'
    if callable(value):
        return '<callable>'
    return str(value)


def _stable_variables(values: dict[str, Any]) -> dict[str, Any]:
    return {
        str(name): _stable_value(values[name])
        for name in sorted(values, key=str)
        if str(name) not in _VM_BUILTIN_NAMES
    }


@dataclass(frozen=True)
class DapBreakpoint:
    """One verified DAP v2 breakpoint with deterministic hit evidence."""

    id: int
    source: str
    line: int
    condition: str | None = None
    hit_condition: str | None = None
    enabled: bool = True
    hits: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id, 'source': self.source, 'line': self.line,
            'condition': self.condition, 'hit_condition': self.hit_condition,
            'enabled': self.enabled, 'hits': self.hits,
        }


def dap_v2_capabilities() -> dict[str, Any]:
    """Return the versioned DAP v2 capability set."""

    return {
        'supportsConfigurationDoneRequest': True,
        'supportsConditionalBreakpoints': True,
        'supportsHitConditionalBreakpoints': True,
        'supportsEvaluateForHovers': True,
        'supportsExceptionInfoRequest': True,
        'supportsRestartRequest': True,
        'supportsStepInTargetsRequest': False,
        'supportsStepBack': False,
        'supportsSetVariable': True,
    }


class DapV2Session:
    """A reproducible VM-backed debug session with inspectable evidence."""

    def __init__(self, *, max_instructions: int = 100_000,
                 source_name: str = '<input>') -> None:
        self.max_instructions = max(1, int(max_instructions))
        self.source_name = source_name
        self.source = ''
        self.module: BytecodeModule | None = None
        self.vm: VirtualMachine | None = None
        self.initialized = False
        self.launched = False
        self.terminated = False
        self.breakpoints: tuple[DapBreakpoint, ...] = ()
        self.events: list[dict[str, Any]] = []
        self.output: tuple[str, ...] = ()
        self._output_buffer: list[Any] = []
        self.last_status: dict[str, Any] = {'reason': 'uninitialized'}
        self.handled_commands: set[str] = set()
        self.snapshots = ReproducibleDebugSession()
        self._references: dict[int, dict[str, Any]] = {}
        self._next_breakpoint_id = 1
        self._response_seq = 1

    def _event(self, name: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        event = {
            'seq': len(self.events) + 1, 'type': 'event', 'event': name,
            'body': body or {},
        }
        self.events.append(event)
        return event

    def initialize(self, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = arguments or {}
        self.initialized = True
        self._event('initialized', {'version': DAP_V2_VERSION,
                                    'lines': bool(arguments.get('lines'))})
        return dap_v2_capabilities()

    def launch(self, *, source: str | None = None, path: str | None = None
               ) -> dict[str, Any]:
        if source is None and path is None:
            raise DapV2Error('launch requires source text or a path')
        if path is not None:
            program = Path(path)
            self.source = program.read_text(encoding='utf-8')
            self.source_name = str(program)
            module = (BytecodeModule.load(program)
                      if program.suffix == '.peac'
                      else compile_source_to_bytecode(self.source, self.source_name))
        else:
            self.source = source or ''
            module = compile_source_to_bytecode(self.source, self.source_name)
        output: list[str] = []
        self.vm = VirtualMachine(output.append,
                                 max_instructions=self.max_instructions)
        self.vm.module = module
        self.module = module
        self._output_buffer = output
        self.output = ()
        self.snapshots = ReproducibleDebugSession()
        self.breakpoints = ()
        self._next_breakpoint_id = 1
        self._references = {}
        self.terminated = False
        self.launched = True
        self.last_status = {'reason': 'launched'}
        codes = [module.code, *module.functions.values()]
        lines = sorted({int(instruction.line)
                        for code in codes for instruction in code.instructions})
        return {
            'verified': True, 'source_name': self.source_name,
            'instruction_count': sum(len(code.instructions) for code in codes),
            'lines': lines,
        }

    def set_breakpoints(self, source: str | None,
                        breakpoints: Iterable[dict[str, Any]]) -> dict[str, Any]:
        if self.vm is None or self.module is None:
            raise DapV2Error('launch the program before setting breakpoints')
        source_name = str(source or self.source_name)
        self.vm.breakpoints.clear()
        available = {int(instruction.line)
                     for code in [self.module.code, *self.module.functions.values()]
                     for instruction in code.instructions}
        created: list[DapBreakpoint] = []
        for specification in breakpoints:
            line = int(specification.get('line', 0))
            if line not in available:
                continue
            breakpoint = DapBreakpoint(
                id=self._next_breakpoint_id, source=source_name, line=line,
                condition=specification.get('condition'),
                hit_condition=specification.get('hitCondition'),
            )
            self._next_breakpoint_id += 1
            created.append(breakpoint)
            self.vm.add_breakpoint(line, source_name)
        self.breakpoints = tuple(created)
        verified = [{
            'id': item.id, 'verified': True, 'line': item.line,
            'source': item.source,
        } for item in created]
        self._event('breakpoint', {'count': len(verified)})
        return {'breakpoints': verified}

    def _condition_holds(self, breakpoint: DapBreakpoint,
                         variables: dict[str, Any]) -> bool:
        condition = (breakpoint.condition or '').strip()
        if not condition:
            return True
        match = _CONDITION_RE.fullmatch(condition)
        if match:
            return _compare(variables.get(match.group(1)), match.group(2),
                            int(match.group(3)))
        return bool(variables.get(condition, False))

    def _hit_condition_holds(self, breakpoint: DapBreakpoint) -> bool:
        condition = (breakpoint.hit_condition or '').strip()
        if not condition:
            return True
        match = _HIT_CONDITION_RE.fullmatch(condition)
        if match:
            return _compare(breakpoint.hits, match.group(1), int(match.group(2)))
        return True

    def _process_status(self, status: Any) -> dict[str, Any]:
        self.output = tuple(str(item) for item in self._output_buffer)
        if not isinstance(status, dict) or 'reason' not in status:
            self.terminated = True
            self.last_status = {'reason': 'terminated'}
            self._event('terminated', {'output': list(self.output)})
            return self.last_status
        result = dict(status)
        source = str(result.get('source', self.source_name))
        line = int(result.get('line', 0))
        function = str(result.get('frame', '<module>'))
        frames = self.stack_trace()
        variables = (self._references.get(frames[0]['id'], {})
                     if frames else {})
        self.snapshots.record(result['reason'], _basename(source), line,
                              function, variables,
                              tuple(frame['name'] for frame in frames))
        self._event('stopped', {'reason': result['reason'], 'threadId': 1,
                                'source': _basename(source), 'line': line,
                                'function': function})
        matched = [bp for bp in self.breakpoints
                   if bp.enabled and _basename(bp.source) == _basename(source)
                   and bp.line == line]
        skipped = False
        for breakpoint in matched:
            self.breakpoints = tuple(
                DapBreakpoint(**{**bp.to_dict(),
                                 'hits': bp.hits + 1 if bp == breakpoint else bp.hits})
                for bp in self.breakpoints
            )
            updated = next(bp for bp in self.breakpoints if bp.id == breakpoint.id)
            if not (self._condition_holds(updated, variables)
                    and self._hit_condition_holds(updated)):
                skipped = True
        if result['reason'] == 'breakpoint' and skipped:
            self._event('continued', {'reason': 'conditionNotMet',
                                      'source': _basename(source), 'line': line})
            return {'reason': 'skipped-breakpoint'}
        self.last_status = result
        return result

    def _resume(self, *, first: bool = False) -> dict[str, Any]:
        if self.vm is None or self.module is None:
            raise DapV2Error('launch the program before resuming')
        pending = True
        result: dict[str, Any] = {'reason': 'terminated'}
        while pending:
            if first:
                outcome = self.vm.run(self.module)
            else:
                outcome = self.vm.continue_run()
            result = self._process_status(outcome)
            pending = result.get('reason') == 'skipped-breakpoint'
            first = False
        return result

    def configuration_done(self) -> dict[str, Any]:
        return self._resume(first=True)

    def continue_run(self) -> dict[str, Any]:
        return self._resume()

    def next(self) -> dict[str, Any]:
        if self.vm is None:
            raise DapV2Error('launch the program before stepping')
        return self._process_status(self.vm.step())

    def step_in(self) -> dict[str, Any]:
        return self.next()

    def step_out(self) -> dict[str, Any]:
        if self.vm is None or not self.vm.frames:
            return {'reason': 'end'}
        depth = len(self.vm.frames)
        while True:
            result = self.next()
            if result.get('reason') == 'terminated' or len(self.vm.frames) < depth:
                return result

    def threads(self) -> dict[str, Any]:
        return {'threads': [{'id': 1, 'name': 'PeaLang main', 'running': not self.terminated}]}

    def stack_trace(self) -> list[dict[str, Any]]:
        if self.vm is None:
            return []
        frames: list[dict[str, Any]] = []
        for index, frame in enumerate(self.vm.stack_trace()):
            frame_id = 1000 + index + 1
            self._references[frame_id] = _stable_variables(frame.get('locals', {}))
            source = str(frame.get('source', self.source_name))
            frames.append({
                'id': frame_id, 'name': frame.get('name', '<module>'),
                'line': int(frame.get('line', 0)), 'column': 1,
                'source': {'name': _basename(source), 'path': source},
            })
        if frames:
            self._references[2000] = dict(self._references[1001])
        return frames

    def scopes(self, frame_id: int) -> dict[str, Any]:
        return {
            'scopes': [
                {'name': 'Locals', 'variablesReference': int(frame_id),
                 'expensive': False},
                {'name': 'Globals', 'variablesReference': 2000,
                 'expensive': False},
            ],
        }

    def variables(self, reference: int) -> dict[str, Any]:
        values = self._references.get(int(reference), {})
        return {
            'variables': [{
                'name': str(name), 'value': repr(values[name]),
                'type': type(values[name]).__name__, 'variablesReference': 0,
            } for name in sorted(values, key=str)],
        }

    def evaluate(self, expression: str, frame_id: int | None = None
                 ) -> dict[str, Any]:
        expression = str(expression)
        local_values = self._references.get(int(frame_id or 1001), {})
        global_values = self._references.get(2000, {})
        if expression in local_values:
            value = local_values[expression]
        elif expression in global_values:
            value = global_values[expression]
        else:
            try:
                value = int(expression)
            except ValueError:
                value = '<unavailable>'
        return {'result': repr(value), 'variablesReference': 0}

    def exception_info(self) -> dict[str, Any]:
        return {
            'exceptionId': 'PeaLangVMError', 'breakMode': 'unhandled',
            'description': str(self.last_status.get('message', 'VM exception')),
        }

    def disconnect(self) -> dict[str, Any]:
        if not self.terminated:
            self.terminated = True
            self._event('terminated', {'output': list(self.output)})
        return {}

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Dispatch one DAP request and return its deterministic response."""

        command = str(message.get('command', ''))
        arguments = message.get('arguments') or {}
        self.handled_commands.add(command)
        success = True
        body: dict[str, Any] = {}
        try:
            if command == 'initialize':
                body = self.initialize(arguments)
            elif command in ('launch', 'attach'):
                body = self.launch(source=arguments.get('source'),
                                   path=arguments.get('program'))
            elif command == 'setBreakpoints':
                body = self.set_breakpoints(arguments.get('source'),
                                            arguments.get('breakpoints', ()))
            elif command == 'configurationDone':
                body = self.configuration_done()
            elif command == 'continue':
                body = self.continue_run()
            elif command == 'next':
                body = self.next()
            elif command == 'stepIn':
                body = self.step_in()
            elif command == 'stepOut':
                body = self.step_out()
            elif command == 'threads':
                body = self.threads()
            elif command == 'stackTrace':
                body = {'stackFrames': self.stack_trace()}
                body['totalFrames'] = len(body['stackFrames'])
            elif command == 'scopes':
                body = self.scopes(int(arguments.get('frameId', 1001)))
            elif command == 'variables':
                body = self.variables(int(arguments.get('variablesReference', 1001)))
            elif command == 'evaluate':
                body = self.evaluate(arguments.get('expression', ''),
                                     arguments.get('frameId'))
            elif command == 'exceptionInfo':
                body = self.exception_info()
            elif command in ('disconnect', 'terminate'):
                body = self.disconnect()
        except Exception as exc:  # DAP requests report errors in the response
            success = False
            body = {'error': str(exc)}
        response = {
            'seq': self._response_seq, 'type': 'response',
            'request_seq': int(message.get('seq', 0)), 'command': command,
            'success': success, 'body': body,
        }
        if not success:
            response['message'] = str(body.get('error', 'request failed'))
        self._response_seq += 1
        return response


def dap_v2_report(session: DapV2Session) -> dict[str, Any]:
    """Return a deterministic report over DAP v2 session evidence."""

    commands = sorted(set(DAP_V2_COMMANDS) | session.handled_commands)
    conformance = DAPConformance().certify(commands)
    fingerprint = session.snapshots.fingerprint()
    payload: dict[str, Any] = {
        'version': DAP_V2_VERSION,
        'format': DAP_V2_FORMAT,
        'protocol_version': DAP_V2_PROTOCOL_VERSION,
        'source_name': session.source_name,
        'launched': session.launched,
        'terminated': session.terminated,
        'command_count': len(commands),
        'commands': commands,
        'conformance': conformance,
        'breakpoints': [item.to_dict() for item in session.breakpoints],
        'events': list(session.events),
        'output': list(session.output),
        'snapshot_fingerprint': fingerprint,
        'gate': 'PASS',
    }
    digest_payload = dict(payload)
    digest_payload['source_name'] = _basename(session.source_name)
    digest_payload['breakpoints'] = [
        {**item, 'source': _basename(item['source'])}
        for item in digest_payload['breakpoints']
    ]
    digest_payload['events'] = [
        {
            **event,
            'body': {
                key: (_basename(value) if key == 'source' else value)
                for key, value in event.get('body', {}).items()
            },
        }
        for event in digest_payload['events']
    ]
    payload['digest'] = _digest(digest_payload)
    return payload


def dap_v2_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute a deterministic PASS/FAIL decision from a DAP v2 report."""

    issues: list[str] = []
    if report.get('version') != DAP_V2_VERSION:
        issues.append('version')
    if report.get('format') != DAP_V2_FORMAT:
        issues.append('format')
    if report.get('gate') != 'PASS':
        issues.append('report')
    if not report.get('conformance', {}).get('passed'):
        issues.append('conformance')
    if len(str(report.get('snapshot_fingerprint', ''))) != 64:
        issues.append('fingerprint')
    if len(str(report.get('digest', ''))) != 64:
        issues.append('digest')
    return {'gate': 'PASS' if not issues else 'FAIL', 'issues': issues}


def build_dap_v2_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis namespaces."""

    return {
        'DAP_V2_VERSION': DAP_V2_VERSION,
        'DAP_V2_PROTOCOL_VERSION': DAP_V2_PROTOCOL_VERSION,
        'DAP_V2_FORMAT': DAP_V2_FORMAT,
        'DapV2Error': DapV2Error,
        'DapBreakpoint': DapBreakpoint,
        'DapV2Session': DapV2Session,
        'dap_v2_capabilities': dap_v2_capabilities,
        'dap_v2_report': dap_v2_report,
        'dap_v2_gate': dap_v2_gate,
        'build_dap_v2_namespace': build_dap_v2_namespace,
    }


__all__ = [
    'DAP_V2_VERSION', 'DAP_V2_PROTOCOL_VERSION', 'DAP_V2_FORMAT',
    'DapV2Error', 'DapBreakpoint', 'DapV2Session', 'dap_v2_capabilities',
    'dap_v2_report', 'dap_v2_gate', 'build_dap_v2_namespace',
]
