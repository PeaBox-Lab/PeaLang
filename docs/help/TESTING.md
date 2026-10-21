# Pea Test Help v0.5.0
Put executable `.pea` files under `pea_tests/` and run `pea test pea_tests/`. Use native `assert` for conditions. To validate console output, create a sibling file with the same base name and `.out` extension. Output is compared line-by-line exactly. Any parser/runtime/assertion error fails the test. Use Python `unittest` for interpreter internals.
