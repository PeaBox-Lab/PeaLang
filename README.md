# PeaLang 0.15.0

PeaLang is a readable automation and AI-workflow language. Version 0.15 introduces a Debug Adapter Protocol foundation for editor debugging.

## Install
```bash
python -m venv .venv
python -m pip install -e .
pea --version
```

## Debug
```bash
pea debug examples/hello.pea --break=2
pea dap
```

The DAP supports initialize, launch, breakpoints, continue, next, step-in, step-out, threads, stack traces, scopes, variables, evaluate and disconnect.
