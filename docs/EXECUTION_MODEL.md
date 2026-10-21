# PeaLang Execution Model

## What a user needs
A PeaLang user needs the PeaLang runtime/interpreter and a `.pea` program. They do not need a compiler.

```text
program.pea
   -> Lexer
   -> Parser
   -> typed AST
   -> Interpreter
   -> output / side effects
```

## Commands
`pea app.pea` and `pea run app.pea` execute source. `pea repl` runs interactively. `pea start` resolves `pea.json` and runs the project entry file.

## Current implementation
The runtime is hosted on Python 3.9+ and performs tree-walk AST interpretation. This is an implementation detail exposed by the current development installation, not a requirement of PeaLang syntax.

## Future runtime path
1. Stabilise grammar and semantics.
2. Strengthen modules, types and standard library.
3. Package the interpreter as a standalone runtime so users do not need Python knowledge.
4. Profile real workloads.
5. Prototype Pea bytecode and a VM only if it provides clear performance/distribution benefits.

A native-machine-code compiler is not a v0.x requirement.
