# PeaLang v0.3.0

**A small language for big ideas.** v0.3.0 turns PeaLang into a practical automation language while preserving the v0.1 and v0.2 language foundation.

## Highlights

- Structured namespaces: `file`, `path`, `json`, `csv`, `env`, `datetime`, `regex`, `http`, and `process`
- UTF-8 file operations and parent-directory creation
- JSON and CSV read/write workflows
- Environment-variable access without embedding secrets
- ISO-oriented date/time helpers
- Regular-expression search, replace, find and split
- HTTP GET/POST/request with structured responses and timeouts
- Process execution disabled by default and enabled only with `--allow-process`

## Quick start

```bash
python -m pip install -e .
pea examples/automation.pea
python -m unittest discover -s tests -v
```

```pea
let employees = csv.read("employees.csv")
for employee in employees {
    print "{employee.name}: {employee.department}"
}
```

## Standard-library example

```pea
let response = http.get("https://example.com", {}, 10)
print response.status

let data = json.parse("{\"name\":\"PeaLang\"}")
file.write(path.join("output", "name.txt"), data.name)
```

## Security defaults

`process.run` is blocked unless the CLI receives `--allow-process` or the Python API uses `allow_process=True`. PeaLang is still not a sandbox: files, imports, environment variables and network calls use the host process permissions. Run only trusted `.pea` programs.

## Commands

- `pea program.pea`
- `pea --allow-process trusted.pea`
- `pea` for the REPL
- `pea --version`
- `pealang` remains a compatible alias

See `LANGUAGE.md`, `docs/STANDARD_LIBRARY.md`, `docs/SECURITY_MODEL.md`, and `ROADMAP.md`.
