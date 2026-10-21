# Projects and Modules Guide v0.7.0

## Project manifest
A project is identified by `pea.json`. The required `project` fields are `name`, `version`, and `entry`. `dependencies` must be a dictionary.

## Discovery
When a file is run, PeaLang searches its directory and parent directories for `pea.json`. Project-aware execution passes the project root and dependency map to the interpreter.

## Modules
A bare import such as `import "math"` first resolves `modules/math.pea` at the project root. Explicit relative paths and `.pea` file imports preserve the earlier behaviour.

## Dependencies
`pea add NAME PATH` records a local path. If that path is another PeaLang project, its manifest entry file is imported. Dependencies still share the interpreter global namespace in v0.7.

## Commands
- `pea init app` creates a manifest, entry file and modules directory.
- `pea project` prints resolved manifest information.
- `pea add name path` writes a path dependency.
- `pea remove name` removes it.
- `pea start` runs the configured entry file.

## Boundaries
No registry, download/install operation, semver solver, lockfile, namespaced exports, private/public module symbols or dependency isolation exists yet.
