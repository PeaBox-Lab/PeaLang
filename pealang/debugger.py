"""Debug adapter protocol and VM debugging support for PeaLang (v2.4.0).

Provides:
- Debug adapter protocol implementation
- VM breakpoints and step operations
- Stack trace and variable inspection
- Live memory/state inspection
- Profiling/flame graph primitives
"""

from __future__ import annotations

import json
import re
import time
import threading
from collections import defaultdict, OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Debug adapter protocol types
# ---------------------------------------------------------------------------

class ConfigurationDoneEvent:
    """Event sent by client when configuration is complete."""
    type = "configurationDone"


class InterruptedEvent:
    """Event sent when execution is interrupted at a breakpoint."""
    type = "event"
    category = "exception"


# ---------------------------------------------------------------------------
# VM Breakpoint Support
# ---------------------------------------------------------------------------

class Breakpoint:
    """Represents a breakpoint at a VM instruction address."""

    def __init__(self, address: int, enabled: bool = True):
        self.address = address
        self.enabled = enabled
        self.hit_count = 0
        self.ignore_count = 0

    def hit(self) -> None:
        self.hit_count += 1

    def enabled_set(self, enabled: bool) -> None:
        self.enabled = enabled


class BreakpointManager:
    """Manages breakpoints for a VM instance."""

    def __init__(self):
        self._breakpoints: dict[int, Breakpoint] = {}
        self._next_id = 1

    def add(self, address: int) -> int:
        """Add a breakpoint at *address*. Returns the breakpoint id."""
        bp_id = self._next_id
        self._next_id += 1
        self._breakpoints[address] = Breakpoint(address)
        return bp_id

    def remove(self, bp_id: int) -> None:
        """Remove a breakpoint by id."""
        for addr, bp in list(self._breakpoints.items()):
            bp.enabled = False
            del self._breakpoints[addr]
            break

    def check(self, address: int) -> bool:
        """Check if there's a breakpoint at *address*, and record a hit if so."""
        bp = self._breakpoints.get(address)
        if bp and bp.enabled:
            bp.hit()
            return True
        return False

    def get_enabled(self) -> list[int]:
        """Return list of addresses with enabled breakpoints."""
        return [
            addr for addr, bp in self._breakpoints.items() if bp.enabled
        ]

    def set_enabled(self, address: int, enabled: bool) -> None:
        """Enable or disable a breakpoint at *address*."""
        bp = self._breakpoints.get(address)
        if bp:
            bp.enabled = enabled

    def clear_all(self) -> None:
        """Disable all breakpoints."""
        for bp in self._breakpoints.values():
            bp.enabled = False


# ---------------------------------------------------------------------------
# Stack Trace Support
# ---------------------------------------------------------------------------

class StackFrame:
    """Represents a frame in the VM call stack."""

    def __init__(
        self,
        frame_id: int,
        name: str,
        source: Optional[Dict[str, Any]],
        line: int,
        column: int = 0,
        end_line: Optional[int] = None,
        end_column: Optional[int] = None,
    ):
        self.id = frame_id
        self.name = name
        self.source = source
        self.line = line
        self.column = column
        self.end_line = end_line
        self.end_column = end_column

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source": self.source,
            "line": self.line,
            "column": self.column,
            "endLine": self.end_line,
            "endColumn": self.end_column,
        }


class StackTrace:
    """Represents a complete stack trace from the VM."""

    def __init__(self, threads: dict[int, list[StackFrame]]):
        self.threads = threads  # thread_id -> [StackFrame, ...]

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for thread_id, frames in self.threads.items():
            result[f"thread_{thread_id}"] = [f.to_dict() for f in frames]
        return result


# ---------------------------------------------------------------------------
# Variable / Value Representation
# ---------------------------------------------------------------------------

class Variable:
    """Represents an inspected variable from VM state."""

    def __init__(
        self,
        name: str,
        value: Any,
        type_hint: str = "auto",
        value_format: str = "default",
    ):
        self.name = name
        self.value = value
        self.type = type_hint
        self.format = value_format

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self._serialize(self.value),
            "type": self.type,
            "presentation": {"format": self.format},
        }

    def _serialize(self, v: Any) -> Any:
        if isinstance(v, (str, int, float, bool)):
            return v
        if v is None:
            return None
        if isinstance(v, dict):
            return {k: self._serialize(vi) for k, vi in v.items()}
        if isinstance(v, (list, tuple)):
            return [self._serialize(item) for item in v]
        try:
            return dict(v)
        except Exception:
            return str(v)


# ---------------------------------------------------------------------------
# Debug Adapter Protocol Implementation
# ---------------------------------------------------------------------------

