# Errors

Standard error categories are `SyntaxError`, `TypeError`, `NameError`, `ImportError`, `IndexError`, `KeyError`, `ValueError`, `PermissionError`, `TimeoutError`, `ResourceLimitError`, `NetworkError`, and `HostError`. Diagnostics SHOULD contain code, message, source, line/column range, stack/cause data when available.

Structured runtime errors use schema `pealang-error-v1`. A structured error value contains `schema`, `kind`, `message`, `code`, `cause`, `context`, `source`, `line`, `column`, `end_line`, `end_col`, `frames`, and `trace`. `error(kind, message, code, cause)` creates such a value, and `throw` preserves it. `catch` bindings expose this same record in both the interpreter and bytecode VM. Typed catches match by `kind` and its exception hierarchy; untyped catches match all PeaLang runtime errors. Builtin runtime failures are converted to typed structured errors where a matching category exists.
