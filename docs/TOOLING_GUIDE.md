# Developer Tooling Guide

## Format
`pea fmt app.pea` rewrites a file. `pea fmt src/` processes `.pea` files recursively. `pea fmt --check src/` returns exit code 1 if formatting is required.

## Check
`pea check app.pea` runs parser validation and static checks. Codes: `P100` syntax/parser error, `P101` undefined variable, `P102` duplicate declaration, and `P104` unused variable warning. Warnings do not make the command fail; errors do.

## Test
`pea test pea_tests/` discovers `.pea` files recursively. A test passes if it exits normally. For assertions in v0.4, encode a failing path that calls an undefined function when the condition is false, as demonstrated in `pea_tests/smoke.pea`. A dedicated assertion language is planned.

## Docs
`pea docs library.pea -o API.md` generates a Markdown index of top-level public functions. It is intentionally minimal in v0.4 and does not yet extract doc comments.

## REPL
`pea repl` opens a persistent interpreter. `:vars` lists global names, `:clear` creates a fresh interpreter, `:help` lists commands, and `exit` leaves.

## CI pattern
```bash
pea fmt --check examples/
pea check examples/
python -m unittest discover -s tests -v
pea test pea_tests/
```
