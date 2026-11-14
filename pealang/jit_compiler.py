"""Just-In-Time compilation hints and optimizations for the PeaLang VM.

Provides:
- Register allocation hints
- Basic block optimization
- Inline caching for property access
- Loop invariant code motion
- Trace-based JIT compilation skeleton
"""

from __future__ import annotations

import json
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Iterable, NamedTuple


# ---------------------------------------------------------------------------
# Instruction metadata
# ---------------------------------------------------------------------------

class InstructionInfo(NamedTuple):
    """Metadata for a VM instruction."""
    name: str
    latency: float  # estimated cycles
    throughput: float  # ops per cycle
    reads: frozenset[str]  # register names read
    writes: frozenset[str]  # register names written


# Instruction catalog (subset — extends as needed)
INSTRUCTION_CATALOG: dict[str, InstructionInfo] = {
    "LOAD": InstructionInfo("LOAD", 1.0, 1.0, {"addr"}, {"r"}),
    "STORE": InstructionInfo("STORE", 1.0, 1.0, {"r"}, {"addr"}),
    "ADD": InstructionInfo("ADD", 1.0, 0.5, {"r1", "r2"}, {"r3"}),
    "SUB": InstructionInfo("SUB", 1.0, 0.5, {"r1", "r2"}, {"r3"}),
    "MUL": InstructionInfo("MUL", 3.0, 1.0, {"r1", "r2"}, {"r3"}),
    "DIV": InstructionInfo("DIV", 10.0, 1.0, {"r1", "r2"}, {"r3"}),
    "MOD": InstructionInfo("MOD", 10.0, 1.0, {"r1", "r2"}, {"r3"}),
    "POW": InstructionInfo("POW", 5.0, 1.0, {"r1", "r2"}, {"r3"}),
    "CALL": InstructionInfo("CALL", 20.0, 1.0, {"func", "arg"}, {"r"}),
    "RETURN": InstructionInfo("RETURN", 5.0, 1.0, {"r"}, set()),
    "JUMP": InstructionInfo("JUMP", 2.0, 1.0, {"addr"}, set()),
    "JMPZ": InstructionInfo("JMPZ", 2.0, 1.0, {"r", "addr"}, set()),
    "DEF": InstructionInfo("DEF", 2.0, 1.0, {"name", "val"}, {"loc"}),
    "GETATTR": InstructionInfo("GETATTR", 2.0, 1.0, {"obj", "attr"}, {"r"}),
    "SETATTR": InstructionInfo("SETATTR", 2.0, 1.0, {"obj", "val", "attr"}, set()),
}


# ---------------------------------------------------------------------------
# Optimization passes
# ---------------------------------------------------------------------------

