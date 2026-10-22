# PeaLang 0.16.0

PeaLang is a readable, Python-hosted language for automation, workflows, AI integrations, agents, and practical scripting. Version 0.16 strengthens editor debugging with function-aware frames, frame-local scopes, conditional and hit-count breakpoints, exception stops, source-aware breakpoints, and proper DAP lifecycle events.

## Requirements

- Python 3.10 or newer
- Windows, Linux, or macOS

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
pea repl
pea check examples
pea fmt examples
pea test
```

## Debugging

```bash
pea debug examples/hello.pea --break=2
pea dap
```

The DAP adapter supports initialize, launch, source breakpoints, conditional breakpoints, hit conditions, log points, exception breakpoints, continue, next, step-in, step-out, threads, stack traces, frame scopes, variables, evaluate, disconnect, and terminate.

### Hit conditions

- `3`: stop on the third hit
- `>=3`: stop on the third and later hits
- `%2`: stop on every second hit

## Safety

Process execution remains disabled by default. Use `--allow-process` only for trusted PeaLang programs.

## Documentation

Start with `docs/FOUNDATIONS.md`, `docs/BASICS.md`, `docs/USER_GUIDE.md`, and `docs/DEBUG_ADAPTER.md`. See `LANGUAGE.md` for the language summary and `ROADMAP.md` for planned releases.