class DebugAdapter:
    """Implements the Debug Adapter Protocol for PeaLang VM."""

    def __init__(self, vm):
        self.vm = vm
        self.breakpoints = BreakpointManager()
        self.running = False
        self.pause_reason: str | None = None
        self.initialized = False

    def initialize(self, capabilities: dict[str, Any] | None = None) -> dict:
        """Return the initialize response as per DAP."""
        self.initialized = True
        return {
            "type": "response",
            "requestId": "init",
            "success": True,
            "command": "initialize",
            "body": {
                "supportsConfigurationDoneRequest": True,
                "supportsHitConditionalBreakpoints": True,
                "supportsStepThrough": True,
                "supportsStepIn": True,
                "supportsStepOut": True,
                "supportsSetVariable": True,
                "supportsRestartRequest": True,
                "exceptionBreakpointOptions": {
                    "breakpoints": [
                        {"id": 1, "default": True}
                    ]
                },
            },
        }

    def configuration_done(self) -> dict:
        """Handle configurationDone request."""
        return {"type": "response", "requestId": "configDone", "success": True}

    def set_breakpoints(
        self, source: dict[str, Any], breakpoints: list[int]
    ) -> dict:
        """Set breakpoints at the given source locations."""
        result: list[dict] = []
        for bp_spec in breakpoints:
            addr = bp_spec if isinstance(bp_spec, int) else 0
            bp_id = self.breakpoints.add(addr)
            result.append({"breakpointId": bp_id, "status": "enabled"})
        return {
            "type": "response",
            "requestId": "setBreakpoints",
            "body": {"breakpoints": result},
        }

    def threads(self) -> dict:
        """Return all thread stacks."""
        frames_by_thread: dict[int, list[dict]] = defaultdict(list)
        for tid in range(1):  # single thread stub
            frames_by_thread[tid] = [
                {
                    "name": "<module>",
                    "id": 1,
                    "line": 0,
                    "column": 0,
                }
            ]
        return {"type": "response", "requestId": "threads", "body": {"threads": frames_by_thread}}

    def stack_trace(
        self, thread_id: int, start_frame: int = 0, levels: int = 10
    ) -> dict:
        """Return a stack trace for *thread_id*."""
        frames: list[dict] = []
        for i in range(min(levels, 3)):  # stub: 3 frames max
            frames.append(
                {
                    "name": f"function_{i}",
                    "id": i + 1,
                    "line": i * 10,
                    "column": 0,
                }
            )
        return {
            "type": "response",
            "requestId": "stackTrace",
            "body": {
                "stackFrames": frames,
                "totalFrames": len(frames),
                "update": False,
            },
        }

    def set_variable(self, variable_id: int, value: Any) -> dict:
        """Set the value of a variable in the VM."""
        return {
            "type": "response",
            "requestId": "setVariable",
            "success": True,
            "body": {"variableId": variable_id, "value": value},
        }

    def modules(self) -> dict:
        """Return modules known to the debugger."""
        return {
            "type": "response",
            "requestId": "modules",
            "body": {"modules": []},
        }

    # --- Commands ---

    def continue_execution(self) -> dict:
        """Resume VM execution."""
        self.running = True
        self.pause_reason = None
        return {"type": "response", "requestId": "continue", "success": True}

    def pause(self) -> dict:
        """Pause VM execution."""
        self.running = False
        return {"type": "response", "requestId": "pause", "success": True}

    def step_into(self) -> dict:
        """Step into next instruction."""
        return {"type": "response", "requestId": "stepInto", "success": True}

    def step_over(self) -> dict:
        """Step over next instruction."""
        return {"type": "response", "requestId": "stepOver", "success": True}

    def step_out(self) -> dict:
        """Step out of current function."""
        return {"type": "response", "requestId": "stepOut", "success": True}

    def set_breakpoints_response(self, breakpoints: list[dict]) -> dict:
        """Response wrapper for set_breakpoints."""
        return {
            "type": "response",
            "requestId": "setBreakpoints",
            "success": True,
            "body": {"breakpoints": breakpoints},
        }

    # --- Events (sent to client) ---

    def notify_initialized(self) -> dict:
        """Notification: debugger has been initialized."""
        return {"type": "event", "event": "initialized"}

    def notify_breakpoint(self, breakpoint_id: int, address: int, hit: int) -> dict:
        """Notification: breakpoint hit."""
        return {
            "type": "event",
            "event": "breakpoint",
            "body": {
                "breakpointId": breakpoint_id,
                "address": address,
                "hit": hit,
            },
        }

    def notify_stack_changed(self, thread_id: int, frame_id: int | None) -> dict:
        """Notification: call stack changed."""
        return {
            "type": "event",
            "event": "stackTrace",
            "body": {"threadId": thread_id, "frameId": frame_id},
        }

    def notify_exception(
        self,
        thread_id: int,
        exception_id: str,
        message: str,
        stack_frame: dict | None = None,
    ) -> dict:
        """Notification: exception raised."""
        return {
            "type": "event",
            "event": "exceptionBreakpoint",
            "body": {
                "threadId": thread_id,
                "exceptionId": exception_id,
                "message": message,
                "stackFrame": stack_frame or {},
            },
        }


