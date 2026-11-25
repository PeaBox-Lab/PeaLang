# Bytecode optimizer

Wave 2 adds an optional, deterministic optimizer for portable `.peac` bytecode.
It is a host/runtime facility, not a language feature: the frozen 3.0 surface
defined by `CORE_SURFACES` is unchanged.

The optimizer operates on a deep copy of a `BytecodeModule`, including every
function code object, and applies three conservative passes:

- `constant_folding` rewrites `CONST a, CONST b, OP` triples into one constant
  for numeric arithmetic and same-type comparisons, and rewrites `CONST, NEG`
  into one constant. Division or modulo by zero is never folded.
- `dead_push_pop` removes a literal push immediately followed by `POP`, since
  literal pushes have no observable side effects.
- `unreachable_code` removes instructions unreachable from entry or from any
  jump, exception-handler, or iterator-end target, then remaps every remaining
  target. Branches targeting the end of code remain valid.

Source line numbers are preserved. New constant values reuse an existing entry
only when the type and value both match.

`optimize_bytecode()` returns the optimized module. `optimize_report()` returns
pass counts, before/after instruction and constant counts, a SHA-256 digest of
the optimized artifact, and a PASS/FAIL gate. `verify_optimization()` runs the
original and optimized modules on the virtual machine with an instruction limit
and requires identical output and return values.

The `pea optimize FILE.pea [--verify] [-o OUT.peac]` command exposes the same
operations to users. Individual passes can be disabled with
`--no-constant-folding`, `--no-dead-push-pop`, and `--no-unreachable-code`.
The `runtime.bytecode_optimizer_v3` feature flag records availability.
