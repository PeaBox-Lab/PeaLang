# Architecture
Source passes through `Lexer -> Parser -> typed AST -> Interpreter`. `Env` provides lexical scope; `UserFunction` captures its defining environment. `runtime.py` preserves the v0.1 public API. Imports are interpreted recursively with one-execution tracking and entry-file-relative resolution. Control-flow signals are internal exceptions caught at function or loop boundaries.
