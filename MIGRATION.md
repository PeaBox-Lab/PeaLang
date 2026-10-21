# Migrating from 0.10.0

1. Replace the package and reinstall with `python -m pip install -e .`.
2. Existing `pea.json` files remain valid because missing `manifest_version` is treated as version 1.
3. Ensure each project entry ends in `.pea`.
4. Resolve any newly reported circular imports.
5. Re-run `pea check .` and `pytest`.
