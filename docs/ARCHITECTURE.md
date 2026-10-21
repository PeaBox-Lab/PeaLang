# Architecture

Source passes through Lexer → Parser → AST → Interpreter. `Env` provides lexical scope. `project.py` resolves manifests and modules. `stdlib.py` builds runtime namespaces. `tooling.py` implements formatting, diagnostics, discovery, and API notes.