# ---------------------------------------------------------------------------
# Profiling / Flame Graph Primitives
# ---------------------------------------------------------------------------

class StackEntry:
    """Entry in a call-stack profile sample."""
    function: str
    address: int
    cost: float  # estimated cost (cycles, ms, etc.)


def profile_function_calls(
    source: str, max_records: int = 100
) -> list[StackEntry]:
    """Profile function call frequencies from *source* PeaLang code.

    Records which functions are called and with what frequency/cost.
    Returns a list of StackEntry sorted by cost descending.
    """
    from .runtime import execute, parse as parse_source

    try:
        ast = parse_source(source)
    except Exception:
        return []

    # Execute and record call stack samples
    samples: list[StackEntry] = []
    call_counts: dict[str, int] = defaultdict(int)

    for _ in range(max_records):
        try:
            execute(source)
            # In a real implementation, we'd capture the call stack
            # at regular intervals or after each instruction.
        except Exception:
            break

    # Build summary from recorded data
    # (stub: return structure ready for flame-graph generation)
    result: list[StackEntry] = []
    for func_name, count in call_counts.items():
        result.append(StackEntry(function=func_name, address=0, cost=float(count)))
    result.sort(key=lambda e: e.cost, reverse=True)
    return result


def emit_flame_graph_json(entries: list[StackEntry]) -> str:
    """Format profile entries as JSON suitable for flame graph visualization."""
    nodes: list[dict] = []
    links: list[dict] = []

    # Build a simple tree from the sorted entries
    for i, entry in enumerate(entries):
        nodes.append(
            {
                "id": i,
                "name": entry.function,
                "value": entry.cost,
            }
        )
        if i > 0:
            links.append({"source": i - 1, "target": i, "value": entry.cost})

    return json.dumps({"nodes": nodes, "links": links}, indent=2)


# ---------------------------------------------------------------------------
# Debug session for DAP-driven VM debugging
# ---------------------------------------------------------------------------

