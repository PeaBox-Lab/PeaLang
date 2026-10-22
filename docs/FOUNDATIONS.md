# PeaLang Foundations

A PeaLang program is a UTF-8 `.pea` file. Execute it with `pea run FILE`. The runtime lexes and parses source into an AST, then evaluates it with the tree-walking interpreter.

## First program

```pea
let name = "PeaLang"
print "Hello {name}"
```

## Core model

- `let` declares mutable values; `const` declares constants.
- Functions use lexical closures and support default parameters.
- `if`, `while`, and `for` provide control flow.
- Lists and dictionaries hold structured data.
- `try`, `catch`, `finally`, and `throw` provide error handling.
- Imports can expose exported module symbols under an alias.
- Built-in namespaces cover files, paths, JSON, CSV, environment variables, dates, regex, HTTP, processes, tasks, workflows, AI, tools, agents, and skills.
