# PeaLang User Guide v0.9.0

## Run code
Install the runtime, create a `.pea` file and run `pea file.pea`. For a project, use `pea init` then `pea start`. Use `pea repl` for experiments.

## Write robust programs
Use `try/catch/finally` around operations that can fail and `throw` for domain validation failures. Catch errors close to where you can handle them meaningfully; allow unexpected errors to surface during development.

## Design functions
Put mandatory arguments first and optional arguments last. Defaults make common calls concise without requiring overloads.

## Develop
Format, check and test before running. Project/module, automation, workflow, AI and agent capabilities from earlier releases remain available, but language maturity is now the primary roadmap.