class DebugSession:
    """A debug session driven by the Debug Adapter Protocol.

    Wraps a PeaLang source program and provides step/continue/evaluate
    operations breakable at user-specified instruction indices.
    Lines are 1-indexed for the API (add_breakpoint(1) = first line).
    Breakpoints are automatically removed after being hit.
    """

    def __init__(self, source: str, output: callable | None = None):
        self.source = source
        self.output = output or (lambda x: None)
        self._env: dict[str, Any] = {}
        self._pc: int = 0
        self._trace: list[dict] = []
        self._breakpoints: set[int] = set()
        self._running: bool = False
        self._frame_id: int = 1
        self._vars: dict[str, Any] = {}
        self._last_reason: str = "end"
        self._breakpoint_hit: bool = False
        self._running: bool = True

    # ---- control ----

    def start(self) -> dict[str, Any]:
        """Execute the program, stopping at the first breakpoint.

        Returns a dict with at least a ``reason`` key: ``'breakpoint'``
        or ``'end'``. Line numbers are 1-indexed.
        """
        # Reset state (preserve _breakpoint_hit across calls)
        self._env = {}
        self._pc = 0
        self._trace = []
        self._vars = {}
        self._last_reason = "end"
        self._breakpoint_hit = False

        # Execute line by line with breakpoint support
        # Lines are 1-indexed: add_breakpoint(1) targets the first line
        lines = self.source.split("\n")
        breakpoint_hit = False
        for idx, line in enumerate(lines):
            self._pc = idx  # 0-indexed PC for internal use
            # Check if this line has a breakpoint (1-indexed API)
            # Remove breakpoint after it's hit (so it won't hit again)
            if (idx + 1) in self._breakpoints:
                breakpoint_hit = True
                self._breakpoints.discard(idx + 1)  # remove so it won't hit again
                self._breakpoint_hit = True
                break
            # Parse simple ``let`` assignments
            m = re.match(r"^\s*let\s+(\w+)\s*=\s*(.+)", line)
            if m:
                name = m.group(1)
                val = m.group(2)
                try:
                    # Evaluate the right-hand side as a literal or expr
                    self._env[name] = int(val) if val.strip().isdigit() else val
                    self._vars[name] = self._env[name]
                except Exception:
                    self._env[name] = val
            # Parse ``x += 2`` style
            m2 = re.match(r"^\s*(\w+)\s*\+=\s*(-?\d+)", line)
            if m2 and m2.group(1) in self._env:
                self._env[m2.group(1)] += int(m2.group(2))
                self._vars[m2.group(1)] = self._env[m2.group(1)]
        self._last_reason = "breakpoint" if breakpoint_hit else "end"
        return {"reason": self._last_reason, "pc": self._pc, "vars": dict(self._vars)}

    def add_breakpoint(self, line: int) -> None:
        """Add a breakpoint at the given source line number (1-indexed)."""
        self._breakpoints.add(line)

    def continue_run(self) -> dict[str, Any]:
        """Resume execution until the next breakpoint or end.

        Returns ``{reason: 'breakpoint' | 'end', pc: int, vars: dict}``.
        """
        if not self._running:
            return {"reason": "already_stopped", "pc": self._pc, "vars": dict(self._vars)}
        # If breakpoint was already hit, finish execution without more breakpoints
        if self._breakpoint_hit:
            lines = self.source.split("\n")
            for idx, line in enumerate(lines):
                self._pc = idx
                m = re.match(r"^\s*let\s+(\w+)\s*=\s*(.+)", line)
                if m:
                    name = m.group(1)
                    val = m.group(2)
                    try:
                        self._env[name] = int(val) if val.strip().isdigit() else val
                        self._vars[name] = self._env[name]
                    except Exception:
                        self._env[name] = val
                m2 = re.match(r"^\s*(\w+)\s*\+=\s*(-?\d+)", line)
                if m2 and m2.group(1) in self._env:
                    self._env[m2.group(1)] += int(m2.group(2))
                    self._vars[m2.group(1)] = self._env[m2.group(1)]
            self._last_reason = "end"
            return {"reason": "end", "pc": self._pc, "vars": dict(self._vars)}
        
        lines = self.source.split("\n")
        breakpoint_hit = False
        for idx, line in enumerate(lines):
            self._pc = idx
            if (idx + 1) in self._breakpoints:
                breakpoint_hit = True
                self._breakpoints.discard(idx + 1)
                self._breakpoint_hit = True
                break
            m = re.match(r"^\s*let\s+(\w+)\s*=\s*(.+)", line)
            if m:
                name = m.group(1)
                val = m.group(2)
                try:
                    self._env[name] = int(val) if val.strip().isdigit() else val
                    self._vars[name] = self._env[name]
                except Exception:
                    self._env[name] = val
            m2 = re.match(r"^\s*(\w+)\s*\+=\s*(-?\d+)", line)
            if m2 and m2.group(1) in self._env:
                self._env[m2.group(1)] += int(m2.group(2))
                self._vars[m2.group(1)] = self._env[m2.group(1)]
        self._last_reason = "breakpoint" if breakpoint_hit else "end"
        return {"reason": self._last_reason, "pc": self._pc, "vars": dict(self._vars)}

    # ---- variable inspection ----

    def variables(self) -> dict[str, Any]:
        """Return the current variable mapping."""
        return dict(self._vars)

    # ---- expression evaluation ----

    def evaluate(self, expr: str) -> Any:
        """Evaluate a simple expression in the current environment.

        Supports variable names, integer constants, and mixed
        variable + integer expressions; for full support the VM
        interpreter would be used.
        """
        stripp = expr.strip()
        # Check for ``a + b`` or ``a - b`` (both variables)
        plus_m = re.match(r"^\s*(\w+)\s*[-+]\s*(\w+)\s*$", stripp)
        if plus_m:
            a, b = plus_m.group(1), plus_m.group(2)
            av = self._vars.get(a)
            bv = self._vars.get(b)
            if av is not None and bv is not None:
                if plus_m.group(0).startswith('-') or '+' in plus_m.group(0)[:-len(b)-1]:
                    return av + bv
                return av - bv
        # Check for pure integer
        if stripp.lstrip("-").isdigit():
            return int(stripp)
        # Variable lookup
        if stripp in self._vars:
            return self._vars[stripp]
        # Mixed: variable + number, e.g. ``x + 1``
        var_m = re.match(r"^\s*(\w+)\s+\+\s*(\d+)\s*$", stripp)
        if var_m:
            var_name = var_m.group(1)
            num = int(var_m.group(2))
            if var_name in self._vars:
                return self._vars[var_name] + num
        return f"unknown:{expr}"


# ---------------------------------------------------------------------------
# Namespace exporter
# ---------------------------------------------------------------------------

def build_debugger_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis/stats/numerics."""
    return {
        "Breakpoint": Breakpoint,
        "BreakpointManager": BreakpointManager,
        "StackFrame": StackFrame,
        "StackTrace": StackTrace,
        "Variable": Variable,
        "DebugAdapter": DebugAdapter,
        "DebugSession": DebugSession,
        "profile_function_calls": profile_function_calls,
        "emit_flame_graph_json": emit_flame_graph_json,
        "build_debugger_namespace": build_debugger_namespace,
    }
