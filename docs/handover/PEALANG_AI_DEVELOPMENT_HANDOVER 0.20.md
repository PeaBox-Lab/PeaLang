



# PeaLang AI Development Handover 0.20

## Product direction

PeaLang is an embeddable extension language. Version 0.20 adds its first portable execution layer: PEAC bytecode and a stack VM.

## Implementation

- `pealang.bytecode`: opcodes, instructions, code objects, module serialization
- `pealang.compiler`: AST-to-bytecode lowering
- `pealang.vm`: instruction pointer, stack, frames, closures, exports, and instruction budget
- `pealang.disassembler`: readable instruction listing
- CLI commands: `compile`, `dis`, and `vm`

## Current compiler subset

Literals, variables, arithmetic, comparisons, lists, dictionaries, property/index access, if/else, loops, functions, calls, returns, exports, and selected built-ins.

## Next build

Version 0.21 should close VM parity gaps: break/continue patch stacks, compound/property/index assignment, try/catch/finally/throw, lexical closure cells, module loading, imported source maps, default arguments, debugger pause/resume hooks, and VM differential conformance tests.

## Release rule

Every future release must include cumulative changelog, detailed release notes, README, roadmap, version history, foundations, complete user/embedding guides, help pages, security and architecture notes, tests, examples, and an updated AI handover.




