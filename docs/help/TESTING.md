# Pea Test Help
Put executable `.pea` scenarios under `pea_tests/` and run `pea test pea_tests/`. A thrown parser/runtime error fails a test. The runner does not yet capture expected output or provide native assertions. Use Python `unittest` for interpreter implementation tests.
