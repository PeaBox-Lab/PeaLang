# User Guide

## Workflow
1. `pea init my-project`
2. Edit `main.pea`.
3. Run `pea check .`.
4. Run `pea start`.
5. Put reusable modules in `modules/`.
6. Put executable language tests in `pea_tests/` with optional matching `.out` files.

## Automation
Use `file`, `json`, `csv`, `http`, and `datetime`. Enable `process.run` only for trusted code with `--allow-process`.