def optimize_instructions(
    instructions: list[dict[str, Any]],
    hints: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Apply a sequence of optimization passes to register-based instructions.

    Passes included (feature flags in *hints*):
    - "constant_folding" — fold constant expressions
    - "dead_code_elimination" — remove unused instructions
    - "inline_caching" — cache property/attribute lookups
    - "loop_invariants" — hoist loop-invariant code
    - "strength_reduction" — replace expensive ops with cheap ones
    """
    if hints is None:
        hints = {}

    # 1. Constant folding
    if hints.get("constant_folding", True):
        instructions = _constant_fold(instructions)

    # 2. Dead code elimination
    if hints.get("dead_code_elimination", True):
        instructions = _dead_code_elimination(instructions)

    # 3. Inline caching
    if hints.get("inline_caching", True):
        instructions = _inline_caching(instructions)

    # 4. Loop invariant hoisting
    if hints.get("loop_invariants", True):
        instructions = _loop_invariant_hoist(instructions)

    # 5. Strength reduction
    if hints.get("strength_reduction", True):
        instructions = _strength_reduction(instructions)

    return instructions


def _constant_fold(instructions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fold constant sub-expressions."""
    out: list[dict[str, Any]] = []
    i = 0
    while i < len(instructions):
        instr = instructions[i]
        op = instr.get("op")
        if op in ("ADD", "SUB", "MUL", "DIV") and i + 1 < len(instructions):
            nxt = instructions[i + 1]
            # Pattern: op a, b  followed by STORE c, r  →  constant assignment
            if nxt.get("op") == "STORE" and nxt.get("arg") == instr.get("arg1", "?"):
                # Try to resolve both args to constants
                a = _resolve_reg_or_const(instructions, i - 1, nxt.get("arg1"))
                b = _resolve_reg_or_const(instructions, i, nxt.get("arg2"))
                if a is not None and b is not None:
                    result = _arith_op(op, a, b)
                    # Replace with LOAD immediate
                    out.append({"op": "LOAD", "arg": result})
                    i += 2  # skip op + STORE
                    continue
        out.append(instr)
        i += 1
    return out


def _resolve_reg_or_const(
    instructions: list[dict[str, Any]], pc: int, ref: str,
) -> int | None:
    """Resolve a register or immediate to a constant integer, if possible."""
    # Very simple: look for a prior LOAD immediate
    for j in range(max(0, pc - 10), pc):
        if instructions[j].get("op") == "LOAD":
            arg = instructions[j].get("arg")
            if isinstance(arg, int):
                return arg
    return None


def _arith_op(op: str, a: int, b: int) -> int:
    if op == "ADD":
        return a + b
    if op == "SUB":
        return a - b
    if op == "MUL":
        return a * b
    if op == "DIV":
        return a // b  # integer division for PeaLang
    raise ValueError(f"unknown op {op}")


def _dead_code_elimination(
    instructions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove instructions whose result is never read."""
    # Build liveness map: which registers are written/read
    writes: dict[str, int] = {}  # reg → last instruction index that writes it
    read_set: set[str] = set()

    # First pass: collect all reads
    for idx, instr in enumerate(instructions):
        for r in instr.get("reads", frozenset()) | instr.get("writes", frozenset()):
            if "r" in str(r) or instr.get("op") in ("LOAD", "ARG", "IMPORT"):
                read_set.add(r)

    # Second pass: keep only instructions whose writes reach a read
    kept: list[dict[str, Any]] = []
    last_write: dict[str, int] = {}

    for idx, instr in enumerate(instructions):
        w = instr.get("writes", "")
        r = instr.get("reads", "")
        # Keep if it defines something that is later read, or it's a control flow
        if w and w not in read_set and not any(
            rr in read_set for rr in (writes or {})
        ):
            # Dead write — skip
            continue
        kept.append(instr)
        if w:
            last_write[w] = idx

    return kept


def _inline_caching(instructions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Insert inline-cache guard checks for property access."""
    out: list[dict[str, Any]] = []
    for instr in instructions:
        if instr.get("op") == "GETATTR":
            # Prepend a cache check: if receiver class matches, skip attribute lookup
            cache_check = {
                "op": "IC_CHECK",
                "recv": instr.get("args", {}).get("obj"),
                "expected_type": "dict",  # simplified
            }
            out.append(cache_check)
        out.append(instr)
    return out


def _loop_invariant_hoist(
    instructions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Move loop-invariant computations before the loop."""
    # Simple placeholder: in a real VM this would analyze dominator trees.
    # For now, we just return as-is.
    return instructions


def _strength_reduction(instructions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Replace expensive operations with cheaper equivalents."""
    out: list[dict[str, Any]] = []
    for instr in instructions:
        op = instr.get("op")
        if op == "POW" and instr.get("arg1") == 2:
            # x**2 → x*x (multiplication is cheaper)
            out.append({"op": "MUL", "arg1": instr["arg2"], "arg2": instr["arg2"]})
        elif op == "DIV" and instr.get("arg2") == 2:
            # x/2 → x*0.5 (multiplication by float is cheaper)
            out.append({"op": "MUL", "arg1": instr["arg1"], "arg2": 0.5})
        else:
            out.append(instr)
    return out


# ---------------------------------------------------------------------------
# Trace-based JIT compilation skeleton
# ---------------------------------------------------------------------------

class JITTrace(NamedTuple):
    """A recorded execution trace for JIT compilation."""
    pc: int  # program counter start
    instructions: list[dict[str, Any]]
    guard: str | None  # type guard or guard condition
    exit_count: int  # how many times the trace was exited


def record_trace(
    source: str,
    max_records: int = 100,
) -> JITTrace | None:
    """Record a execution trace from *source* PeaLang code for JIT compilation.

    Returns a JITTrace if enough iterations were recorded, else None.
    """
    from .runtime import execute, parse as parse_source

    try:
        ast = parse_source(source)
    except Exception:
        return None

    # Execute and record instruction trace
    recorded: list[dict[str, Any]] = []
    exit_count = 0

    for _ in range(max_records):
        try:
            execute(source)
            # In a real implementation, we'd capture the bytecode instructions
            # executed and their operands here.
        except Exception:
            exit_count += 1
            break

    if exit_count == 0 and recorded:
        # We have a hot trace — return a skeleton for JIT compilation
        return JITTrace(
            pc=0,
            instructions=recorded,
            guard=None,
            exit_count=exit_count,
        )
    return None


def emit_native(stub: dict[str, Any]) -> bytes:
    """Emit a native code stub from a JIT-compiled representation.

    In v2.2 this would output x86-64 or WebAssembly machine code.
    For now, we return a placeholder bytecode marker.
    """
    marker = b"JIT_STUB"
    payload = json.dumps(stub, default=str).encode("utf-8")
    return marker + len(payload).to_bytes(4, "big") + payload


def build_jit_namespace() -> dict[str, Any]:
    """Return a namespace dict for registration in analysis/stats/numerics."""
    return {
        "InstructionInfo": InstructionInfo,
        "INSTRUCTION_CATALOG": INSTRUCTION_CATALOG,
        "optimize_instructions": optimize_instructions,
        "JITTrace": JITTrace,
        "record_trace": record_trace,
        "emit_native": emit_native,
        "build_jit_namespace": build_jit_namespace,
    }
