# PeaLang User Guide v0.4.0

## Install
From the project root, run `python -m pip install -e .`. Verify with `pea --version`.

## Create and run a project
Create `main.pea`, write your program, run `pea fmt main.pea`, then `pea check main.pea`, and finally `pea run main.pea`.

## Organize code
Keep the entry file small and place reusable functions in local `.pea` files imported with `import "helpers.pea"`. Imported declarations currently enter shared global scope, so use distinct names.

## Work with business data
Use `csv.read` for row dictionaries and `json.read`/`json.write` for nested data. Remember that CSV values are strings. Construct portable paths with `path.join`.

## Configuration and secrets
Read non-secret and secret configuration through `env.get` or `env.require`. Do not place tokens in source, examples, logs or Git history.

## Network and processes
Use `http.get`, `http.post` or `http.request` with explicit timeouts. Check `response.ok` and `response.status` before decoding JSON. Process execution is off by default. Enable it only for reviewed scripts.

## Quality workflow
Format before commit, check every source directory, run Python interpreter tests, run PeaLang smoke tests, generate API docs for reusable libraries, and review the security implications of I/O.

## Troubleshooting
Read `docs/help/CLI.md`, `FORMATTER.md`, `CHECKER.md`, `TESTING.md`, `ERRORS.md`, `IMPORTS.md`, and `AUTOMATION.md`.
