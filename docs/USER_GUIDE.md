# PeaLang User Guide v0.10.0

## Run programs
Use `pea file.pea`, `pea run file.pea`, `pea repl`, or `pea start` for a project.

## Structure programs
Move related reusable functions/constants into modules, explicitly export their public API, then import with an alias. Prefer `math.square()` over placing `square()` directly into global scope.

## Preserve compatibility
Existing unaliased imports still work. Convert them gradually when namespace boundaries are useful.

## Develop safely
Use `pea check` to catch undefined exported symbols and ordinary source errors, then run tests. Module visibility prevents name collisions but does not isolate filesystem/network/process permissions.
