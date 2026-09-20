# PeaLang

PeaLang is a compact, readable programming language implemented in Python. Version 0.1 includes variables, constants, expressions, conditions, loops, functions, recursion, lists, dictionaries, file operations, a REPL, and a CLI.

## Quick start

### Windows

```bat
install.bat
.venv\Scripts\pealang examples\features.pea
```

### Linux or macOS

```bash
chmod +x install.sh
./install.sh
.venv/bin/pealang examples/features.pea
```

### Without installation

```bash
python -m pealang examples/hello.pea
```

## Language example

```text
const tax = 18
let values = [100, 250, 500]
let total = 0

for value in values {
    total += value
}

function add_tax(amount) {
    return amount + amount * tax / 100
}

print add_tax(total)
```

## Commands

```bash
pealang program.pea
pealang
pealang --version
python -m unittest discover -s tests
```

## Built-ins

`range`, `len`, `str`, `number`, `int`, `type`, `upper`, `lower`, `split`, `join`, `append`, `keys`, `values`, `json`, `read`, `write`, `exists`, `sqrt`, `round`, and `sleep`.

See `docs/LANGUAGE.md` for the language reference.
