# Getting started with PeaLang

This walkthrough gets you from a clone to a running service. Every step is
self-contained — no documentation beyond this file is required.

## 0. Prerequisites

- Python 3.10 or newer
- Node 18+ and `npm` (only for the React frontend example)
- Network access for `pip install` and `npm install`

## 1. Install PeaLang

```bash
pip install -e .
```

## 2. Verify the installation

```bash
pea doctor            # reports environment diagnostics
pea cheatsheet        # developer cheat sheet (if available in your build)
```

You can also evaluate a snippet directly:

```bash
pea eval -e 'print 1 + 2'
```

## 3. Quick sanity check — run a source file

```bash
pealang run examples/getting_started/hello.pea
```

Expected output includes: `Hello from PeaLang!` and `x + 1 = 6`.

## 4. Aggregate project health

```bash
pea eval -e 'print "diagnostics ok"'   # quick check
python -m pytest -q                      # runs the full regression suite
```

## 5. Generate a ready-to-run backend

```bash
pea scaffold fastapi ./myservice
cd myservice
python -m venv .venv && . .venv/bin/activate   # or .\.venv\Scripts\activate on Windows
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload
```

A complete, pre-generated version lives at `examples/getting_started/fastapi_orders/` — copy it and run the same commands.

## 6. Generate a full-stack app

```bash
pea scaffold fullstack ./myshop
```

Or copy `examples/getting_started/fullstack_shop/`. See `examples/getting_started/README.md`.

## 7. Diagnostics for your own code

```bash
python -c "from pealang.devx import project_check; print(project_check('.'))"
```

`project_check` walks your `.pea` files (bounded at 50) and returns per-file
counts plus a totals summary suitable for CI.
