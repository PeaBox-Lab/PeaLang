# Troubleshooting

- **Module not found:** verify `.pea` spelling, current directory, `modules/`, and `pea.json`.
- **Circular import:** move shared declarations to a third module.
- **Undefined variable:** check scope and the suggested spelling.
- **Process disabled:** use `--allow-process` only after reviewing the program.
- **AI credential missing:** set the environment variable configured in `api_key_env`.
