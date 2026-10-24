
# PEAC Format 1

The `.peac` artifact contains:

- `format`: always `PEAC`
- `version`: bytecode format version, currently `1`
- `source_name`: originating source identity
- `constants`: JSON-safe constant pool
- `code`: top-level code object
- `functions`: named function code objects

Each instruction contains `op`, optional `arg`, and original source `line`. Consumers must reject unknown format markers and should reject unsupported bytecode versions. The format is preview and not yet guaranteed stable across minor releases.
