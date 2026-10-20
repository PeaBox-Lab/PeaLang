# PeaLang v0.4.0

**A small language for big ideas.** PeaLang is a readable, Python-hosted programming language for learning, scripting, business automation, data work, and future AI workflows.

v0.4.0 is the **Developer Experience release**. It adds a formatter, static checker, PeaLang test runner, API documentation generator, richer REPL commands, and a consolidated CLI while retaining the v0.1-v0.3 language and automation capabilities.

## Start in five minutes

```bash
python -m pip install -e .
pea --version
pea examples/hello.pea
pea repl
```

Create `hello.pea`:

```pea
let name = "Rajesh"
let ideas = ["automation", "AI", "HR systems"]
print "Hello {name}. You have {len(ideas)} ideas."
```

Run and validate it:

```bash
pea run hello.pea
pea fmt hello.pea
pea check hello.pea
```

## v0.4.0 commands

```text
pea program.pea                  Run a file, compatible with earlier releases
pea run program.pea              Explicit run command
pea repl                         Open the interactive shell
pea fmt file.pea                 Format one file
pea fmt src/                     Format all .pea files recursively
pea fmt --check src/             Report files that need formatting
pea check file.pea               Parse and statically inspect a file
pea check src/                   Check a directory recursively
pea test pea_tests/              Execute discovered .pea test programs
pea docs library.pea             Generate Markdown API documentation
pea docs library.pea -o API.md   Save generated documentation
pea --version                    Show the version
```

## Language at a glance

```pea
const tax_rate = 18
let prices = [100, 250, 500]
let total = 0

for price in prices {
    total += price
}

function add_tax(amount, rate) {
    return amount + amount * rate / 100
}

let employee = {"name": "Rajesh", "city": "Gurgaon"}
employee.city = "Delhi"
print "{employee.name}: {add_tax(total, tax_rate)}"
```

PeaLang supports values, variables/constants, operators, conditions, loops, `break`/`continue`, functions and closures, recursion, lists, dictionaries, index/property mutation, interpolation, local imports, files, JSON, CSV, paths, environment variables, date/time, regular expressions, HTTP calls and guarded processes.

## Developer tooling

### Formatter
`pea fmt` produces one stable layout and is idempotent. `--check` makes it usable in CI without modifying files.

### Checker
`pea check` reports parser errors, undefined variables (`P101`), duplicate declarations (`P102`) and unused variables (`P104`). The checker is intentionally conservative and is not a full type system.

### Pea test runner
Every `.pea` file under the supplied path is a test program. A file passes when it completes without an error and fails when parsing or execution raises an error. Use Python `unittest` for interpreter internals and `pea test` for language-level smoke/integration programs.

### API docs
`pea docs` scans top-level public functions and emits Markdown signatures and source locations. Functions beginning with `_` are treated as private.

### REPL
The REPL retains definitions between inputs. Use `:help`, `:vars`, and `:clear`.

## Automation example

```pea
let rows = csv.read("employees.csv")
let active = []

for row in rows {
    if row.status == "Active" {
        append(active, row)
    }
}

json.write(path.join("output", "active.json"), active)
print "Exported {len(active)} active employees"
```

## Safety
PeaLang is experimental and **not sandboxed**. File, import, environment and HTTP operations use host permissions. `process.run` is blocked by default and requires `pea run --allow-process trusted.pea`. Never run untrusted PeaLang programs or commit credentials.

## Documentation map

- `docs/GETTING_STARTED.md`: installation and first program
- `docs/LANGUAGE_BASICS.md`: beginner lessons and worked examples
- `docs/FOUNDATIONS.md`: how the language works and core design concepts
- `LANGUAGE.md`: concise reference
- `docs/USER_GUIDE.md`: practical end-to-end usage
- `docs/TOOLING_GUIDE.md`: formatter, checker, tests, docs and REPL
- `docs/STANDARD_LIBRARY.md`: automation APIs
- `docs/help/`: task-specific troubleshooting and command help
- `CHANGELOG.md`, `RELEASE_NOTES.md`, `ROADMAP.md`: release history and direction

## Install, test and package

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
pea test pea_tests/
python -m pip wheel . --no-deps --no-build-isolation
```

## Compatibility
Programs from v0.1-v0.3 remain supported. The direct `pea file.pea` form remains valid. Existing flat built-ins are retained while namespaced v0.3 APIs are preferred for automation.

## License
MIT. See `LICENSE`.
