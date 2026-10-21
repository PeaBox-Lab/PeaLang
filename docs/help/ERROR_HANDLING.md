# Error Handling Help
Use `try { ... } catch err { ... } finally { ... }`. The catch variable is optional. `err.message` is the human-readable error. `err.source`, `err.line`, and `err.column` provide source context when available. `throw value` converts the value to display text and raises it as a PeaLang error. A `try` block requires `catch`, `finally`, or both.
