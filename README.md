# PeaLang 0.14.0

PeaLang is a compact language for readable automation, workflows and AI-oriented tools. Version 0.14 adds debugger and cross-file workspace foundations while preserving the established interpreter, standard library, AI, skills, agents and project tooling.

## Install
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e .
pea --version
```

## Run
```bash
pea run examples/hello.pea
pea debug examples/hello.pea --break=2
pea index .
```

## Debugger
`DebugSession` supports top-level breakpoints, step, continue, variable snapshots and a module stack frame. The command-line debugger emits JSON suitable for editor integration. Function-level stepping and a full Debug Adapter Protocol are planned next.

## Security
PeaLang is not a sandbox. Keep process execution disabled for untrusted programs.
